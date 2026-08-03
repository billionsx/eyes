#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · УСТРОЙСТВА. Опубликованные размеры экранов Apple и размерные классы.

Родословная. Департамент мерит кадры на ширине 393 pt и держит эту ширину
как данность: «телефонная рамка 393pt» стоит в паспорте клиента и в
геометрии базы. Откуда 393 — знал только тот, кто ставил.

Жатва добыла таблицу `layout › iOS, iPadOS device screen dimensions`: Apple
публикует точный размер КАЖДОЙ модели в пунктах и пикселях с масштабом.
Теперь ширина замера не данность, а сверяемое число.

Что даёт орган:

  · ШИРИНЫ. Полный перечень моделей: 393×852, 440×956, 320×568 и так далее.
    Замер департамента получает подтверждение или расхождение.
  · КЛАССЫ. Размерный класс каждой модели в обеих ориентациях — то, чем
    Apple на самом деле переключает вёрстку. Не 768 из давней моды, а
    compact/regular по реальной ширине.
  · ТОЧКИ ПЕРЕКЛЮЧЕНИЯ. Из ширин выводится набор настоящих границ, на
    которых меняется класс. Число из моды и число из системы различимы.

Провенанс. Опубликовано Apple, не снято департаментом. Лежит отдельно от
tokens.json и сверяется с ним — как палитра и шкала.

Приложения:
    python3 bin/devices.py            — перемолоть и свести
    python3 bin/devices.py --write    — записать в стандарты
    python3 bin/devices.py --court
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAWS = ROOT / "registry" / "library" / "hig-tables.jsonl"
OUT = ROOT / "registry" / "standards" / "devices.json"
TOKENS = ROOT / "registry" / "standards" / "tokens.json"

# Разделы объявлены. watchOS и tvOS публикуются рядом в тех же таблицах —
# смешать их с iOS значит завести точку переключения на 176 pt.
DIMS = re.compile(r"iOS, iPadOS device screen dimensions")
CLASSES = re.compile(r"iOS, iPadOS device size classes")

CELL = re.compile(r"([^:·]+):\s*([^·]+)")
# «1032x1376 pt (2064x2752 px @2x)» — берём пункты и масштаб, пиксели
# производны и хранить их значит держать два источника одной правды.
SIZE = re.compile(r"(\d+)\s*[x×]\s*(\d+)\s*pt(?:[^@]*@(\d)x)?", re.I)


def cells(law):
    body = law.split("] ", 1)[1] if law.startswith("[") else law
    return {k.strip(): v.strip() for k, v in CELL.findall(body)}


def mill(rows):
    """Законы → структура устройств."""
    out = {"screens": {}, "classes": {}, "address": {},
           "note": "опубликовано Apple; это НЕ замер"}
    for r in rows:
        law, page = r.get("law", ""), r.get("id", "")
        if not page:
            continue
        c = cells(law)
        model = c.get("Model")
        if not model:
            continue

        if DIMS.search(law):
            m = SIZE.search(c.get("Dimensions (portrait)", ""))
            if not m:
                continue
            out["screens"][model] = {
                "w": int(m.group(1)), "h": int(m.group(2)),
                "scale": int(m.group(3)) if m.group(3) else None}
            out["address"]["screens"] = page
        elif CLASSES.search(law):
            p = c.get("Portrait orientation")
            l = c.get("Landscape orientation")
            if not p and not l:
                continue
            out["classes"][model] = {"portrait": p, "landscape": l}
            out["address"]["classes"] = page
    return out


def widths(dev):
    """Ширины моделей по возрастанию, без повторов."""
    return sorted({v["w"] for v in dev.get("screens", {}).values() if v.get("w")})


def breakpoints(dev):
    """Настоящие точки переключения: ширины, на которых меняется класс.

    Не «круглые» числа из моды, а границы между compact и regular по
    опубликованным данным. Если класс модели неизвестен, модель в вывод
    не идёт: догадка о классе хуже его отсутствия.
    """
    known = []
    for model, cl in dev.get("classes", {}).items():
        scr = dev.get("screens", {}).get(model)
        if not scr or not cl.get("portrait"):
            continue
        known.append((scr["w"], "regular" if cl["portrait"].lower()
                      .startswith("regular") else "compact"))
    known.sort()
    out = []
    for i in range(1, len(known)):
        if known[i][1] != known[i - 1][1]:
            out.append(known[i][0])
    return sorted(set(out))


def cross(dev, tokens):
    """Сверка опубликованного с замером департамента."""
    rows = []
    w = tokens.get("geometry", {}).get("frame_width_pt") or 393
    ws = widths(dev)
    if ws:
        hit = [m for m, v in dev.get("screens", {}).items() if v.get("w") == w]
        rows.append({"what": f"ширина кадра замера · {w} pt",
                     "verdict": "ПОДТВЕРЖДЕНО" if hit else "НЕТ ТАКОЙ МОДЕЛИ",
                     "models": sorted(hit)[:3], "published_widths": len(ws)})
    return rows


def court():
    ok = True

    def chk(n, c):
        nonlocal ok
        ok = ok and bool(c)
        print(f"  {'✓' if c else '✗'} {n}")

    print("СУД · устройства (опубликованные размеры Apple)")

    P = "/design/human-interface-guidelines/layout"
    D = "[Specifications › iOS, iPadOS device screen dimensions] "
    C = "[Specifications › iOS, iPadOS device size classes] "
    W = "[Specifications › watchOS device screen dimensions] "

    rows = [
        {"id": P, "law": D + "Model: iPhone 16 Pro · Dimensions (portrait): "
                             "402x874 pt (1206x2622 px @3x)"},
        {"id": P, "law": D + "Model: iPhone 15 Pro · Dimensions (portrait): "
                             "393x852 pt (1179x2556 px @3x)"},
        {"id": P, "law": D + "Model: iPad Pro 13-inch · Dimensions (portrait): "
                             "1032x1376 pt (2064x2752 px @2x)"},
        {"id": P, "law": W + "Model: Apple Watch 45mm · Dimensions (portrait): "
                             "198x242 pt (396x484 px @2x)"},
        {"id": P, "law": C + "Model: iPhone 15 Pro · Portrait orientation: "
                             "Compact width, regular height · "
                             "Landscape orientation: Compact width, compact height"},
        {"id": P, "law": C + "Model: iPad Pro 13-inch · Portrait orientation: "
                             "Regular width, regular height · "
                             "Landscape orientation: Regular width, regular height"},
        {"id": "", "law": D + "Model: Призрак · Dimensions (portrait): 1x1 pt"},
    ]
    d = mill(rows)

    chk("размер модели разобран в пунктах",
        d["screens"]["iPhone 15 Pro"]["w"] == 393
        and d["screens"]["iPhone 15 Pro"]["h"] == 852)
    chk("масштаб взят", d["screens"]["iPhone 15 Pro"]["scale"] == 3)
    chk("пиксели не хранятся: они производны от пунктов и масштаба",
        "px" not in json.dumps(d["screens"], ensure_ascii=False))
    chk("watchOS в перечень iOS НЕ попал",
        "Apple Watch 45mm" not in d["screens"])
    chk("закон без адреса не берётся", "Призрак" not in json.dumps(d, ensure_ascii=False))

    chk("размерный класс разобран в обеих ориентациях",
        d["classes"]["iPhone 15 Pro"]["portrait"].startswith("Compact"))
    chk("адреса первоисточника записаны",
        d["address"]["screens"] == P and d["address"]["classes"] == P)

    chk("ширины идут по возрастанию без повторов",
        widths(d) == [393, 402, 1032])

    bp = breakpoints(d)
    chk("точка переключения найдена ТАМ, где меняется класс", bp == [1032])
    chk("модель без известного класса в точки не идёт",
        breakpoints({"screens": {"X": {"w": 500}}, "classes": {}}) == [])

    cr = cross(d, {"geometry": {"frame_width_pt": 393}})
    chk("замер департамента подтверждён публикацией",
        cr[0]["verdict"] == "ПОДТВЕРЖДЕНО" and "iPhone 15 Pro" in cr[0]["models"])
    cr2 = cross(d, {"geometry": {"frame_width_pt": 375}})
    chk("выдуманная ширина не выдаётся за подтверждённую",
        cr2[0]["verdict"] == "НЕТ ТАКОЙ МОДЕЛИ")

    chk("пустой вход не роняет орган",
        mill([])["screens"] == {} and widths({}) == [] and breakpoints({}) == [])

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()
    if not LAWS.exists():
        print("нет законов таблиц — сначала жатва", file=sys.stderr)
        return 1
    rows = []
    for line in LAWS.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    d = mill(rows)
    tok = json.loads(TOKENS.read_text(encoding="utf-8"))

    print(f"моделей с размером: {len(d['screens'])} · "
          f"с размерным классом: {len(d['classes'])}")
    print("\nШИРИНЫ (pt):", widths(d))
    print("ТОЧКИ ПЕРЕКЛЮЧЕНИЯ КЛАССА (pt):", breakpoints(d) or "—")
    print("\nСВЕРКА С ЗАМЕРОМ")
    for r in cross(d, tok):
        print(f"  {r['verdict']:18s} {r['what']}")
        if r.get("models"):
            print(f"     модели: {', '.join(r['models'])}")
    if a.write:
        OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print("\nзаписано:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
