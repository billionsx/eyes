#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ДВОЙНОЕ СВИДЕТЕЛЬСТВО (ст. 2, ЗКН-Э002).

Зачем орган. Воронка добытчика измерена и вынесла приговор: из 30 125 норм
библиотеки число с единицей несут ШЕСТЬДЕСЯТ ВОСЕМЬ. Расширять словарь связей
бессмысленно — потолок стоит не там. Текстовый свод Apple физически не
является источником чисел, и попытка вывести правила только из него упирается
в две дюжины кандидатов, сколько ни расширяй.

Но и обратное неверно. Число, снятое с кадра, — это то, что Apple ОТГРУЗИЛА;
норма из свода — то, что Apple НАПИСАЛА. По отдельности каждое свидетельство
уязвимо: замер можно списать на частный случай продукта, цитату — на то, что
свод устарел относительно кода. Вместе они несокрушимы.

Что делает орган. Сшивает измеренную базу с библиотекой: под каждое
измеренное число ищет дознанием (bin/law.py) норму свода о ТОМ ЖЕ свойстве и
выносит один из четырёх вердиктов.

  ПОДТВЕРЖДЕНО  свод называет то же число. Сильнейшее свидетельство:
                написанное и отгруженное совпали.
  СОГЛАСОВАНО   свод говорит о свойстве, своего числа не называет и
                измеренному не противоречит.
  ПРОТИВОРЕЧИЕ  свод называет ДРУГОЕ число по тому же свойству. Это не сбой
                органа и не повод прятать: расхождение написанного с
                отгруженным — самостоятельная находка, и обе стороны
                предъявляются с адресами. Разрешает основатель (ст. 7.4).
  НЕМО          свод молчит. Число держится на одном замере — так и пишется,
                без прикрытия цитатой.

Почему это позиция, которую нельзя скопировать. Конкурент, стоящий на
замороженном снимке свода (hig-doctor и родня), имеет только слова: он не
может заметить, что Apple пишет одно, а отгружает другое. Инструмент, стоящий
только на замере, имеет только числа: он не может сослаться. Департамент,
держащий оба конца, единственный способен ПРЕДЪЯВИТЬ РАСХОЖДЕНИЕ.

Что орган НЕ делает. Не правит базу и не правит библиотеку. Он свидетельствует.

Запуск:
    python3 bin/attest.py                 — свод в registry/state/ATTEST.md
    python3 bin/attest.py --json
    python3 bin/attest.py --only tap_target
    python3 bin/attest.py --court         — суд, без сети и библиотеки
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import law as law_mod  # noqa: E402  (дознание — одно на департамент)
import propose  # noqa: E402  (разбор чисел с единицами — один на департамент)

TOKENS = ROOT / "registry" / "standards" / "tokens.json"
OUT = ROOT / "registry" / "state" / "ATTEST.md"

# Сколько законов дознания рассматривать под одно свойство. Глубина восемь,
# а не три: мусор теперь отсекает якорь свойства, а не короткий список, и
# нужная формулировка часто лежит не первой. Отсев перенесён с длины
# выдачи на смысл — это и позволяет смотреть глубже без потери точности.
DEPTH = 8

# ПРЕДМЕТЫ СВИДЕТЕЛЬСТВА. Таблица объявлена, а не выведена: какое измеренное
# число каким запросом ищется в своде и в каких единицах сравнивается.
# Угадывать здесь нельзя — это правовой инструмент, а не эвристика.
#   path   — путь в измеренной базе (узел.ключ)
#   query  — чем спрашивать библиотеку
#   anchor — ЯКОРЬ СВОЙСТВА. Норма засчитывается свидетельством, только если
#            говорит об этом свойстве буквально. Без якоря BM25 выдаёт текст,
#            делящий с запросом общую лексику, и он проходит за «согласие»:
#            «Prefer a tab bar for navigation» — не норма о ВЫСОТЕ таб-бара.
#            Слабое свидетельство, выданное за согласие, надувает вес правила
#            ровно так же, как обрезанный долг надувал балл сертификата.
#            Якорь объявляется, а не выводится: это правовой инструмент.
#   unit   — единица, в которой числа сопоставимы
#   tol    — допуск сравнения (абсолютный, в тех же единицах)
SUBJECTS = (
    ("tap_target.min_pt", "touch target minimum size tappable control",
     r"\b(tap|touch|tappable|hit|control|target|button|finger)\b", "pt", 0.0),
    ("tap_target.secondary_min_pt",
     "less important controls minimum size menus",
     r"\b(tap|touch|tappable|control|menu)\b", "pt", 0.0),
    ("contrast.min_ratio", "contrast ratio between colors minimum",
     r"\bcontrast\b", ":1", 0.05),
    ("geometry.corner_form_required_above_pt",
     "corner radius rounded corners concentric",
     r"\b(corner|radius|rounded)\b", "pt", 0.0),
    ("geometry.radius_card_pt", "corner radius card rounded rectangle",
     r"\b(corner|radius|rounded)\b", "pt", 0.0),
    ("geometry.tabbar_height_pt", "tab bar height size",
     r"\btab bar\b(?=.*\b(height|tall|size)\b)|\b(height|tall)\b(?=.*\btab bar\b)",
     "pt", 0.0),
    ("geometry.inset_card_pt", "layout margins inset edges content",
     r"\b(margin|inset)\b", "pt", 0.0),
    ("motion.press_response_ms_max",
     "animation duration responsive feedback press",
     r"\b(press|tap|touch)\b", "ms", 0.0),
    ("motion.min_ms_for_curve", "animation duration transition timing",
     r"\b(animation|animate|transition)\b", "ms", 0.0),
    ("typography.tracking_cap_px", "letter spacing tracking type size",
     r"\b(tracking|letter[- ]spacing|kern)\b", "px", 0.0),
)



def dig(tree, path):
    """Значение по пути 'узел.ключ'. None — если пути нет."""
    cur = tree
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur if isinstance(cur, (int, float)) else None


def stated(laws, unit):
    """Числа нужной единицы, названные сводом. Возвращает [(значение, закон)].

    Единица обязательна: 44 в норме о касании и 44 в номере версии — разные
    сущности, и голое совпадение цифр свидетельством не является.
    """
    out = []
    for rec, _ in laws:
        for val, u in propose.quantities(rec["law"]):
            if u == unit:
                out.append((val, rec))
    return out


# НОРМАТИВНОСТЬ. Текст, описывающий устройство API («The property contains
# the edge inset values»), не является нормой о свойстве — им нельзя
# подпереть измеренное число. Согласие вправе давать только предписание.
NORMATIVE = re.compile(
    r"\b(must|should|shall|need to|make sure|ensure|avoid|never|always|"
    r"prefer|recommend(?:ed)?|at least|no less|no more|no smaller|no larger|"
    r"minimum|maximum|don't|do not)\b", re.I)


def anchored(rec, anchor):
    """Говорит ли норма об этом свойстве буквально.

    Якорь проверяется по сырому тексту И по свёрнутому. Свод пишет во
    множественном («respects the layout margins»), а якорь объявлен в
    единственном («margin») — без свёртки граница слова не встаёт после
    «margin» в «margins», и норма теряется. Свёртка — та же, что у
    дознания: один фолд на департамент, двух правд о слове не бывает.
    """
    if re.search(anchor, rec["law"], re.I):
        return True
    return bool(re.search(anchor, " ".join(law_mod.tokenize(rec["law"])), re.I))


def verdict(measured, laws, anchor, unit, tol):
    """Вердикт по предмету. Возвращает (метка, довод-или-None, число-или-None).

    Третьим членом идёт ИМЕННО СОВПАВШЕЕ число, а не первое число нормы.
    Норма часто перечисляет пару порогов в одном предложении («44 pt для
    частых контролов и 28 pt для меню»), и печатать первое — значит
    свидетельствовать не о том, что подтверждено.

    Свидетелем становится только норма, зацепленная якорем свойства. Всё,
    что якорь не держит, — лексическое совпадение, и оно объявляется
    молчанием свода, а не согласием.
    """
    held = [(rec, s) for rec, s in laws if anchored(rec, anchor)]
    if not held:
        return "НЕМО", None, None
    said = stated(held, unit)
    if said:
        # Совпадение числа — свидетельство само по себе, нормативность для
        # него не требуется: если свод НАЗЫВАЕТ то же число, довод состоялся.
        for val, rec in said:
            if abs(val - measured) <= tol:
                return "ПОДТВЕРЖДЕНО", rec, val
        val, rec = min(said, key=lambda p: abs(p[0] - measured))
        return "ПРОТИВОРЕЧИЕ", rec, val
    # Числа свод не назвал. Согласие вправе давать только ПРЕДПИСАНИЕ и
    # только из СВОДА НОРМ. Справочник API — не источник дизайн-нормы: это
    # доказано нулевым урожаем добытчика, и подпирать замер фразой вида
    # «minimum duration of the long press» значит выдавать имя параметра за
    # норму. Слово «minimum» в справочнике встречается сотнями и означает
    # устройство ручки, а не требование к интерфейсу. Молчание свода —
    # честный вердикт; ложное согласие — надутый вес правила.
    for rec, _ in held:
        if rec["fw"] in law_mod.PRIVILEGED and NORMATIVE.search(rec["law"]):
            return "СОГЛАСОВАНО", rec, None
    return "НЕМО", None, None


def attest(tokens, records, only=None):
    """Свидетельство по всем предметам. Детерминировано: тот же вход — тот же
    выход, порядок предметов — объявленный, а не по счёту BM25."""
    out = []
    for path, query, anchor, unit, tol in SUBJECTS:
        if only and not path.startswith(only):
            continue
        measured = dig(tokens, path)
        if measured is None or isinstance(measured, str):
            # ДЫРА, НО СВОД МОЖЕТ ГОВОРИТЬ. Раньше отсутствие замера обрывало
            # свидетельство: орган печатал «НЕТ ЗАМЕРА» и не смотрел, назвал ли
            # свод число сам. А для части величин замер невозможен в принципе —
            # вес начертания и доля высоты прописной не лежат на экране, — и
            # там ВЫПИСКА ПЕРВОИСТОЧНИКА С АДРЕСОМ есть единственный законный
            # путь. Молчать о том, что путь есть, — то же молчание, которое
            # запрещает ЗКН-Э001.
            laws = law_mod.rank(records, query, DEPTH)
            held = [(rec, sc) for rec, sc in laws if anchored(rec, anchor)]
            said = stated(held, unit) if held else []
            if said:
                vals = sorted({round(v, 3) for v, _ in said})
                val, rec = said[0]
                out.append({"path": path,
                            "verdict": "ТОЛЬКО СВОД" if len(vals) == 1
                                       else "СВОД РАЗНОГЛАСИТ",
                            "measured": None, "unit": unit,
                            "law": rec["law"], "id": rec["id"],
                            "stated": val, "variants": vals})
                continue
            out.append({"path": path, "verdict": "НЕТ ЗАМЕРА", "measured": None,
                        "unit": unit, "law": None, "id": None, "stated": None})
            continue
        laws = law_mod.rank(records, query, DEPTH)
        mark, rec, said = verdict(float(measured), laws, anchor, unit, tol)
        out.append({"path": path, "verdict": mark, "measured": measured,
                    "unit": unit,
                    "law": rec["law"] if rec else None,
                    "id": rec["id"] if rec else None,
                    "stated": said})
    return out


def render(rows):
    order = {"ПОДТВЕРЖДЕНО": 0, "ПРОТИВОРЕЧИЕ": 1, "СОГЛАСОВАНО": 2,
             "ТОЛЬКО СВОД": 3, "СВОД РАЗНОГЛАСИТ": 4, "НЕМО": 5,
             "НЕТ ЗАМЕРА": 6}
    tally = {}
    for r in rows:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1

    L = ["# ДВОЙНОЕ СВИДЕТЕЛЬСТВО · замер против свода",
         "",
         "Каждая строка сшивает число, снятое с кадров операционной системы, "
         "с нормой, написанной Apple словами. Совпадение усиливает правило "
         "вдвое; расхождение — самостоятельная находка и предъявляется, "
         "а не прячется (ст. 7.4: разрешает основатель).",
         "",
         "| вердикт | предмет | замер | свод говорит | адрес нормы |",
         "|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda x: (order.get(x["verdict"], 9), x["path"])):
        m = "—" if r["measured"] is None else f"{r['measured']} {r['unit']}"
        s = "—" if r["stated"] is None else f"{r['stated']} {r['unit']}"
        addr = r["id"] or "—"
        L.append(f"| {r['verdict']} | `{r['path']}` | {m} | {s} | {addr} |")

    L += ["", "## Счёт", ""]
    for k in sorted(tally, key=lambda x: order.get(x, 9)):
        L.append(f"- {k}: {tally[k]}")

    contra = [r for r in rows if r["verdict"] == "ПРОТИВОРЕЧИЕ"]
    if contra:
        L += ["", "## Расхождения написанного с отгруженным", "",
              "Ниже — места, где свод Apple называет одно число, а кадры "
              "операционной системы дают другое. Ни одна сторона не "
              "объявляется правой автоматически.", ""]
        for r in contra:
            L += [f"**`{r['path']}`** — замер {r['measured']} {r['unit']}, "
                  f"свод {r['stated']} {r['unit']}",
                  f"> {r['law']}",
                  f"> адрес: {r['id']}", ""]
    return "\n".join(L) + "\n"


def court():
    """Суд органа. Библиотека и база кладутся на месте — ни сети, ни диска."""
    ok = True

    def check(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    print("СУД · двойное свидетельство")

    tok = {"tap_target": {"min_pt": 44}, "geometry": {"radius_card_pt": 24}}
    check("путь в базе читается", dig(tok, "tap_target.min_pt") == 44)
    check("отсутствующий путь не роняет орган",
          dig(tok, "tap_target.nope") is None and dig(tok, "no.such") is None)
    check("нечисло значением не считается",
          dig({"a": {"b": "текст"}}, "a.b") is None)

    TAP = r"\b(tap|touch|tappable)\b"

    agree = [({"fw": "human-interface-guidelines", "id": "/design/hig/layout",
               "law": "Controls must be at least 44 pt to accommodate touch."}, 9.0)]
    check("свод назвал то же число → ПОДТВЕРЖДЕНО",
          verdict(44.0, agree, TAP, "pt", 0.0)[0] == "ПОДТВЕРЖДЕНО")

    check("другое число по тому же свойству → ПРОТИВОРЕЧИЕ",
          verdict(32.0, agree, TAP, "pt", 0.0)[0] == "ПРОТИВОРЕЧИЕ")

    silent = [({"fw": "human-interface-guidelines", "id": "/design/hig/a",
                "law": "Make sure controls are easy to tap."}, 9.0)]
    check("предписание о свойстве без числа → СОГЛАСОВАНО",
          verdict(44.0, silent, TAP, "pt", 0.0)[0] == "СОГЛАСОВАНО")
    check("свод молчит вовсе → НЕМО", verdict(44.0, [], TAP, "pt", 0.0)[0] == "НЕМО")

    off = [({"fw": "human-interface-guidelines", "id": "/design/hig/tb",
             "law": "Prefer a tab bar for navigation."}, 15.0)]
    check("общая лексика без якоря свойства — НЕ согласие, а молчание",
          verdict(62.0, off, r"\btab bar\b(?=.*\bheight\b)", "pt", 0.0)[0]
          == "НЕМО")

    api = [({"fw": "uikit", "id": "/documentation/uikit/m",
             "law": "The property contains the edge inset values for margins."}, 12.0)]
    check("описание устройства API согласия не даёт: не предписание",
          verdict(16.0, api, r"\b(margin|inset)\b", "pt", 0.0)[0] == "НЕМО")

    mixed = [({"fw": "uikit", "id": "/documentation/uikit/m",
               "law": "The property contains the edge inset values for margins."}, 12.0),
             ({"fw": "human-interface-guidelines", "id": "/design/hig/lm",
               "law": "Make sure content respects the layout margins."}, 9.0)]
    check("якорь держит множественное число нормы",
          anchored({"law": "respects the layout margins"}, r"\b(margin|inset)\b"))
    api_norm = [({"fw": "uikit", "id": "/documentation/uikit/d",
                  "law": "The minimum duration of the long press."}, 12.0)]
    check("предписание ИЗ СПРАВОЧНИКА согласия не даёт: свод молчит",
          verdict(120.0, api_norm, r"\bpress\b", "ms", 0.0)[0] == "НЕМО")
    check("свидетелем становится предписание, а не первый по счёту",
          verdict(16.0, mixed, r"\b(margin|inset)\b", "pt", 0.0)[1]["id"]
          == "/design/hig/lm")

    wrong_unit = [({"fw": "human-interface-guidelines", "id": "/design/hig/u",
                    "law": "Make sure to wait at least 44 ms before retrying "
                           "the touch."}, 9.0)]
    check("совпадение цифр в ЧУЖОЙ единице свидетельством не считается",
          verdict(44.0, wrong_unit, TAP, "pt", 0.0)[0] == "СОГЛАСОВАНО")

    pair = [({"fw": "human-interface-guidelines", "id": "/design/hig/b",
              "law": "For touch, use 28 pt for menus and 44 pt for frequent controls."}, 9.0)]
    check("совпадение ищется среди ВСЕХ чисел нормы, не только первого",
          verdict(44.0, pair, TAP, "pt", 0.0)[0] == "ПОДТВЕРЖДЕНО")
    check("свидетельствует СОВПАВШЕЕ число, а не первое в норме",
          verdict(28.0, pair, TAP, "pt", 0.0)[2] == 28.0)

    ratio = [({"fw": "human-interface-guidelines", "id": "/design/hig/dm",
               "law": "Keep the contrast ratio no lower than 4.5:1."}, 9.0)]
    check("допуск работает: 4.5 против 4.5 при tol 0.05",
          verdict(4.5, ratio, r"\bcontrast\b", ":1", 0.05)[0] == "ПОДТВЕРЖДЕНО")
    check("допуск не растягивается: 7.0 против 4.5 — расхождение",
          verdict(7.0, ratio, r"\bcontrast\b", ":1", 0.05)[0] == "ПРОТИВОРЕЧИЕ")

    rows = attest({"tap_target": {"min_pt": 44}},
                  [{"fw": "human-interface-guidelines", "id": "/design/hig/l",
                    "law": "Controls must be at least 44 pt to accommodate touch."}],
                  only="tap_target.min_pt")
    check("сшивка целиком: один предмет, вердикт с адресом",
          len(rows) == 1 and rows[0]["verdict"] == "ПОДТВЕРЖДЕНО"
          and rows[0]["id"] == "/design/hig/l")

    rows2 = attest({}, [], only="tap_target.min_pt")
    check("нет замера — так и сказано, а не выдумано",
          rows2[0]["verdict"] == "НЕТ ЗАМЕРА")

    check("свод рисуется и несёт счёт", "## Счёт" in render(rows))

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--only", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--court", action="store_true")
    ap.add_argument("--tokens", default="",
                    help="иная база: например registry/standards/ios27/tokens.next.json")
    a = ap.parse_args()

    if a.court:
        return court()

    global TOKENS
    if a.tokens:
        TOKENS = Path(a.tokens) if Path(a.tokens).is_absolute() else ROOT / a.tokens
    if not TOKENS.exists():
        print("Измеренная база недоступна:", TOKENS, file=sys.stderr)
        return 1
    tokens = json.loads(TOKENS.read_text(encoding="utf-8"))
    records = law_mod.load()
    if not records:
        print("Библиотека пуста:", law_mod.LIBRARY, file=sys.stderr)
        return 1

    rows = attest(tokens, records, a.only)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    text = render(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    for r in rows:
        m = "—" if r["measured"] is None else f"{r['measured']} {r['unit']}"
        print(f"  {r['verdict']:14s} {r['path']:44s} замер {m}")
    print("записано:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
