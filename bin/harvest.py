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
import gzip
import hashlib
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
CORPUS = ROOT / "registry" / "corpus" / "hig"
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


def _flat(cell):
    """Ячейка таблицы → плоский текст. Ссылка отдаёт своё имя: в таблицах
    Apple третья колонка — это имя API, и оно живёт ссылкой, а не текстом."""
    parts = []

    def w(o):
        if isinstance(o, dict):
            if o.get("type") == "text" and o.get("text"):
                parts.append(o["text"])
            elif o.get("type") == "reference" and o.get("identifier"):
                parts.append(str(o["identifier"]).rstrip("/").split("/")[-1])
            for v in o.values():
                w(v)
        elif isinstance(o, list):
            for x in o:
                w(x)
    w(cell)
    return " ".join(x.strip() for x in parts if x and x.strip()).strip()


def _tables(node):
    if isinstance(node, dict):
        if node.get("type") == "table":
            yield node
        for v in node.values():
            yield from _tables(v)
    elif isinstance(node, list):
        for x in node:
            yield from _tables(x)


def _walk_ordered(node, state):
    """Обходит содержимое ПО ПОРЯДКУ, помня последний заголовок каждого
    уровня. Только порядок и связывает таблицу с её разделом: в JSON
    таблица не ссылается на заголовок, она просто идёт после него."""
    if isinstance(node, dict):
        t = node.get("type")
        if t == "heading" and node.get("text"):
            lvl = int(node.get("level") or 2)
            state["h"] = {k: v for k, v in state["h"].items() if k < lvl}
            state["h"][lvl] = node["text"].strip()
        elif t == "table":
            yield node, [state["h"][k] for k in sorted(state["h"])]
            return
        for v in node.values():
            yield from _walk_ordered(v, state)
    elif isinstance(node, list):
        for x in node:
            yield from _walk_ordered(x, state)


def sieve_tables(doc, page):
    """Сито таблиц. Возвращает ("закон", текст, адрес).

    Зачем. Текстовый обход расплющивает таблицу в поток слов, и связь
    «роль → назначение → имя API» распадается. А это и есть самая
    применимая часть свода: на вопрос «каким цветом вторичный текст»
    отвечает ИМЕННО строка таблицы, а не абзац рядом с ней.

    Строка склеивается с заголовками колонок, поэтому закон читается
    отдельно от таблицы и годится в выдачу дознания как есть.
    """
    out = []
    body = doc.get("content") or doc.get("primaryContentSections") or doc
    for t, heads in _walk_ordered(body, {"h": {}}):
        rows = t.get("rows") or []
        if len(rows) < 2:
            continue
        head = [_flat(c) for c in rows[0]]
        if not any(head):
            continue
        for r in rows[1:]:
            cells = [_flat(c) for c in r]
            if not any(cells):
                continue
            pairs = [f"{h}: {c}" if h else c
                     for h, c in zip(head + [""] * len(cells), cells) if c]
            if len(pairs) < 2:
                continue
            law = " · ".join(pairs)
            if heads:
                # Раздел идёт ПЕРВЫМ: он задаёт платформу и режим, без
                # которых числа строки не значат ничего.
                law = "[" + " › ".join(heads) + "] " + law
            out.append(("закон", law, page))
    return out


# Сита объявлены с ВИДОМ урожая: одно даёт значения в палитру, другое —
# законы в библиотеку. Смешивать нельзя: у них разный вес свидетельства и
# разное место хранения.
SIEVES = (("образцы цвета", sieve_swatches, "палитра"),
          ("таблицы свода", sieve_tables, "закон"))


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


def _shard(page):
    h = hashlib.sha256(page.encode("utf-8")).hexdigest()[:2]
    return CORPUS / f"{h}.jsonl.gz"


def corpus_put(page, doc):
    """Сохранить СЫРОЙ документ страницы. Идемпотентно по адресу.

    Родословная. Работник просеивал страницу и выбрасывал её. Из этого
    следовало, что ЛЮБОЕ новое сито требует заново обойти весь свод: сотни
    страниц и недели вежливого хода ради одной новой формы записи. Инструмент
    был структурно неспособен улучшать собственное извлечение иначе как
    повторным хождением к Apple.

    Атлас departamentа прошёл эту же ошибку и закрыл её хранением корпуса.
    Жатва повторять её не будет: сырьё хранится, сита правятся офлайн,
    перемол идёт по складу (`--remill`).
    """
    # Хранится СОДЕРЖИМОЕ, а не выжимка из него. Первая кладка держала
    # только таблицы — и платформа таблицы пропала: страница типографики
    # покрывает iOS, macOS, watchOS и tvOS, а строка «Large Title · 31 pt»
    # без раздела неотличима от «Large Title · 34 pt». Число без платформы
    # ХУЖЕ отсутствующего: оно выглядит как знание.
    keep = {"page": page,
            "content": doc.get("primaryContentSections") or [],
            "references": {k: {"type": v.get("type"), "alt": v.get("alt"),
                               "url": v.get("url"), "title": v.get("title")}
                           for k, v in (doc.get("references") or {}).items()}}
    try:
        CORPUS.mkdir(parents=True, exist_ok=True)
        f = _shard(page)
        old = []
        if f.exists():
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                old = [l for l in fh.read().splitlines()
                       if l.strip() and json.loads(l).get("page") != page]
        with gzip.open(f, "wt", encoding="utf-8") as fh:
            fh.write("\n".join(old + [json.dumps(keep, ensure_ascii=False)]) + "\n")
        return True
    except (OSError, ValueError):
        # Склад — удобство, а не обязанность: невозможность записать не имеет
        # права отменить жатву.
        return False


def corpus_read():
    """Весь склад: адрес → документ. Для перемола без сети."""
    out = {}
    if not CORPUS.exists():
        return out
    for f in sorted(CORPUS.glob("*.jsonl.gz")):
        try:
            with gzip.open(f, "rt", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    d = json.loads(line)
                    if d.get("page"):
                        out[d["page"]] = d
        except (OSError, ValueError):
            continue
    return out


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


LAWS = ROOT / "registry" / "library" / "hig-tables.jsonl"


def put_laws(rows, path=None):
    """Кладёт законы таблиц в библиотеку. Возвращает число НОВЫХ.

    Дубли схлопываются по тексту: одна и та же таблица встречается на
    нескольких страницах свода, и цитировать её дважды департамент не будет
    (та же причина, что у схлопывания близнецов в дознании).
    """
    f = Path(path) if path else LAWS
    have = set()
    if f.exists():
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                have.add(json.loads(line).get("law"))
            except ValueError:
                continue
    fresh = []
    for _kind, text, page in rows:
        if not page or not text or text in have:
            continue
        have.add(text)
        fresh.append({"id": page, "law": text})
    if fresh:
        try:
            f.parent.mkdir(parents=True, exist_ok=True)
            with f.open("a", encoding="utf-8") as fh:
                for r in fresh:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        except OSError:
            return 0
    return len(fresh)


def harvest(pages, getter, pal, state, budget=None):
    """Один заход жатвы. getter(page) → документ или None.

    Фронт берётся ЖИВЫМ. Первая редакция брала срез фронта на входе, и после
    посева, когда во фронте одна страница, прогон обходил ровно одну — свод
    в 40 страниц отстраивался бы полтора месяца по странице в сутки.
    Страницы, найденные ВНУТРИ прогона, доступны тому же прогону, пока не
    исчерпан бюджет вежливости.
    """
    rows, laws, walked, dead = [], [], [], []
    queue = list(pages)
    limit = budget if budget is not None else len(queue)
    seen = set()
    while queue and len(walked) + len(dead) < limit:
        page = queue.pop(0)
        if page in seen:
            continue
        seen.add(page)
        doc = getter(page)
        if not doc:
            dead.append(page)
            continue
        walked.append(page)
        corpus_put(page, doc)
        for _name, sieve, kind in SIEVES:
            got = sieve(doc, page)
            (laws if kind == "закон" else rows).extend(got)
        for u in links(doc):
            if u in state["done"] or u in seen:
                continue
            if u not in state["front"]:
                state["front"].append(u)
            if u not in queue:
                queue.append(u)
    added, changed, conflicts = merge(pal, rows)
    laws_new = put_laws(laws)
    for p in walked:
        if p not in state["done"]:
            state["done"].append(p)
        if p in state["front"]:
            state["front"].remove(p)
    state["harvested"] = state.get("harvested", 0) + added + changed
    return {"walked": len(walked), "dead": dead, "values": len(rows),
            "added": added, "changed": changed, "conflicts": conflicts,
            "laws": laws_new}


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
                                                   "sources": {}}, st, budget=1)
    chk("заход целиком: страница пройдена, фронт пополнен",
        res["walked"] == 1 and HIG + "materials" in st["front"])

    # Живой фронт: найденное внутри прогона доступно этому же прогону.
    st3 = {"done": [], "front": [], "harvested": 0}
    chain = {HIG + "a": {"references": {"t": {"type": "topic",
                                              "url": HIG + "b"}}},
             HIG + "b": {"references": {"t": {"type": "topic",
                                              "url": HIG + "c"}}},
             HIG + "c": {"references": {}}}
    r3 = harvest([HIG + "a"], chain.get, {"system": {}, "gray": {},
                                          "sources": {}}, st3, budget=3)
    chk("найденное ВНУТРИ прогона обходится тем же прогоном",
        r3["walked"] == 3)
    st4 = {"done": [], "front": [], "harvested": 0}
    r4 = harvest([HIG + "a"], chain.get, {"system": {}, "gray": {},
                                          "sources": {}}, st4, budget=2)
    chk("бюджет вежливости соблюдается: больше не берём",
        r4["walked"] == 2 and HIG + "c" in st4["front"])
    chk("пройденная страница ушла из фронта в пройденные",
        st["done"] == [HIG + "color"])

    st2 = {"done": [], "front": [], "harvested": 0}
    res2 = harvest([HIG + "nope"], lambda p: None,
                   {"system": {}, "gray": {}, "sources": {}}, st2)
    chk("недоступная страница не роняет жатву, а отмечается",
        res2["walked"] == 0 and res2["dead"] == [HIG + "nope"])

    import tempfile as _tf
    import shutil as _sh
    _save = globals()["CORPUS"]
    globals()["CORPUS"] = Path(_tf.mkdtemp(prefix="eyes-corp-")) / "hig"
    chk("страница кладётся на склад", corpus_put(HIG + "color", doc) is True)
    store = corpus_read()
    chk("склад читается обратно", list(store) == [HIG + "color"])
    chk("на складе лежат ССЫЛКИ — сырьё для будущих сит",
        "ios-default-systemgray6.png" in store[HIG + "color"]["references"])
    corpus_put(HIG + "color", doc)
    chk("повторная кладка не двоит страницу", len(corpus_read()) == 1)
    got2 = sieve_swatches(store[HIG + "color"], HIG + "color")
    chk("сито работает по СКЛАДУ так же, как по живой странице",
        len(got2) == len(got))
    _sh.rmtree(globals()["CORPUS"].parent, ignore_errors=True)
    globals()["CORPUS"] = _save

    # ── сито таблиц ───────────────────────────────────────────────────────
    def _cell(txt):
        return [{"type": "paragraph", "inlineContent": [{"type": "text",
                                                         "text": txt}]}]

    tdoc = {"primaryContentSections": [
        {"type": "heading", "level": 2, "text": "iOS, iPadOS"},
        {"type": "heading", "level": 3, "text": "Specifications"},
        {"type": "table", "rows": [
        [_cell("Color"), _cell("Use for…"), _cell("UIKit API")],
        [_cell("Secondary label"), _cell("Secondary content"),
         [{"type": "reference", "identifier": "doc://x/UIColor/secondaryLabel"}]],
        [_cell(""), _cell(""), _cell("")],
    ]}]}
    tl = sieve_tables(tdoc, HIG + "color")
    chk("строка таблицы стала законом с заголовками колонок",
        len(tl) == 1 and "Color: Secondary label" in tl[0][1]
        and "UIKit API: secondaryLabel" in tl[0][1])
    chk("РАЗДЕЛ идёт первым: платформа и режим не теряются",
        tl[0][1].startswith("[iOS, iPadOS › Specifications]"))

    deep = {"primaryContentSections": [
        {"type": "heading", "level": 2, "text": "iOS"},
        {"type": "table", "rows": [[_cell("A")], [_cell("1")]]},
        {"type": "heading", "level": 2, "text": "macOS"},
        {"type": "table", "rows": [[_cell("A"), _cell("B")],
                                   [_cell("Large Title"), _cell("31")]]},
    ]}
    dl = sieve_tables(deep, "p")
    chk("следующий заголовок ТОГО ЖЕ уровня вытесняет прежний",
        dl and dl[-1][1].startswith("[macOS]"))
    chk("таблица iOS не подписана разделом macOS",
        all("macOS" not in x[1] for x in dl[:-1]))
    chk("имя API взято из ССЫЛКИ, а не потеряно",
        "secondaryLabel" in tl[0][1])
    chk("пустая строка таблицы законом не становится",
        all(x[1].strip() for x in tl))
    chk("адрес страницы неотделим от закона таблицы",
        tl[0][2] == HIG + "color")
    chk("таблица из одной строки закона не даёт",
        sieve_tables({"a": {"type": "table", "rows": [[_cell("H")]]}}, "p") == [])

    _lf = Path(_tf.mkdtemp(prefix="eyes-law-")) / "t.jsonl"
    chk("закон записан в библиотеку", put_laws(tl, _lf) == 1)
    chk("повтор той же таблицы не плодит закон", put_laws(tl, _lf) == 0)
    chk("закон без адреса не пишется",
        put_laws([("закон", "нечто", "")], _lf) == 0)
    _sh.rmtree(_lf.parent, ignore_errors=True)

    chk("битое состояние читается как пустое", isinstance(read_state(), dict))

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--pages", type=int, default=PAGES_PER_RUN)
    ap.add_argument("--seed", action="store_true")
    ap.add_argument("--offline", action="store_true",
                    help="жатва по фикстурам: без сети, для суда и починки сит")
    ap.add_argument("--remill", action="store_true",
                    help="перемолоть СКЛАД новыми ситами: без сети, без "
                         "повторного хода к Apple")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()

    state = read_state()
    if a.seed or (not state["done"] and not state["front"]):
        if SEED not in state["front"] and SEED not in state["done"]:
            state["front"].insert(0, SEED)

    if a.remill:
        store = corpus_read()
        if not store:
            print("склад пуст — сначала пройди фронт жатвой")
            return 1
        pal = load_palette()
        st = {"done": list(state["done"]), "front": [], "harvested": 0}
        res = harvest(list(store), store.get, pal, st)
        PALETTE.write_text(json.dumps(pal, ensure_ascii=False, indent=1),
                           encoding="utf-8")
        print(f"перемолото страниц склада: {res['walked']} · "
              f"значений {res['values']} · новых {res['added']} · "
              f"изменившихся {res['changed']}")
        for c in res["conflicts"]:
            print(f"  ПРАВКА · {c['token']}: {c['was']} → {c['now']}")
        return 0

    if a.offline:
        fx = {}
        for f in sorted(FIXTURES.glob("hig-*.json")):
            fx[HIG + f.stem[4:]] = json.loads(f.read_text(encoding="utf-8"))
        pages = list(fx)
        getter = fx.get
    else:
        pages = list(state["front"])
        getter = fetch

    if not pages:
        print("фронт пуст — весь свод пройден; заново: --seed")
        return 0

    pal = load_palette()
    res = harvest(pages, getter, pal, state,
                  budget=None if a.offline else max(1, a.pages))

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
