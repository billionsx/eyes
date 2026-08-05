#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ДОЗОР СРОКОВ (ст. 54).

Зачем орган. У департамента есть сроки, после которых он ОСТАНАВЛИВАЕТСЯ
целиком, и до 05.08.2026 о них знал только тот, кто случайно заглянул в
настройки GitHub:

  · требование двухфакторной защиты — после срока аккаунт ограничивается, и
    вместе с ним встают все прогоны: суд, гейты, сертификаты, монитор;
  · истечение ключа забора кода — храповик и сертификат теряют код клиента и
    начинают докладывать «код не забран», то есть красный инструмента.

Оба отказа приходят в назначенный день целиком, без предупреждения, и оба
выглядят как поломка департамента. Департамент, узнающий о своём отказе в день
отказа, не есть надзорный орган.

Что делает орган. Считает дни до каждого срока и выносит вердикт числом:

  🟢 больше 30 дней   — время есть;
  🟠 30…14 дней       — пора;
  🔴 меньше 14 дней   — последний срок; départament говорит об этом на каждом
                        прогоне, а не раз в месяц.

ЧТО ИЗМЕРЯЕТСЯ, А ЧТО ОБЪЯВЛЕНО — сказано в каждой строке отдельно, потому что
это разные по прочности сведения (ЗКН-Э001):

  · срок КЛЮЧА измеряется: GitHub отдаёт его заголовком
    `github-authentication-token-expiration` на любой запрос этим ключом. Это
    факт, снятый с источника;
  · срок ТРЕБОВАНИЯ объявлен: он взят из предупреждения GitHub и записан здесь
    с адресом. Объявление стареет молча, поэтому рядом стоит адрес, по которому
    его можно сверить, и дата записи.

Орган ничего не чинит и ключей не выписывает: создать ключ может только человек
в браузере — у GitHub нет API для выдачи ключей, и это правильно. Инструмент,
способный выписать себе доступ, есть дыра, а не инструмент. Поэтому орган
делает единственное, что может делать честно: считает дни и называет их вслух.

Запуск:
    python3 bin/keys.py                 — сводка в registry/state/KEYS.md
    python3 bin/keys.py --json
    python3 bin/keys.py --court         — суд, без сети
"""
import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "registry" / "state" / "KEYS.md"
STATE = ROOT / "registry" / "state" / "keys.json"

WARN_DAYS = 30
RED_DAYS = 14

# ОБЪЯВЛЕННЫЕ сроки: не измеряются, взяты из предупреждения источника. Каждый
# несёт адрес для сверки и дату записи — объявление без адреса проверить нельзя.
DECLARED = (
    {"что": "двухфакторная защита аккаунта billionsx",
     "срок": "2026-09-08",
     "чем грозит": "аккаунт ограничивается — встают ВСЕ прогоны департамента: "
                   "суд, гейты, сертификаты, монитор",
     "адрес": "https://github.com/settings/security",
     "записано": "2026-08-05",
     "источник": "предупреждение GitHub в интерфейсе аккаунта"},
)

# Ключи, срок которых департамент измеряет, если они у него на руках.
KEYS = (
    ("ключ забора кода клиентов", "EYES_PROJECTS_TOKEN",
     "храповик и сертификат теряют код клиента: вердикт станет "
     "«код не забран», то есть красный ИНСТРУМЕНТА"),
    ("ключ прогона", "GITHUB_TOKEN",
     "встроенный ключ прогона; истекает вместе с прогоном, срока не имеет"),
)


def days_left(date_str: str, today=None) -> int:
    """Дней до срока. Отрицательное — срок прошёл."""
    today = today or datetime.now(timezone.utc).date()
    d = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    return (d - today).days


def mark(days: int) -> str:
    if days < RED_DAYS:
        return "🔴"
    if days <= WARN_DAYS:
        return "🟠"
    return "🟢"


def measure_key(token: str, timeout: int = 15):
    """Срок ключа, СНЯТЫЙ с источника. None — источник срока не назвал.

    GitHub отдаёт срок заголовком на любой запрос. Мы не спрашиваем про сам
    ключ и не пересылаем его никуда, кроме владельца, — заголовок приходит
    попутно, и это самый дешёвый честный замер из возможных.
    """
    req = urllib.request.Request("https://api.github.com/user",
                                 headers={"Authorization": f"token {token}",
                                          "User-Agent": "bxe-keys"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            v = r.headers.get("github-authentication-token-expiration", "")
    except Exception:                                          # noqa: BLE001
        return None
    raw = (v or "").strip()
    # Сырьё сохраняется дословно (У1). Сита здесь нет: сведение — ОДИН
    # заголовок, и извлечённое совпадает с сырым. Хранить нечего сверх этой
    # строки, и она хранится.
    measure_key.last_raw = raw
    return raw[:10] or None


def rows(today=None, probe=measure_key) -> list:
    out = []
    for what, env, risk in KEYS:
        tok = os.environ.get(env, "")
        if not tok:
            out.append({"что": what, "род": "замер", "срок": None,
                        "дней": None, "знак": "⚪",
                        "почему": f"ключа {env} у органа нет — измерить нечего. "
                                  f"Молчание не есть исправность (ЗКН-Э001)",
                        "чем грозит": risk})
            continue
        exp = probe(tok)
        if not exp:
            out.append({"что": what, "род": "замер", "срок": None,
                        "дней": None, "знак": "⚪",
                        "почему": "источник срока не назвал: у ключа его может "
                                  "не быть вовсе (классический ключ без срока)",
                        "чем грозит": risk})
            continue
        d = days_left(exp, today)
        out.append({"что": what, "род": "замер", "срок": exp, "дней": d,
                    "знак": mark(d), "почему": "снято заголовком источника",
                    "чем грозит": risk})
    for dec in DECLARED:
        d = days_left(dec["срок"], today)
        out.append({"что": dec["что"], "род": "объявлено", "срок": dec["срок"],
                    "дней": d, "знак": mark(d),
                    "почему": f"объявлено {dec['записано']} по источнику: "
                              f"{dec['источник']} · сверить: {dec['адрес']}",
                    "чем грозит": dec["чем грозит"]})
    return out


def render(rs: list) -> str:
    worst = min((r["дней"] for r in rs if r["дней"] is not None), default=None)
    head = ("# ДОЗОР СРОКОВ\n\n"
            "Сроки, после которых департамент останавливается целиком. Оба рода\n"
            "отказа приходят в назначенный день сразу и оба выглядят как\n"
            "поломка департамента — поэтому дни считаются на каждом прогоне.\n\n"
            "Столбец «род» важен: ЗАМЕР снят с источника заголовком, ОБЪЯВЛЕНО\n"
            "взято из предупреждения и проверяется по адресу. Это сведения\n"
            "разной прочности, и смешивать их нельзя (ЗКН-Э001).\n\n"
            "Ключей департамент не выписывает: у GitHub нет API для выдачи\n"
            "ключей, и это правильно — инструмент, способный выписать себе\n"
            "доступ, есть дыра. Орган считает дни и называет их вслух.\n\n")
    if worst is not None:
        head += (f"**Ближайший срок: {worst} дней.**\n\n")
    L = [head, "| | что | род | срок | дней | чем грозит |",
         "|---|---|---|---|---|---|"]
    for r in sorted(rs, key=lambda x: (x["дней"] is None,
                                       x["дней"] if x["дней"] is not None else 0)):
        L.append(f"| {r['знак']} | {r['что']} | {r['род']} | "
                 f"{r['срок'] or '—'} | {r['дней'] if r['дней'] is not None else '—'} "
                 f"| {r['чем грозит']} |")
    L.append("")
    for r in rs:
        L.append(f"- **{r['что']}** — {r['почему']}")
    return "\n".join(L) + "\n"


def court() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    print("СУД · дозор сроков (без сети)")
    from datetime import date
    t = date(2026, 8, 5)
    chk("дни считаются от даты, а не на глаз",
        days_left("2026-09-08", t) == 34 and days_left("2026-08-05", t) == 0)
    chk("прошедший срок даёт отрицательное число, а не ноль",
        days_left("2026-08-01", t) == -4)
    chk("ломаю → красный: 13 дней до срока — последний срок", mark(13) == "🔴")
    chk("30 дней — «пора», 31 — «время есть»: порог объявлен числом",
        mark(30) == "🟠" and mark(31) == "🟢")
    chk("чиню → зелёный: далёкий срок не поднимает тревогу", mark(365) == "🟢")

    keep = dict(os.environ)
    try:
        os.environ.pop("EYES_PROJECTS_TOKEN", None)
        rs = rows(t, probe=lambda tok: None)
        k = [r for r in rs if r["род"] == "замер"][0]
        chk("ключа нет — орган говорит «измерить нечего», а не «всё в порядке»",
            k["знак"] == "⚪" and "ЗКН-Э001" in k["почему"])
        os.environ["EYES_PROJECTS_TOKEN"] = "x"
        rs = rows(t, probe=lambda tok: "2026-08-10")
        k = [r for r in rs if r["род"] == "замер" and r["срок"]][0]
        chk("ключ на руках — срок снимается с источника и краснеет за 5 дней",
            k["дней"] == 5 and k["знак"] == "🔴")
        chk("объявленный срок стоит рядом с замером, но РОДОМ отличается",
            any(r["род"] == "объявлено" for r in rs)
            and all("сверить:" in r["почему"] for r in rs
                    if r["род"] == "объявлено"))
        rs2 = rows(t, probe=lambda tok: None)
        chk("источник срока не назвал — это тоже ⚪, а не 🟢",
            [r for r in rs2 if r["род"] == "замер"][0]["знак"] == "⚪")
        txt = render(rows(t, probe=lambda tok: "2026-08-10"))
        chk("сводка называет ближайший срок числом в первых строках",
            "Ближайший срок: 5 дней" in txt)
        chk("сводка объясняет, почему ключей департамент не выписывает",
            "нет API для выдачи" in txt)
    finally:
        os.environ.clear()
        os.environ.update(keep)
    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="BXE · дозор сроков")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args(argv)
    if a.court:
        return court()
    rs = rows()
    OUT.write_text(render(rs), encoding="utf-8")
    worst = min((r["дней"] for r in rs if r["дней"] is not None), default=None)
    STATE.write_text(json.dumps(
        {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
         "worst_days": worst,
         "raw": getattr(measure_key, "last_raw", ""),
         "rows": [{k: v for k, v in r.items() if k != "почему"} for r in rs]},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if a.json:
        print(json.dumps(rs, ensure_ascii=False, indent=1))
    else:
        for r in rs:
            print(f"  {r['знак']} {r['что']:<38} {r['срок'] or '—':<12} "
                  f"{r['дней'] if r['дней'] is not None else '—'}")
        print(f"ближайший срок: {worst if worst is not None else '—'} дней · "
              f"{OUT.relative_to(ROOT)}")
    return 1 if (worst is not None and worst < RED_DAYS) else 0


if __name__ == "__main__":
    sys.exit(main())
