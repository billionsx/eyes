#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ШКАЛА. Опубликованная типографика Apple: ступени Dynamic Type и
трекинг по кеглям.

Родословная. В базе департамента шкала ролей стояла ЗАМЕРОМ без подтверждения
публикацией, а долг «Dynamic Type кроме Large» висел с самого начала: замер
снят для одной ступени, а их у Apple десять. Крышка трекинга (0.4 px) тоже
стояла одна на все кегли, хотя Apple публикует своё значение для каждого.

Жатва добыла таблицы свода с разделами, и оказалось, что опубликовано всё:

    [… › iOS, iPadOS Dynamic Type sizes › Large (default)]
        Style: Large Title · Size (points): 34 · Leading (points): 41
    [… › Tracking values › SF Pro]
        Size (points): 17 · Tracking (1/1000 em): -43 · Tracking (points): -0.43

Орган перемалывает эти законы в СТРУКТУРУ: ступень → роль → кегль и
интерлиньяж; начертание → кегль → трекинг. Из потока строк получается то,
чем можно судить.

Провенанс. Это ОПУБЛИКОВАННОЕ, не замер. Apple предупреждает, что значения
плывут от выпуска к выпуску, поэтому шкала лежит отдельно от tokens.json и
сшивается с ним сверкой — как палитра.

Приложения:
    python3 bin/typescale.py            — перемолоть и свести
    python3 bin/typescale.py --write    — записать в стандарты
    python3 bin/typescale.py --court
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAWS = ROOT / "registry" / "library" / "hig-tables.jsonl"
OUT = ROOT / "registry" / "standards" / "typescale.json"
TOKENS = ROOT / "registry" / "standards" / "tokens.json"

# Разделы объявлены. Угадывать «похоже на типографику» нельзя: на странице
# соседствуют таблицы macOS, watchOS и tvOS, и перепутать платформы значит
# выдать чужое число за своё.
STEP = re.compile(r"iOS, iPadOS Dynamic Type sizes › ([^\]›]+)")
TRACK = re.compile(r"Tracking values › ([^\]›]+)")

CELL = re.compile(r"([^:·]+):\s*([^·]+)")


def cells(law):
    """Строка закона → словарь колонок. Раздел отрезается."""
    body = law.split("] ", 1)[1] if law.startswith("[") else law
    out = {}
    for k, v in CELL.findall(body):
        out[k.strip()] = v.strip()
    return out


def _num(s):
    m = re.search(r"[-+]?\d+(?:\.\d+)?", str(s))
    return float(m.group()) if m else None


def mill(rows):
    """Законы → структура. rows: [{id, law}]."""
    out = {"dynamic_type": {}, "tracking": {}, "address": {},
           "note": "опубликовано Apple; значения меняются от выпуска "
                   "к выпуску — это НЕ замер"}
    for r in rows:
        law, page = r.get("law", ""), r.get("id", "")
        if not page:
            continue                       # без адреса не берём (ЗКН-Э002)
        c = cells(law)

        m = STEP.search(law)
        if m and c.get("Style"):
            # «Large (default)» и «Large» — одна ступень: скобка поясняет,
            # а не именует. Без сведения ступень раздваивается и сверка
            # сравнивает шкалу саму с собой.
            step = m.group(1).strip()
            step = re.sub(r"\s*\(.*?\)\s*", "", step).strip() or step
            size, lead = _num(c.get("Size (points)")), _num(c.get("Leading (points)"))
            if size is None:
                continue
            out["dynamic_type"].setdefault(step, {})[c["Style"].strip()] = {
                "size": size, "leading": lead,
                "weight": (c.get("Weight") or "").strip() or None,
                "emphasized": (c.get("Emphasized weight") or "").strip() or None}
            out["address"]["dynamic_type"] = page
            continue

        m = TRACK.search(law)
        if m and c.get("Size (points)"):
            font = m.group(1).strip()
            size = _num(c.get("Size (points)"))
            pts = _num(c.get("Tracking (points)"))
            if size is None or pts is None:
                continue
            out["tracking"].setdefault(font, {})[f"{size:g}"] = pts
            out["address"]["tracking"] = page
    return out


def role_sizes(scale, step="Large"):
    """Кегли ступени по убыванию — в том виде, в каком их держит база."""
    node = scale.get("dynamic_type", {}).get(step, {})
    return sorted({v["size"] for v in node.values() if v.get("size")},
                  reverse=True)


def track_cap(scale, font="SF Pro"):
    """Наибольший по модулю опубликованный трекинг начертания."""
    node = scale.get("tracking", {}).get(font, {})
    return max((abs(v) for v in node.values()), default=None)


def cross(scale, tokens):
    """Сверка ОПУБЛИКОВАННОГО с ИЗМЕРЕННЫМ."""
    rows = []
    pub = role_sizes(scale, "Large")
    mes = [float(x) for x in tokens.get("typography", {}).get("role_sizes_pt", [])]
    if pub and mes:
        common = sorted(set(pub) & set(mes), reverse=True)
        rows.append({"what": "шкала ролей · Large",
                     "published": len(pub), "measured": len(mes),
                     "agree": len(common),
                     "only_measured": sorted(set(mes) - set(pub), reverse=True),
                     "only_published": sorted(set(pub) - set(mes), reverse=True)})
    cap_pub = track_cap(scale)
    cap_mes = tokens.get("typography", {}).get("tracking_cap_px")
    if cap_pub is not None and cap_mes is not None:
        rows.append({"what": "крышка трекинга · SF Pro",
                     "published": cap_pub, "measured": float(cap_mes),
                     "verdict": "ЗАМЕР СТРОЖЕ" if float(cap_mes) < cap_pub
                                else ("СОВПАЛО" if float(cap_mes) == cap_pub
                                      else "публикация строже")})
    return rows


def court():
    ok = True

    def chk(n, c):
        nonlocal ok
        ok = ok and bool(c)
        print(f"  {'✓' if c else '✗'} {n}")

    print("СУД · шкала (опубликованная типографика Apple)")

    P = "/design/human-interface-guidelines/typography"
    L = "[Specifications › iOS, iPadOS Dynamic Type sizes › Large (default)] "
    X = "[Specifications › iOS, iPadOS Dynamic Type sizes › xSmall] "
    T = "[Specifications › Tracking values › SF Pro] "
    M = "[Platform considerations › macOS] "

    rows = [
        {"id": P, "law": L + "Style: Large Title · Weight: Regular · "
                             "Size (points): 34 · Leading (points): 41 · "
                             "Emphasized weight: Bold"},
        {"id": P, "law": L + "Style: Body · Weight: Regular · "
                             "Size (points): 17 · Leading (points): 22 · "
                             "Emphasized weight: Semibold"},
        {"id": P, "law": X + "Style: Large Title · Weight: Regular · "
                             "Size (points): 31 · Leading (points): 38 · "
                             "Emphasized weight: Bold"},
        {"id": P, "law": T + "Size (points): 17 · Tracking (1/1000 em): -43 · "
                             "Tracking (points): -0.43"},
        {"id": P, "law": T + "Size (points): 6 · Tracking (1/1000 em): +41 · "
                             "Tracking (points): +0.24"},
        {"id": P, "law": M + "Style: Body · Size (points): 13"},
        {"id": "", "law": L + "Style: Ghost · Size (points): 99"},
    ]
    s = mill(rows)

    chk("ступень Large разобрана",
        s["dynamic_type"]["Large"]["Large Title"]["size"] == 34)
    chk("интерлиньяж и начертания взяты",
        s["dynamic_type"]["Large"]["Large Title"]["leading"] == 41
        and s["dynamic_type"]["Large"]["Large Title"]["emphasized"] == "Bold")
    chk("«Large (default)» и «Large» — одна ступень, а не две",
        list(s["dynamic_type"]) == ["Large", "xSmall"])
    chk("xSmall лежит ОТДЕЛЬНО и не подменяет Large",
        s["dynamic_type"]["xSmall"]["Large Title"]["size"] == 31)
    chk("macOS в шкалу iOS НЕ попал",
        all("Body" not in v or v["Body"]["size"] != 13
            for v in s["dynamic_type"].values()))
    chk("закон без адреса не берётся",
        "Ghost" not in json.dumps(s, ensure_ascii=False))

    chk("трекинг разобран по кеглям", s["tracking"]["SF Pro"]["17"] == -0.43)
    chk("положительный трекинг мелких кеглей взят",
        s["tracking"]["SF Pro"]["6"] == 0.24)
    chk("крышка трекинга — наибольшая по МОДУЛЮ", track_cap(s) == 0.43)

    chk("кегли ступени идут по убыванию", role_sizes(s, "Large") == [34, 17])
    chk("адрес первоисточника записан",
        s["address"]["dynamic_type"] == P and s["address"]["tracking"] == P)
    chk("шкала объявлена публикацией, а не замером", "НЕ замер" in s["note"])

    cr = cross(s, {"typography": {"role_sizes_pt": [34, 17, 12],
                                  "tracking_cap_px": 0.4}})
    chk("сверка считает совпадения и расхождения",
        cr[0]["agree"] == 2 and cr[0]["only_measured"] == [12])
    chk("сверка не выдаёт замер за публикацию",
        cr[1]["verdict"] == "ЗАМЕР СТРОЖЕ")

    chk("пустой вход не роняет орган",
        mill([])["dynamic_type"] == {} and role_sizes({}) == []
        and track_cap({}) is None)

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
        print("нет законов таблиц — сначала жатва:", LAWS, file=sys.stderr)
        return 1
    rows = []
    for line in LAWS.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    s = mill(rows)
    tok = json.loads(TOKENS.read_text(encoding="utf-8"))

    print(f"ступеней Dynamic Type: {len(s['dynamic_type'])} · "
          f"начертаний с трекингом: {len(s['tracking'])}")
    print("\nСТУПЕНИ (кегли по убыванию)")
    for step in sorted(s["dynamic_type"], key=lambda k: -len(s["dynamic_type"][k])):
        print(f"  {step:12s} {role_sizes(s, step)}")
    print("\nСВЕРКА С ЗАМЕРОМ")
    for r in cross(s, tok):
        if "agree" in r:
            print(f"  {r['what']}: опубликовано {r['published']} · "
                  f"измерено {r['measured']} · совпало {r['agree']}")
            if r["only_measured"]:
                print(f"     только в замере: {r['only_measured']}")
            if r["only_published"]:
                print(f"     только в публикации: {r['only_published']}")
        else:
            print(f"  {r['what']}: опубликовано {r['published']} · "
                  f"измерено {r['measured']} → {r['verdict']}")
    if a.write:
        OUT.write_text(json.dumps(s, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print("\nзаписано:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
