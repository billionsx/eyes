#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ЧЕМ ЗАКРЫВАЕТСЯ ДЫРА (ст. 2, ЗКН-Э001).

Зачем орган существует. В базе iOS 27 все 53 дыры помечены одинаково —
«🕳 замерить». Из этой пометки следует, будто любую можно закрыть, добавив
кадров. Это неверно и вводит в заблуждение департамент вместе с основателем:

  · motion.* — девять дыр. Длительность перехода НЕ ВИДНА на статическом
    кадре ни при каком их числе. Нужна запись экрана с известной частотой.
  · typography.weights.* — четыре дыры. Вес начертания живёт в файле шрифта,
    а не в пикселях снимка; снимать его с кадра — гадание по толщине штриха.
  · остальное — кадры, и их действительно не хватает.

Дыра, не называющая своего сырья, хуже дыры: она выглядит закрываемой
завтра. Орган приписывает каждой дыре ВИД СЫРЬЯ и считает, сколько чего
нужно, — чтобы блокировка превратилась в поручение с инструкцией.

Запуск:  python3 bin/needs.py [--json]
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "registry" / "standards" / "ios27" / "tokens.next.json"
OUT = ROOT / "registry" / "standards" / "ios27" / "NEEDS.md"

# ВИД СЫРЬЯ. Ключ базы → чем эта величина вообще может быть измерена.
# Порядок важен: первое совпадение выигрывает.
FEED = (
    (r"^motion\.", "ЗАПИСЬ",
     "запись экрана 60 fps: длительности на статическом кадре не существует"),
    (r"^typography\.weights\.", "ШРИФТ",
     "метрики из файла шрифта (fontTools), а не из пикселей снимка"),
    (r"^typography\.cap_height_fraction\.", "ШРИФТ",
     "доля высоты прописной берётся из таблиц шрифта"),
    (r"^glass\.", "КАДР+СЛОЙ",
     "кадр, где известен цвет под стеклом: иначе прозрачность неотделима от фона"),
    (r"^opacity_ladder\.", "КАДР+СЛОЙ",
     "то же: ступень прозрачности видна только против известной подложки"),
    (r"^typography\.(role_sizes_pt|line_height_families_pt|tracking_cap_px)$", "КАДР",
     "измеряется по кадру: набранный текст на экране, не таблица шрифта"),
    (r"^(geometry|rows|glyphs|empty)\.", "КАДР",
     "статический кадр iOS 27 в тёмной теме"),
    (r"^(base|debts)$", "СВОДКА",
     "не величина, а состояние базы: закроется само, когда закроются остальные"),
)
DEFAULT = ("НЕ КЛАССИФИЦИРОВАНО",
           "🕳 вид сырья не назван — орган обязан быть дополнен, а не угадать")

# Сколько наблюдений требуется для закрытия. Значение берётся из самой базы,
# если она его называет; иначе величина объявляется неизвестной, а не выдуманной.
RE_NEED = re.compile(r"нужно\s+(\d+)")
RE_HAVE = re.compile(r"(?:карточек|элементов|образцов)\s+(\d+)|(\d+)\s*(?:наблюдени|шт)")


def feed_of(key: str) -> tuple[str, str]:
    for pat, name, why in FEED:
        if re.match(pat, key):
            return name, why
    return DEFAULT


def holes(base: Path = BASE) -> list[dict]:
    d = json.loads(base.read_text(encoding="utf-8"))
    out: list[dict] = []

    def walk(o, tr=""):
        if isinstance(o, dict):
            for k, v in o.items():
                t = f"{tr}.{k}" if tr else k
                if isinstance(v, (dict, list)):
                    walk(v, t)
                elif "🕳" in str(v):
                    out.append({"key": t, "evidence": str(v)})
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, (dict, list)):
                    walk(v, f"{tr}[{i}]")
                elif "🕳" in str(v):
                    out.append({"key": f"{tr}[{i}]", "evidence": str(v)})

    walk(d)
    for h in out:
        h["feed"], h["why"] = feed_of(h["key"])
        m = RE_NEED.search(h["evidence"])
        h["need"] = int(m.group(1)) if m else None
        # «нужно 30 скруглённых» и «скруглённых карточек 8» — разные числа.
        # Ищем наличие в тексте БЕЗ фразы про потребность, иначе орган
        # прочитает потребность как наличие и объявит дыру закрытой.
        rest = RE_NEED.sub(" ", h["evidence"])
        m2 = RE_HAVE.search(rest) or re.search(r"(\d+)\s*(?:наблюдени|кадр)", rest)
        h["have"] = int(next(x for x in m2.groups() if x)) if m2 else None
        if h["need"] and h["have"] is not None and h["have"] >= h["need"]:
            # Разбор противоречив: наличие не может быть больше потребности при
            # незакрытой дыре. Числу, которое спорит с фактом, верить нельзя.
            h["have"] = None
            h["parse_conflict"] = True
    return out


def render(hs: list[dict], frames: int) -> str:
    g: dict[str, list] = defaultdict(list)
    for h in hs:
        g[h["feed"]].append(h)
    lines = [
        "# ЧЕМ ЗАКРЫВАЮТСЯ ДЫРЫ БАЗЫ iOS 27", "",
        f"Дыр: **{len(hs)}** · кадров измерено: **{frames}**", "",
        "Дыра, не называющая своего сырья, хуже дыры: она выглядит закрываемой "
        "завтра. Здесь сказано, чем именно каждая закрывается — и чего "
        "департамент не получит, сколько бы кадров ему ни дали.", "",
        "| вид сырья | дыр | чем закрывается |", "|---|---|---|",
    ]
    for feed in sorted(g, key=lambda k: -len(g[k])):
        lines.append(f"| **{feed}** | {len(g[feed])} | {g[feed][0]['why']} |")
    lines.append("")
    for feed in sorted(g, key=lambda k: -len(g[k])):
        lines += [f"## {feed} — {len(g[feed])}", ""]
        for h in g[feed]:
            tail = ""
            if h["need"] and h["have"] is not None:
                tail = f" · есть {h['have']} из {h['need']}"
            elif h["need"]:
                tail = f" · нужно наблюдений: {h['need']}"
            lines.append(f"- `{h['key']}`{tail}")
        lines.append("")
    lines += [
        "---", "",
        "**Что это значит на деле.** Кадры поставляются разовым ручным "
        "импортом; автоматической поставки у департамента нет. Пока не "
        "появится новое сырьё нужного вида, соответствующие дыры не "
        "закрываются никаким усердием инструмента — и база iOS 27 не "
        "вступает в силу (Э002).", "",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    hs = holes()
    frames = json.loads(BASE.read_text(encoding="utf-8")).get("measured_frames", 0)
    if "--json" in argv:
        print(json.dumps(hs, ensure_ascii=False, indent=2))
        return 0
    OUT.write_text(render(hs, frames), encoding="utf-8")
    g: dict[str, int] = defaultdict(int)
    for h in hs:
        g[h["feed"]] += 1
    print(f"дыр: {len(hs)}")
    for k, v in sorted(g.items(), key=lambda x: -x[1]):
        print(f"  {k:22} {v}")
    print(f"записано: {OUT}")
    return 1 if g.get(DEFAULT[0]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
