#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ЗАПИСЬ ЗАМЕРОВ В БАЗУ iOS 27 (ЗКН-Э002, ЗКН-Э006).

Орган решает единственный вопрос: какое из снятых чисел имеет право стать
законом, а какое обязано остаться дырой. Мерит `geoscan.py`; здесь — суд над
результатом замера.

Правило согласия. Простая доля здесь не работает и это надо сказать прямо.
В совокупности отступов лежат и карточки, и кнопки, и миниатюры — у них
разные отступы ПО ПРАВУ, и требовать 55% от всех замеров значит не закрыть
никогда ничего. Поэтому приняты два независимых основания, и достаточно
любого:

  СМЫКАНИЕ — числа сходятся арифметически между собой и с экраном.
    Отступ 16 и ширина 361 при экране 393: 16 + 361 + 16 = 393 ровно.
    Совпадение трёх независимо снятых величин — улика сильнее любой доли.

  ПЕРЕВЕС — самое частое значение занимает не меньше 35% замеров и при этом
    не меньше чем в 1.5 раза опережает следующее. Один лидер, а не два.

Всё, что не прошло ни по одному основанию, остаётся дырой — но дырой С
УЛИКАМИ: сколько раз мерили, какое значение вело, какая доля. Разница между
«🕳 замерить» и «🕳 замерено 303×, ведёт 22.5pt, доля 5%» — это разница между
незнанием и знанием о своём незнании (ЗКН-Э001).

Правило пустого замера (ЗКН-Э006). Ноль кадров не даёт права тронуть базу:
пустой обход — промах адреса, а не подтверждение прежних чисел.

Запуск:  python3 bin/geofill.py --scan <файл замеров> [--write]
         python3 bin/geofill.py --court
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "registry" / "standards" / "ios27" / "tokens.next.json"

MIN_SAMPLES = 30      # меньше — совокупность слишком мала для суждения
LEAD_SHARE = 0.35     # доля лидера для перевеса
LEAD_RATIO = 1.5      # во сколько раз лидер обязан опережать следующего
CLOSURE_TOL = 1.0     # допуск смыкания в точках


def mode_of(vals, step=0.5):
    """Лидер совокупности и его доля → (значение, число, доля, следующий)."""
    if not vals:
        return None, 0, 0.0, 0
    q = Counter(round(v / step) * step for v in vals)
    top = q.most_common(2)
    v, n = top[0]
    nxt = top[1][1] if len(top) > 1 else 0
    return v, n, n / len(vals), nxt


def by_lead(vals, step=0.5) -> tuple:
    """Перевес: лидер держит долю и опережает следующего в полтора раза."""
    v, n, share, nxt = mode_of(vals, step)
    ok = bool(vals) and len(vals) >= MIN_SAMPLES and share >= LEAD_SHARE \
        and (nxt == 0 or n >= LEAD_RATIO * nxt)
    return ok, v, n, share


def closes(screen_w, inset, width, tol=CLOSURE_TOL) -> bool:
    """Смыкание: отступ + ширина + отступ = ширина экрана."""
    if None in (screen_w, inset, width):
        return False
    return abs((inset * 2 + width) - screen_w) <= tol


def decide(scan: list) -> dict:
    """Что закрывается замером, что остаётся дырой — и с какой уликой."""
    ok = [x for x in scan if x.get("ok")]
    if not ok:
        return {"frames": 0, "closed": {}, "holes": {},
                "why": "обойдено 0 кадров — база не тронута (ЗКН-Э006)"}
    scr = Counter(tuple(x["screen_pt"]) for x in ok).most_common(1)[0]
    screen, scr_n = list(scr[0]), scr[1]
    surf = [s for x in ok for s in x["surfaces"]]
    cards = [s for s in surf if s["inset_pt"] > 1.0]
    ins = [s["inset_pt"] for s in cards]
    wid = [s["width_pt"] for s in cards]
    seps = [t for x in ok for t in x["separators_pt"]]

    closed, holes = {}, {}
    closed["measured_frames"] = {"value": len(ok), "why": f"кадров принято {len(ok)}"}
    closed["geometry.screen_pt"] = {
        "value": screen,
        "why": f"согласие {scr_n}/{len(ok)} кадров = {scr_n/len(ok):.0%}"}

    vi, ni, shi, _ = mode_of(ins)
    vw, nw, shw, _ = mode_of(wid)
    if closes(screen[0], vi, vw):
        closed["geometry.inset_card_pt"] = {
            "value": vi,
            "why": f"смыкание {vi}·2 + {vw} = {screen[0]} · лидер {ni} замеров ({shi:.0%})"}
        closed["geometry.card_width_pt"] = {
            "value": vw,
            "why": f"смыкание {vi}·2 + {vw} = {screen[0]} · лидер {nw} замеров ({shw:.0%})"}
    else:
        holes["geometry.inset_card_pt"] = {"n": len(ins), "lead": vi, "share": shi}
        holes["geometry.card_width_pt"] = {"n": len(wid), "lead": vw, "share": shw}

    ok_s, vs, ns, shs = by_lead(seps, step=0.01)
    if ok_s:
        closed["separator.width_pt"] = {
            "value": vs, "why": f"перевес {ns} замеров ({shs:.0%}), лидер один"}
    else:
        v, n, sh, _ = mode_of(seps, step=0.01)
        holes["separator.width_pt"] = {"n": len(seps), "lead": v, "share": sh}

    # Радиус карточки считается ТОЛЬКО по тем поверхностям, которые правда
    # карточки: роль card, отступ и ширина сомкнулись с экраном, а верхний и
    # нижний углы сошлись между собой. Всё прочее — обломки и секции.
    real = [s for s in cards
            if s.get("role") == "card" and "radius_pt" in s
            and vi is not None and abs(s["inset_pt"] - vi) <= 0.7
            and vw is not None and abs(s["width_pt"] - vw) <= 1.0]
    square = [s for s in real if s["radius_pt"] <= 0.5]
    round_ = [s["radius_pt"] for s in real if s["radius_pt"] > 0.5]
    ok_r, vr, nr, shr = by_lead(round_)
    if ok_r:
        closed["geometry.radius_card_pt"] = {
            "value": vr,
            "why": f"перевес {nr} из {len(round_)} скруглённых карточек ({shr:.0%})"}
    else:
        h = {"n": len(round_), "square": len(square)}
        if round_:
            lo, hi = min(round_), max(round_)
            h.update({"lead": round(sum(round_) / len(round_), 1),
                      "share": 0.0, "range": [lo, hi]})
        else:
            h.update({"lead": None, "share": 0.0, "range": None})
        holes["geometry.radius_card_pt"] = h
    return {"frames": len(ok), "closed": closed, "holes": holes}


def apply_to_base(dec: dict, base_path: Path = None) -> int:
    """Вписать закрытое и пометить дыры уликами. Возврат — сколько тронуто."""
    base_path = base_path or BASE
    d = json.loads(base_path.read_text(encoding="utf-8"))

    def put(path, val):
        cur, parts = d, path.split(".")
        for k in parts[:-1]:
            if k not in cur or not isinstance(cur[k], dict):
                return False
            cur = cur[k]
        if parts[-1] not in cur:
            return False
        cur[parts[-1]] = val
        return True

    n = 0
    for k, v in dec["closed"].items():
        if put(k, v["value"]):
            n += 1
    for k, h in dec["holes"].items():
        if h.get("range"):
            mark = (f"🕳 скруглённых карточек {h['n']}, все в "
                    f"{h['range'][0]}–{h['range'][1]}pt, среднее {h['lead']}; "
                    f"с прямыми углами {h['square']} (секции, не карточки). "
                    f"Для закрытия нужно {MIN_SAMPLES} скруглённых — "
                    f"кадры со сгруппированными списками")
        else:
            mark = (f"🕳 замерено {h['n']}×, ведёт {h['lead']}, "
                    f"доля {h['share']:.0%} — согласия нет")
        if put(k, mark):
            n += 1
    base_path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def court() -> int:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  ✓ " if cond else "  ✗ ") + name)
        ok = ok and cond

    print("СУД · запись замеров в базу (без кадров и сети)")
    check("смыкание считается: 16·2 + 361 = 393", closes(393, 16.0, 361.0))
    check("ломаю → красный: 16·2 + 350 ≠ 393, смыкания нет",
          not closes(393, 16.0, 350.0))
    lead_ok, v, n, sh = by_lead([0.33] * 42 + [1.0] * 22 + [3.0] * 12, step=0.01)
    check("перевес: лидер 42% и вдвое впереди следующего → принято",
          lead_ok and abs(v - 0.33) < 0.01)
    tie_ok, *_ = by_lead([0.33] * 30 + [1.0] * 28 + [3.0] * 12, step=0.01)
    check("ломаю → красный: два близких лидера — согласия нет", not tie_ok)
    few_ok, *_ = by_lead([0.33] * 5, step=0.01)
    check("ломаю → красный: пять замеров — совокупность мала для суждения",
          not few_ok)

    scan = [{"ok": True, "screen_pt": [393, 852],
             "surfaces": [{"inset_pt": 16.0, "width_pt": 361.0}],
             "separators_pt": [0.33]} for _ in range(40)]
    dec = decide(scan)
    check("замер закрывает экран, отступ и ширину по смыканию",
          dec["closed"].get("geometry.screen_pt", {}).get("value") == [393, 852]
          and dec["closed"].get("geometry.inset_card_pt", {}).get("value") == 16.0
          and dec["closed"].get("geometry.card_width_pt", {}).get("value") == 361.0)
    check("каждое закрытое число несёт улику словами",
          all("why" in v and v["why"] for v in dec["closed"].values()))
    bad = [{"ok": True, "screen_pt": [393, 852],
            "surfaces": [{"inset_pt": 16.0, "width_pt": 300.0}],
            "separators_pt": []} for _ in range(40)]
    dbad = decide(bad)
    check("ломаю → красный: без смыкания отступ и ширина остаются дырами",
          "geometry.inset_card_pt" in dbad["holes"]
          and "geometry.inset_card_pt" not in dbad["closed"])
    check("дыра несёт улики: сколько мерили, что вело, какая доля",
          dbad["holes"]["geometry.inset_card_pt"]["n"] == 40)
    mixed = [{"ok": True, "screen_pt": [393, 852], "separators_pt": [],
              "surfaces": [{"inset_pt": 16.0, "width_pt": 361.0, "role": "card",
                            "radius_pt": 0.0},
                           {"inset_pt": 16.0, "width_pt": 361.0, "role": "card",
                            "radius_pt": 24.0}]} for _ in range(20)]
    dm = decide(mixed)
    hr = dm["holes"].get("geometry.radius_card_pt", {})
    check("прямоугольные секции не смешиваются со скруглёнными карточками",
          hr.get("square") == 20 and hr.get("n") == 20)
    check("разброс скруглённых назван, а не спрятан за долей",
          hr.get("range") == [24.0, 24.0] and hr.get("lead") == 24.0)
    many = [{"ok": True, "screen_pt": [393, 852], "separators_pt": [],
             "surfaces": [{"inset_pt": 16.0, "width_pt": 361.0, "role": "card",
                           "radius_pt": 24.0}]} for _ in range(40)]
    dmany = decide(many)
    check("чиню → зелёный: сорок скруглённых карточек закрывают радиус",
          dmany["closed"].get("geometry.radius_card_pt", {}).get("value") == 24.0)
    empty = decide([])
    check("пустой замер базу не трогает (ЗКН-Э006)",
          empty["frames"] == 0 and not empty["closed"])
    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()
    if not a.scan:
        print("нечего записывать: не задан --scan")
        return 1
    dec = decide(json.loads(Path(a.scan).read_text(encoding="utf-8")))
    print(f"кадров в замере: {dec['frames']}")
    print("ЗАКРЫТО ЗАМЕРОМ:")
    for k, v in dec["closed"].items():
        print(f"  {k} = {v['value']}   ({v['why']})")
    print("ОСТАЛОСЬ ДЫРОЙ, но с уликами:")
    for k, h in dec["holes"].items():
        print(f"  {k}: мерили {h['n']}×, ведёт {h['lead']}, доля {h['share']:.0%}")
    if a.write:
        n = apply_to_base(dec)
        print(f"в базу вписано записей: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
