#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ПАЛИТРА. Опубликованные значения системных цветов Apple — светлые
и тёмные, обычные и высококонтрастные.

Родословная. Светлая тема стояла долгом с самого начала: кадротека почти
целиком тёмная (194 кадра из 195), кит iOS для Sketch Apple больше не
публикует, кит Figma требует места Editor, а текстовый снимок страницы
цвета HIG не несёт ни одного hex — таблицы там образцами.

Оказалось, что искали не там. Страница цвета отдаётся машинным JSON
(`/tutorials/data/design/human-interface-guidelines/color.json`), и Apple
подписывает КАЖДЫЙ образец альтернативным текстом со значением:

    ios-default-systemgray6.png       alt: R-242,G-242,B-247
    ios-default-systemgray6dark.png   alt: R-28,G-28,B-30
    colors-unified-blue-light.png     alt: R-0,G-136,B-255

Это первоисточник, машинно читаемый, с адресом страницы. Не блог, не
чужая сводка, не догадка. Альт написан Apple для незрячих — и оказался
единственным местом, где Apple публикует свои числа текстом.

Что берётся:
  · системные цвета — `colors-unified-<тон>-<light|dark>`
  · высококонтрастные — `colors-unified-accessible-<тон>-<light|dark>`
  · лестница серых iOS — `ios-default-systemgray<N>[dark]`
  · высококонтрастные серые — `ios-accessible-systemgray<N>[dark]`

Чего орган НЕ делает. Не подменяет замер. Apple прямо предупреждает, что
значения плывут от выпуска к выпуску, — поэтому палитра идёт в базу как
ОПУБЛИКОВАННОЕ, отдельно от ИЗМЕРЕННОГО, и сшивается с ним двойным
свидетельством. Совпало — правило вдвое сильнее. Разошлось — находка.

Приложения:
    python3 bin/palette.py                 — разобрать фикстуру, свести
    python3 bin/palette.py --write         — записать в базу
    python3 bin/palette.py --court
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "registry" / "fixtures" / "apple" / "hig-color.json"
OUT = ROOT / "registry" / "standards" / "palette.json"
ADDRESS = "/design/human-interface-guidelines/color"

# Значение в альте: «R-242,G-242,B-247». Пробелы Apple ставит по-разному,
# поэтому допускаются, но структура жёсткая: три канала по порядку.
RGB = re.compile(r"^\s*R\s*-\s*(\d{1,3})\s*,\s*G\s*-\s*(\d{1,3})\s*,\s*"
                 r"B\s*-\s*(\d{1,3})\s*$", re.I)

# Имена образцов. Разбирается ТОЛЬКО объявленная форма: угадывать по
# похожести значит однажды принять снимок экрана за образец цвета.
HUE = re.compile(r"^colors-unified-(accessible-)?([a-z]+)-(light|dark)\.png$", re.I)
GRAY = re.compile(r"^ios-(default|accessible)-systemgray(\d?)(dark)?\.png$", re.I)


def hex_of(r, g, b):
    return "#%02X%02X%02X" % (r, g, b)


def parse(doc):
    """Разбирает JSON страницы. Возвращает словарь палитры.

    Устойчивость к чужому: любой образец, чей альт не является тройкой
    каналов, пропускается молча — на странице десятки скриншотов и
    иллюстраций, и альт у них человеческий текст.
    """
    out = {"system": {}, "gray": {}, "address": ADDRESS,
           "note": "опубликованные значения Apple из альт-текста образцов; "
                   "Apple предупреждает, что значения меняются от выпуска "
                   "к выпуску — это НЕ замер"}
    for key, ref in (doc.get("references") or {}).items():
        if ref.get("type") != "image":
            continue
        m = RGB.match(ref.get("alt") or "")
        if not m:
            continue
        rgb = hex_of(*(int(x) for x in m.groups()))
        name = key if key.endswith(".png") else key + ".png"

        h = HUE.match(name)
        if h:
            acc, hue, mode = h.group(1), h.group(2).lower(), h.group(3).lower()
            slot = out["system"].setdefault(hue, {})
            slot[("accessible_" if acc else "") + mode] = rgb
            continue

        g = GRAY.match(name)
        if g:
            kind, num, dark = g.group(1).lower(), g.group(2) or "1", g.group(3)
            slot = out["gray"].setdefault(f"systemGray{num}", {})
            slot[("accessible_" if kind == "accessible" else "")
                 + ("dark" if dark else "light")] = rgb
    return out


def ladder(pal, mode="light"):
    """Лестница серых по возрастанию номера: systemGray1..6 в нужной теме."""
    out = []
    for n in range(1, 7):
        v = pal.get("gray", {}).get(f"systemGray{n}", {}).get(mode)
        if v:
            out.append(v)
    return out


def cross(pal, tokens):
    """Сверка ОПУБЛИКОВАННОГО с ИЗМЕРЕННЫМ. Возвращает список строк сверки.

    Именно ради этого палитра и заводится отдельно от базы: два независимых
    свидетельства об одном цвете сильнее любого из них поодиночке.
    """
    measured = [c.upper() for c in tokens.get("surfaces", {}).get("allow", [])]
    rows = []
    for n in range(1, 7):
        v = pal.get("gray", {}).get(f"systemGray{n}", {}).get("dark")
        if not v:
            continue
        rows.append({"token": f"systemGray{n}.dark", "published": v,
                     "verdict": "СОВПАЛО" if v in measured else "нет в замере"})
    return rows


def court():
    ok = True

    def chk(n, c):
        nonlocal ok
        ok = ok and bool(c)
        print(f"  {'✓' if c else '✗'} {n}")

    print("СУД · палитра (опубликованные значения Apple)")

    chk("канал разбирается в hex", hex_of(28, 28, 30) == "#1C1C1E")
    chk("альт-тройка распознаётся", bool(RGB.match("R-242,G-242,B-247")))
    chk("пробелы в альте допускаются", bool(RGB.match(" R - 0 , G - 136 , B - 255 ")))
    chk("человеческий альт тройкой не считается",
        not RGB.match("A screenshot of the Notes app in iOS"))

    doc = {"references": {
        "ios-default-systemgray6dark.png": {"type": "image",
                                            "alt": "R-28,G-28,B-30"},
        "ios-default-systemgray6.png": {"type": "image",
                                        "alt": "R-242,G-242,B-247"},
        "ios-accessible-systemgray6.png": {"type": "image",
                                           "alt": "R-235,G-235,B-240"},
        "colors-unified-blue-light.png": {"type": "image",
                                          "alt": "R-0,G-136,B-255"},
        "colors-unified-blue-dark.png": {"type": "image",
                                         "alt": "R-0,G-145,B-255"},
        "colors-unified-accessible-blue-light.png": {"type": "image",
                                                     "alt": "R-30,G-110,B-244"},
        "color-context-light-mode": {"type": "image",
                                     "alt": "A screenshot of the Notes app"},
        "color.svg": {"type": "image", "alt": "An icon of a paint palette"},
    }}
    p = parse(doc)

    chk("СВЕТЛОЕ значение взято", p["gray"]["systemGray6"]["light"] == "#F2F2F7")
    chk("тёмное значение взято", p["gray"]["systemGray6"]["dark"] == "#1C1C1E")
    chk("высококонтрастное лежит ОТДЕЛЬНО, а не подменяет обычное",
        p["gray"]["systemGray6"]["accessible_light"] == "#EBEBF0"
        and p["gray"]["systemGray6"]["light"] == "#F2F2F7")
    chk("системный цвет разобран в обе темы",
        p["system"]["blue"]["light"] == "#0088FF"
        and p["system"]["blue"]["dark"] == "#0091FF")
    chk("высококонтрастный тон отделён",
        p["system"]["blue"]["accessible_light"] == "#1E6EF4")
    chk("скриншоты и иконки в палитру НЕ попали",
        set(p["gray"]) == {"systemGray6"} and set(p["system"]) == {"blue"})
    chk("адрес первоисточника неотделим", p["address"] == ADDRESS)
    chk("палитра честно объявлена НЕ замером", "НЕ замер" in p["note"])

    chk("лестница строится по возрастанию номера",
        ladder(p, "light") == ["#F2F2F7"])

    rows = cross(p, {"surfaces": {"allow": ["#000000", "#1C1C1E"]}})
    chk("сверка находит совпадение замера с публикацией",
        rows and rows[0]["verdict"] == "СОВПАЛО")
    rows2 = cross(p, {"surfaces": {"allow": ["#000000"]}})
    chk("сверка не выдаёт несовпадение за совпадение",
        rows2[0]["verdict"] == "нет в замере")

    chk("пустой документ не роняет орган",
        parse({}) ["gray"] == {} and parse({"references": {}})["system"] == {})

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()
    if not FIXTURE.exists():
        print("нет фикстуры:", FIXTURE, file=sys.stderr)
        return 1
    pal = parse(json.loads(FIXTURE.read_text(encoding="utf-8")))
    tok = json.loads((ROOT / "registry" / "standards" / "tokens.json")
                     .read_text(encoding="utf-8"))

    print(f"системных цветов: {len(pal['system'])} · серых: {len(pal['gray'])}")
    print("\nЛЕСТНИЦА СЕРЫХ")
    print("  светлая:", " → ".join(ladder(pal, "light")) or "—")
    print("  тёмная: ", " → ".join(ladder(pal, "dark")) or "—")
    print("\nСВЕРКА С ЗАМЕРОМ")
    for r in cross(pal, tok):
        print(f"  {r['verdict']:14s} {r['token']:20s} {r['published']}")

    if a.write:
        OUT.write_text(json.dumps(pal, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print("\nзаписано:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
