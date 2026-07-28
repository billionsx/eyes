#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ПРОВЕРКА ЭФИРА НА ДОМЕНЕ (ст. 54).

Хроника легла в репозиторий — это ещё не значит, что домен отдаёт её людям:
между коммитом и доменом стоят сборка Pages и кэш края. Здесь департамент
смотрит на свой эфир снаружи, как посетитель, и сравнивает отпечаток времени
на домене с отпечатком в репозитории.

Вердикт словами в `registry/state/SITE.md`: отставание в минутах, адрес,
код ответа. Правило зрелости: отставание больше `stale_minutes` из
`registry/site.json` — эфир СТАРЫЙ, и это видно текстом в хронике.

Ни одного адреса в коде: домен берётся из `registry/site.json`.

Запуск:  python3 bin/livecheck.py            — посмотреть эфир снаружи
         python3 bin/livecheck.py --selftest  — суд над сравнителем, без сети
"""
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = "BXE/1.0 (+https://github.com/billionsx/eyes)"


def parse_ts(s: str) -> datetime:
    """Отпечаток эфира: «2026-07-28 06:32 UTC» → время с зоной."""
    return datetime.strptime(s.replace(" UTC", ""), "%Y-%m-%d %H:%M").replace(
        tzinfo=timezone.utc)


def lag_minutes(local_ts: str, live_ts: str) -> float:
    """Отставание домена от репозитория в минутах. Отрицательное невозможно
    считать свежестью: домен впереди репозитория — тоже расхождение."""
    return (parse_ts(local_ts) - parse_ts(live_ts)).total_seconds() / 60.0


def verdict(lag: float, limit: float) -> tuple:
    if abs(lag) <= 0.5:
        return 0, "эфир на домене совпадает с репозиторием"
    if lag < 0:
        return 1, f"домен ВПЕРЕДИ репозитория на {abs(lag):.0f} мин — расхождение"
    if lag <= limit:
        return 0, f"домен отстаёт на {lag:.0f} мин — в пределах {limit:.0f}"
    return 1, f"эфир СТАРЫЙ: домен отстаёт на {lag:.0f} мин (предел {limit:.0f})"


def selftest() -> int:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  ✓ " if cond else "  ✗ ") + name)
        ok = ok and cond

    print("СУД · сравнитель эфира (без сети)")
    check("совпадение → зелёный",
          verdict(lag_minutes("2026-07-28 06:32 UTC", "2026-07-28 06:32 UTC"), 15)[0] == 0)
    check("отставание в пределах → зелёный",
          verdict(lag_minutes("2026-07-28 06:32 UTC", "2026-07-28 06:25 UTC"), 15)[0] == 0)
    check("отставание за пределом → красный",
          verdict(lag_minutes("2026-07-28 06:32 UTC", "2026-07-28 05:10 UTC"), 15)[0] == 1)
    check("домен впереди репозитория → красный",
          verdict(lag_minutes("2026-07-28 06:00 UTC", "2026-07-28 06:20 UTC"), 15)[0] == 1)
    return 0 if ok else 1


def main() -> int:
    cfg = json.loads((ROOT / "registry" / "site.json").read_text(encoding="utf-8"))
    url = cfg["url"].rstrip("/") + "/data.json"
    limit = float(cfg.get("stale_minutes", 15))
    local = json.loads((ROOT / "dashboard" / "data.json").read_text(encoding="utf-8"))["ts"]

    code, live, err = 0, None, ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=20) as r:
            code = r.status
            live = json.loads(r.read().decode("utf-8")).get("ts")
    except urllib.error.HTTPError as e:
        code, err = e.code, f"HTTP {e.code}"
    except Exception as e:
        err = type(e).__name__ + ": " + str(e)[:120]

    if live:
        rc, words = verdict(lag_minutes(local, live), limit)
        body = (f"адрес: {url}\nответ: HTTP {code}\n"
                f"в репозитории: {local}\nна домене: {live}\nвердикт: {words}\n")
    else:
        rc = 1
        hint = ("\nпримечание: HTTP 403 бывает и от шлюза песочницы, которому домен "
                "не разрешён — тогда это НЕ вина домена; истину говорит прогон в CI\n"
                if code == 403 else "")
        body = (f"адрес: {url}\nответ: {err or 'пусто'}\n"
                f"в репозитории: {local}\nна домене: —\n"
                "вердикт: эфир снаружи НЕ ПРОЧИТАН — домен молчит, отдаёт не JSON "
                "или запрос не вышел наружу\n" + hint)

    out = ROOT / "registry" / "state" / "SITE.md"
    out.write_text("# ЭФИР НА ДОМЕНЕ · последняя проверка\n\n" + body, encoding="utf-8")
    print("ЭФИР НА ДОМЕНЕ")
    print("  " + body.replace("\n", "\n  ").rstrip())
    return rc


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
