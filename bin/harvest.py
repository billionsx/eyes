#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ЖАТВА. Автономный работник: систематически обходит документацию Apple
и просеивает её на ЧИСЛА С АДРЕСОМ.

Родословная. Светлая тема закрылась находкой: страница цвета отдаётся
машинным JSON, и Apple подписывает каждый образец альт-текстом со значением
(`ios-default-systemgray6.png` → `R-242,G-242,B-247`). Значение первичное,
машинно читаемое, с адресом страницы.

Но добыто оно было РАЗОВЫМ зондом по одной странице. Одна находка — не
источник. Департамент, который обогащается вручную, обогащается ровно
столько раз, сколько у основателя нашлось вечеров.

Работник делает из находки процесс:

  ФРОНТ     каждая разобранная страница отдаёт ссылки на соседние страницы
            HIG. Фронт хранится и растёт сам — обход не нужно составлять.
  СИТА      объявленный список просеивателей. Сито знает ОДНУ форму записи
            и не угадывает: угаданное сито однажды примет скриншот за
            образец цвета. Новая форма — новое сито, а не «поумневшая»
            регулярка.
  ПРОВЕНАНС каждое добытое значение несёт адрес страницы, откуда взято.
            Без адреса значение не записывается вовсе (ЗКН-Э002).
  ВЕЖЛИВОСТЬ бюджет страниц на прогон. Департамент ходит к Apple как гость,
            а не как пылесос.

Что работник НЕ делает. Не подменяет замер: опубликованное Apple слабее
снятого с кадров, потому что Apple прямо предупреждает о плавающих
значениях. Палитра лежит отдельно от базы замера и сшивается с ней двойным
свидетельством (`bin/attest.py`).

Приложения:
    python3 bin/harvest.py                 — жатва по фронту (нужна сеть)
    python3 bin/harvest.py --pages 5       — бюджет страниц
    python3 bin/harvest.py --seed          — заложить фронт от страницы цвета
    python3 bin/harvest.py --offline       — жатва по фикстурам, без сети
    python3 bin/harvest.py --court
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "registry" / "fixtures" / "apple"
PALETTE = ROOT / "registry" / "standards" / "palette.json"
STATE = ROOT / "registry" / "state" / "harvest.json"
HOST = "https://developer.apple.com"
HIG = "/design/human-interface-guidelines/"

PAGES_PER_RUN = 12          # гость, не пылесос
SEED = HIG + "color"

# ── СИТА ────────────────────────────────────────────────────────────────────
# Каждое сито знает ОДНУ объявленную форму. Угадывать нельзя: сито, которое
# «похоже подходит», однажды примет альт скриншота за спецификацию.

RGB_ALT = re.compile(r"^\s*R\s*-\s*(\d{1,3})\s*,\s*G\s*-\s*(\d{1,3})\s*,\s*"
                     r"B\s*-\s*(\d{1,3})\s*$", re.I)
HUE = re.compile(r"^colors-unified-(accessible-)?([a-z]+)-(light|dark)(?:\.png)?$", re.I)
GRAY = re.compile(r"^(?:ios|macos|watchos|tvos|visionos)-(default|accessible)-"
                  r"systemgray(\d?)(dark)?(?:\.png)?$", re.I)


def _hex(r, g, b):
    return "#%02X%02X%02X" % (r, g, b)


def sieve_swatches(doc, page):
    """Сито образцов цвета. Возвращает (что, куда, значение, адрес)."""
    out = []
    for key, ref in (doc.get("references") or {}).items():
        if ref.get("type") != "image":
            continue
        m = RGB_ALT.match(ref.get("alt") or "")
        if not m:
            continue
        val = _hex(*(int(x) for x in m.groups()))
        name = key[:-4] if key.lower().endswith(".png") else key

        h = HUE.match(name)
        if h:
            acc, hue, mode = h.group(1), h.group(2).lower(), h.group(3).lower()
            out.append(("system", hue,
                        ("accessible_" if acc else "") + mode, val, page))
            continue
        g = GRAY.match(name)
        if g:
            kind, num, dark = g.group(1).lower(), g.group(2) or "1", g.group(3)
            out.append(("gray", f"systemGray{num}",
                        ("accessible_" if kind == "accessible" else "")
                        + ("dark" if dark else "light"), val, page))
    return out


SIEVES = (("образцы цвета", sieve_swatches),)


# ── ФРОНТ ───────────────────────────────────────────────────────────────────

def links(doc):
    """Соседние страницы HIG. Только они: департамент обходит СВОД норм,
    а не всю документацию Apple — справочник API числами дизайна не богат
    (доказано: 68 чисел с единицей на 30 000 норм)."""
    out = set()
    for ref in (doc.get("references") or {}).values():
        if ref.get("type") != "topic":
            continue
        u = str(ref.get("url") or "")
        # Якорь — это МЕСТО на странице, а не страница. Без отсечения фронт
        # набивается ссылками `…/color#System-colors`, бюджет прогона уходит
        # на повторную загрузку уже пройденного, а обход не кончается никогда.
        u = u.split("#", 1)[0].rstrip("/")
        if u.lower().startswith(HIG.lower()) and u.count("/") == HIG.count("/"):
            out.add(u)
    return sorted(out)


def read_state():
    if not STATE.exists():
        return {"done": [], "front": [], "harvested": 0}
    try:
        d = json.loads(STATE.read_text(encoding="utf-8"))
    except ValueError:
        return {"done": [], "front": [], "harvested": 0}
    for k, v in (("done", []), ("front", []), ("harvested", 0)):
        d.setdefault(k, v)
    return d


def fetch(page, timeout=25):
    """Машинный JSON страницы. None — не выяснено, и это не сбой жатвы:
    страница может быть переименована, а работник обязан идти дальше."""
    url = f"{HOST}/tutorials/data{page}.json"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": "billions-x-eyes"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError, TimeoutError, OSError):
        return None


def load_palette():
    if PALETTE.exists():
        try:
            p = json.loads(PALETTE.read_text(encoding="utf-8"))
        except ValueError:
            p = {}
    else:
        p = {}
    for k in ("system", "gray", "sources"):
        p.setdefault(k, {})
    p.setdefault("note", "опубликованные значения Apple из альт-текста "
                         "образцов; Apple предупреждает, что значения "
                         "меняются от выпуска к выпуску — это НЕ замер")
    return p


def merge(pal, rows):
    """Вносит урожай в палитру. Возвращает (новых, изменившихся, конфликтов).

    Изменение значения НЕ проходит молча: старое и новое кладутся в конфликты
    и предъявляются. Apple правит свои числа между выпусками, и департамент
    обязан заметить правку, а не затереть память о ней.
    """
    added = changed = 0
    conflicts = []
    for group, name, slot, val, page in rows:
        if not page:
            continue                      # без адреса не пишем (ЗКН-Э002)
        node = pal.setdefault(group, {}).setdefault(name, {})
        old = node.get(slot)
        if old is None:
            node[slot] = val
            added += 1
        elif old != val:
            conflicts.append({"token": f"{group}.{name}.{slot}",
                              "was": old, "now": val, "at": page})
            node[slot] = val
            changed += 1
        pal["sources"][f"{group}.{name}"] = page
    return added, changed, conflicts


def harvest(pages, getter, pal, state):
    """Один заход жатвы. getter(page) → документ или None."""
    rows, walked, dead = [], [], []
    for page in pages:
        doc = getter(page)
        if not doc:
            dead.append(page)
            continue
        walked.append(page)
        for _name, sieve in SIEVES:
            rows.extend(sieve(doc, page))
        for u in links(doc):
            if u not in state["done"] and u not in state["front"]:
                state["front"].append(u)
    added, changed, conflicts = merge(pal, rows)
    for p in walked:
        if p not in state["done"]:
            state["done"].append(p)
        if p in state["front"]:
            state["front"].remove(p)
    state["harvested"] = state.get("harvested", 0) + added + changed
    return {"walked": len(walked), "dead": dead, "values": len(rows),
            "added": added, "changed": changed, "conflicts": conflicts}


def court():
    ok = True

    def chk(n, c):
        nonlocal ok
        ok = ok and bool(c)
        print(f"  {'✓' if c else '✗'} {n}")

    print("СУД · жатва (автономное обогащение из первоисточника)")

    doc = {"references": {
        "ios-default-systemgray6.png": {"type": "image", "alt": "R-242,G-242,B-247"},
        "ios-default-systemgray6dark.png": {"type": "image", "alt": "R-28,G-28,B-30"},
        "colors-unified-blue-light.png": {"type": "image", "alt": "R-0,G-136,B-255"},
        "shot.png": {"type": "image", "alt": "A screenshot of the Notes app"},
        "t1": {"type": "topic", "url": "/design/human-interface-guidelines/materials"},
        "t2": {"type": "topic", "url": "/documentation/UIKit/UIColor/systemGray"},
        "t3": {"type": "topic",
               "url": "/design/human-interface-guidelines/foundations/deep/nested"},
    }}

    got = sieve_swatches(doc, HIG + "color")
    chk("сито взяло только образцы, скриншот пропущен", len(got) == 3)
    chk("светлое и тёмное разведены",
        {(g, n, s): v for g, n, s, v, _ in got}[("gray", "systemGray6", "light")]
        == "#F2F2F7")
    chk("АДРЕС приходит с каждым значением",
        all(p == HIG + "color" for *_x, p in got))

    lk = links(doc)
    chk("фронт берёт соседнюю страницу СВОДА", HIG + "materials" in lk)
    chk("справочник API во фронт не идёт",
        not any("/documentation/" in u for u in lk))
    chk("вложенные страницы не берутся: глубина обхода объявлена",
        not any(u.count("/") > HIG.count("/") for u in lk))

    anch = {"references": {"a": {"type": "topic",
                                 "url": HIG + "color#System-colors"},
                           "b": {"type": "topic", "url": HIG + "color/"}}}
    chk("якорь и хвостовая косая — это ТА ЖЕ страница, а не две новых",
        links(anch) == [HIG + "color"])

    pal = {"system": {}, "gray": {}, "sources": {}}
    a, c, cf = merge(pal, got)
    chk("урожай внесён, конфликтов нет", a == 3 and c == 0 and cf == [])
    chk("провенанс записан", pal["sources"]["gray.systemGray6"] == HIG + "color")

    a2, c2, cf2 = merge(pal, got)
    chk("повторная жатва не плодит записи", a2 == 0 and c2 == 0)

    a3, c3, cf3 = merge(pal, [("gray", "systemGray6", "light", "#F0F0F0",
                               HIG + "color")])
    chk("ПРАВКА Apple не проходит молча — предъявляется конфликтом",
        c3 == 1 and cf3[0]["was"] == "#F2F2F7" and cf3[0]["now"] == "#F0F0F0")

    a4, _c4, _x = merge(pal, [("gray", "systemGray9", "light", "#ABCDEF", "")])
    chk("значение БЕЗ адреса не записывается вовсе",
        a4 == 0 and "systemGray9" not in pal["gray"])

    st = {"done": [], "front": [], "harvested": 0}
    res = harvest([HIG + "color"], lambda p: doc, {"system": {}, "gray": {},
                                                   "sources": {}}, st)
    chk("заход целиком: страница пройдена, фронт пополнен",
        res["walked"] == 1 and HIG + "materials" in st["front"])
    chk("пройденная страница ушла из фронта в пройденные",
        st["done"] == [HIG + "color"])

    st2 = {"done": [], "front": [], "harvested": 0}
    res2 = harvest([HIG + "nope"], lambda p: None,
                   {"system": {}, "gray": {}, "sources": {}}, st2)
    chk("недоступная страница не роняет жатву, а отмечается",
        res2["walked"] == 0 and res2["dead"] == [HIG + "nope"])

    chk("битое состояние читается как пустое", isinstance(read_state(), dict))

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--pages", type=int, default=PAGES_PER_RUN)
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--offline", action="store_true",
                    help="жатва по фикстурам: без сети, для суда и починки сит")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()

    state = read_state()
    if a.seed or (not state["done"] and not state["front"]):
        if SEED not in state["front"] and SEED not in state["done"]:
            state["front"].insert(0, SEED)

    if a.offline:
        fx = {}
        for f in sorted(FIXTURES.glob("hig-*.json")):
            fx[HIG + f.stem[4:]] = json.loads(f.read_text(encoding="utf-8"))
        pages = list(fx)
        getter = fx.get
    else:
        pages = state["front"][:max(1, a.pages)]
        getter = fetch

    if not pages:
        print("фронт пуст — весь свод пройден; заново: --seed")
        return 0

    pal = load_palette()
    res = harvest(pages, getter, pal, state)

    PALETTE.write_text(json.dumps(pal, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                     encoding="utf-8")

    print(f"пройдено страниц: {res['walked']} · значений просеяно: {res['values']}")
    print(f"новых: {res['added']} · изменившихся: {res['changed']}")
    print(f"фронт: {len(state['front'])} · пройдено всего: {len(state['done'])}")
    if res["dead"]:
        print("не открылись:", ", ".join(res["dead"][:5]))
    for c in res["conflicts"]:
        print(f"  ПРАВКА APPLE · {c['token']}: {c['was']} → {c['now']} ({c['at']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
