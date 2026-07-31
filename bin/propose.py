#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ДОБЫТЧИК ПРАВИЛ-КАНДИДАТОВ (ст. 2, ЗКН-Э002).

Зачем орган существует. Правила департамента до сих пор писались руками: AE1
и далее до AE13. Такой способ упирается в одного человека и в его память.
Между тем в библиотеке лежат нормы, добытые обходом из живой документации
Apple, и у КАЖДОЙ есть адрес страницы. Норма с адресом — это готовая заготовка
правила, которую остаётся только связать с проверяемым свойством кода.

Чем это отличается от чужого подхода. Инструменты-конкуренты цитируют
замороженный снимок свода: цитата верна на дату снимка и молча стареет. Здесь
кандидат несёт адрес живой страницы и дату обхода, а обход идёт своим кругом
и сам замечает, что страница изменилась. Правило, которое можно проверить по
первоисточнику, весит больше правила, которое надо принять на веру.

Чего орган НЕ делает. Он не объявляет правила — он предлагает кандидатов.
Правилом кандидат становится, когда у него есть проверяемое свойство кода,
однозначное число и испытание в суде в обе стороны. Предложить — не значит
принять (ст. 7.4: принимает основатель).

Запуск:  python3 bin/propose.py [--lib registry/library] [--out файл]
         python3 bin/propose.py --court
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import atlas  # noqa: E402  (словарь предмета — один на департамент)

HOST = "https://developer.apple.com"

# ЧИСЛО С ЕДИНИЦЕЙ. Только то, что можно сверить с кодом: точки, пиксели,
# миллисекунды, проценты, кратности контраста. Голое число без единицы
# кандидатом не считается — его не с чем сравнивать.
# Единица пишется у Apple тремя способами: сокращением (44 pt), словом
# (16 points), и парой размеров (44x44 pt — здесь одно pt на оба числа).
# Все три обязаны читаться: на живом своде форма «44x44 pt» несёт само
# правило касания, а «16 points» — стандартное поле виджета. Первая версия
# ловила только сокращение и потеряла оба.
QTY = re.compile(
    r"(?P<pair>(?P<w>\d+(?:\.\d+)?)\s*[x×]\s*(?P<h>\d+(?:\.\d+)?))?\s*"
    r"(?(pair)|(?P<num>\d+(?:\.\d+)?))\s*"
    r"(?P<unit>pt\b|px\b|ms\b|s\b|%|:1\b|points?\b|pixels?\b|milliseconds?\b)",
    re.I)

_UNIT = {"point": "pt", "points": "pt", "pixel": "px", "pixels": "px",
         "millisecond": "ms", "milliseconds": "ms"}

# СРАВНЕНИЕ. Норма без направления («44 pt») слабее нормы с направлением
# («не менее 44 pt»): вторая говорит, что считать нарушением.
CMP = (
    (re.compile(r"\b(at least|no less than|minimum(?: of)?|no smaller than|"
                r"or (?:larger|greater))\b", re.I), "min"),
    (re.compile(r"\b(at most|no more than|maximum(?: of)?|no larger than|"
                r"or (?:smaller|less))\b", re.I), "max"),
    (re.compile(r"\b(exactly|always)\b", re.I), "eq"),
)

# СВЯЗЬ С КОДОМ. Слева — слово нормы, справа — свойство, которое департамент
# умеет увидеть в исходнике клиента. Без такой связи кандидат остаётся
# знанием, но не становится проверкой.
BIND = (
    (re.compile(r"\b(tap|touch|hit)\s*(target|area)|tappable|"
                r"controls?\s+are\s+a\s+minimum\s+size|"
                r"minimum\s+size\s+of\s+\d+\s*[x×]|"
                r"comfortable\s+minimum\s+(?:size|target)", re.I),
     "min-width/min-height интерактивного элемента"),
    (re.compile(r"\bcorner radius|rounded corner", re.I), "border-radius"),
    (re.compile(r"\bcontrast ratio|contrast of", re.I), "контраст пары цветов"),
    (re.compile(r"\b(animation|transition)\b.*\b(duration|last)", re.I),
     "transition-duration / animation-duration"),
    (re.compile(r"\bline (height|spacing)|leading\b", re.I), "line-height"),
    (re.compile(r"\b(letter|character) spacing|tracking\b", re.I), "letter-spacing"),
    (re.compile(r"\bfont size|type size|point size\b", re.I), "font-size"),
    (re.compile(r"\b(margin|padding|inset|spacing)\b", re.I), "margin / padding"),
    (re.compile(r"\bopacity|alpha\b", re.I), "opacity"),
    (re.compile(r"\bblur\b", re.I), "backdrop-filter: blur()"),
    (re.compile(r"\bstroke|border width|line width\b", re.I), "border-width"),
)


def bind_of(text: str):
    """Свойство кода, к которому норму можно привязать. None — нельзя."""
    for rx, prop in BIND:
        if rx.search(text):
            return prop
    return None


def cmp_of(text: str) -> str:
    """Направление нормы: min / max / eq / none."""
    for rx, kind in CMP:
        if rx.search(text):
            return kind
    return "none"


def quantities(text: str) -> list:
    """Числа с единицами, приведённые к паре (значение, единица).

    Пара «44x44 pt» возвращается ОДНИМ значением — меньшей стороной: норма
    касания говорит о минимальном размере, и судить надо по узкому месту.
    """
    out = []
    for m in QTY.finditer(text):
        unit = m.group("unit").lower().rstrip()
        unit = _UNIT.get(unit, unit)
        if m.group("pair"):
            out.append((min(float(m.group("w")), float(m.group("h"))), unit))
        else:
            out.append((float(m.group("num")), unit))
    return out


def candidates(rows: list) -> list:
    """Нормы → кандидаты в правила. Один кандидат на (свойство, число, единица).

    Кандидаты копятся, а не перезаписываются: одна и та же норма, встреченная
    на нескольких страницах, — довод в её пользу, и число встреч сохраняется
    вместе со всеми адресами. Довод без адреса не бывает (ЗКН-Э002).
    """
    acc = defaultdict(lambda: {"n": 0, "sources": [], "texts": []})
    for pid, law in rows:
        if not atlas.DESIGN.search(law):
            continue
        prop = bind_of(law)
        if not prop:
            continue
        for val, unit in quantities(law):
            key = (prop, val, unit, cmp_of(law))
            a = acc[key]
            a["n"] += 1
            if pid not in a["sources"]:
                a["sources"].append(pid)
            if len(a["texts"]) < 3:
                a["texts"].append(law[:200])
    out = []
    for (prop, val, unit, kind), a in acc.items():
        out.append({"property": prop, "value": val, "unit": unit, "cmp": kind,
                    "hits": a["n"], "pages": len(a["sources"]),
                    "sources": [f"{HOST}{s}" for s in a["sources"][:5]],
                    "texts": a["texts"],
                    "primary": any(s.startswith("/design/") for s in a["sources"])})
    # Порядок: сначала из свода правил, затем по числу страниц, затем по
    # числу встреч. Детерминирован — один и тот же вход даёт один выход.
    out.sort(key=lambda c: (not c["primary"], -c["pages"], -c["hits"],
                            c["property"], c["value"]))
    return out


def read_library(lib: Path, only_primary: bool = False) -> list:
    rows = []
    files = sorted(lib.glob("*.jsonl"))
    if only_primary:
        files = [f for f in files if "human-interface" in f.name]
    for f in files:
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            rows.append((r.get("id", ""), r.get("law", "")))
    return rows


def render(cands: list, total_rows: int) -> str:
    prim = sum(1 for c in cands if c["primary"])
    head = ["# BXE · кандидаты в правила", "",
            f"Норм просмотрено: {total_rows} · кандидатов: {len(cands)} · "
            f"из них со ссылкой на свод правил: {prim}", "",
            "Кандидат — не правило. Правилом он становится, когда у него есть "
            "проверяемое свойство кода, однозначное число и испытание в суде "
            "в обе стороны. Принимает основатель (ст. 7.4).", "",
            "| свойство | норма | направление | страниц | встреч | первоисточник |",
            "|---|---|---|---|---|---|"]
    for c in cands[:80]:
        head.append(f"| {c['property']} | {c['value']:g} {c['unit']} | {c['cmp']} "
                    f"| {c['pages']} | {c['hits']} | "
                    f"{'да' if c['primary'] else 'нет'} |")
    head += ["", "## Адреса", ""]
    for c in cands[:40]:
        head.append(f"- **{c['property']} {c['value']:g} {c['unit']}** ({c['cmp']}) — "
                    f"{', '.join(c['sources'][:2])}")
        if c["texts"]:
            head.append(f"  - «{c['texts'][0][:150]}»")
    return "\n".join(head) + "\n"


def court() -> int:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  ✓ " if cond else "  ✗ ") + name)
        ok = ok and cond

    print("СУД · добытчик правил-кандидатов (без сети)")
    check("число с единицей снято: 44 pt", quantities("at least 44 pt") == [(44.0, "pt")])
    check("голое число не считается нормой: единицы нет",
          quantities("about 44 items") == [])
    check("направление нормы прочитано: минимум", cmp_of("at least 44 pt") == "min")
    check("направление нормы прочитано: максимум",
          cmp_of("no more than 300 ms") == "max")
    check("без слов направления — none", cmp_of("the size is 44 pt") == "none")
    check("связь с кодом найдена: касание → размер интерактивного элемента",
          bind_of("Use a minimum tappable area of 44x44 pt.").startswith("min-width"))
    check("единица словом читается: 16 points → (16, pt)",
          quantities("a margin of 16 points") == [(16.0, "pt")])
    check("пара размеров читается меньшей стороной: 44x44 pt → одно 44 pt",
          quantities("a minimum size of 44x44 pt") == [(44.0, "pt")])
    _hig = ("Make sure frequently used controls are a minimum size of 44x44 pt, "
            "and less important controls are a minimum size of 28x28 pt.")
    check("живая формулировка свода ловится целиком: 44 и 28, минимум, связь",
          quantities(_hig) == [(44.0, "pt"), (28.0, "pt")]
          and cmp_of(_hig) == "min"
          and bind_of(_hig).startswith("min-width"))
    check("связь с кодом найдена: скругление → border-radius",
          bind_of("Use a corner radius of 12 pt for cards.") == "border-radius")
    check("ломаю → красный: норма без связи с кодом кандидатом не становится",
          bind_of("Design with clarity and deference in mind.") is None)

    rows = [("/design/human-interface-guidelines/layout",
             "Use a minimum tappable area of 44x44 pt for controls."),
            ("/design/human-interface-guidelines/accessibility",
             "Provide a tap target of at least 44 pt on every side."),
            ("/documentation/uikit/uiview",
             "The corner radius of the card is 12 pt."),
            ("/documentation/accelerate/fft",
             "The FFT length must be 8 elements.")]
    c = candidates(rows)
    props = [(x["property"][:9], x["value"], x["pages"]) for x in c]
    check("чиню → зелёный: две страницы про 44 pt слились в одного кандидата "
          "с двумя адресами",
          any(p[1] == 44.0 and p[2] == 2 for p in props))
    check("чужая проза отсеяна: БПФ кандидатом не стал",
          all("FFT" not in t for x in c for t in x["texts"]))
    check("свод правил идёт впереди справочника",
          c[0]["primary"] is True)
    check("у каждого кандидата есть адрес, и он ведёт на apple.com",
          all(x["sources"] and x["sources"][0].startswith(HOST) for x in c))
    check("порядок детерминирован", candidates(rows) == c)
    txt = render(c, len(rows))
    check("отчёт называет и число кандидатов, и долю из свода",
          "кандидатов:" in txt and "свод правил" in txt)
    check("кандидат не выдаётся за правило",
          "Кандидат — не правило" in txt)
    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lib", default=str(ROOT / "registry" / "library"))
    ap.add_argument("--out", default=str(ROOT / "registry" / "standards" / "CANDIDATES.md"))
    ap.add_argument("--primary-only", action="store_true")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()
    rows = read_library(Path(a.lib), a.primary_only)
    c = candidates(rows)
    Path(a.out).write_text(render(c, len(rows)), encoding="utf-8")
    Path(a.out).with_suffix(".json").write_text(
        json.dumps(c, ensure_ascii=False), encoding="utf-8")
    prim = sum(1 for x in c if x["primary"])
    print(f"норм просмотрено {len(rows)} · кандидатов {len(c)} · из свода {prim}")
    for x in c[:8]:
        print(f"  {x['property']} {x['value']:g} {x['unit']} ({x['cmp']}) · "
              f"страниц {x['pages']} · {x['sources'][0]}")
    print(f"записано: {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
