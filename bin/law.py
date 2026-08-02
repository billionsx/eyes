#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ДОЗНАНИЕ. Поиск по библиотеке законов (registry/library/*.jsonl).

Зачем орган. В библиотеке 30 125 законов по 336 фреймворкам, и до сих пор
не было способа спросить у неё что-либо. Библиотека, которую нельзя
опросить, юридически мертва: закон, который не находится, не применяется.
Департамент, который не может процитировать свою норму под конкретный
вопрос клиента, — не департамент, а склад.

Механика — BM25 (k1=1.5, b=0.75) поверх текста закона, без единой внешней
зависимости, как и весь департамент. Индекс строится в памяти на прогон:
30k коротких документов — доли секунды, кэш на диск не нужен и не заводится
(лишний артефакт = лишняя рассинхронизация).

Три вещи, отличающие дознание от обычного поиска:

  1. АДРЕС НЕОТДЕЛИМ (ЗКН-Э002). Закон никогда не возвращается голым
     предложением: всегда `law` + `id` (адрес страницы Apple). Процитировать
     без адреса нельзя технически — поля неразделимы в выдаче.

  2. ПРИВИЛЕГИЯ СВОДА. HIG — источник норм дизайна; /documentation — это
     справочник API, в котором связываемых числовых норм нет (доказано
     нулевым урожаем добытчика). При равном BM25 закон из human-interface-
     guidelines встаёт выше закона из справочника. Не запрет справочнику —
     порядок, отражающий предмет департамента.

  3. МЕТКА СВЯЗЫВАЕМОСТИ. Каждый найденный закон помечается: несёт ли он
     число И направление ("не более", "at least", "minimum") — то есть
     годен ли он в кандидаты правил. Это прямая подача в bin/propose.py:
     дознание отбирает породу, добытчик плавит.

Приложения:
    python3 bin/law.py "contrast ratio"                 — искать везде
    python3 bin/law.py "touch target" --fw human-interface-guidelines
    python3 bin/law.py "spacing" --bindable             — только связываемые
    python3 bin/law.py "corner radius" -n 20 --json
    python3 bin/law.py --court                          — суд, без сети
"""
import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "registry" / "library"

# Свод норм дизайна. При равном счёте идёт впереди справочника API.
PRIVILEGED = ("human-interface-guidelines", "big7")

MAX_RESULTS = 10

# Слова, которые в норме Apple не несут смысла и только шумят в BM25.
STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "are", "be", "it", "that", "this", "as", "by", "at", "from",
    "your", "you", "can", "if", "when", "their", "its", "they", "not",
}

# Ведущий дефис разрешён: `-apple-system` и `-webkit-*` — это имена, а не
# «слово с мусором». Голый дефис токеном не становится (за ним обязан идти
# буквенно-цифровой знак).
_WORD = re.compile(r"-?[a-z0-9][a-z0-9\-\.]*")
_NUM = re.compile(r"\b\d+(?:\.\d+)?\s*(?:pt|px|dp|sp|%|:1|ms|s\b)?")
# Направление нормы: без него число — это факт, а не правило.
_DIR = re.compile(
    r"\b(at least|no less|no more|no smaller|no larger|minimum|maximum|"
    r"min\.|max\.|must|should|never|always|avoid|don't|do not|"
    r"не менее|не более|обязан|запрещ)",
    re.I,
)


def _fold(w):
    """Хвостовая пунктуация и множественное число.

    Точка и дефис нужны ВНУТРИ токена (`0.4`, `-apple-system`), но на конце
    они — знак предложения: без срезки `touch.` не встречается с `touch`.

    Множественное — только безопасная форма: слово длиннее трёх знаков,
    кончается на -s и не на -ss/-us/-is. Иначе фолд съедает смысл
    (`less` → `les`, `status` → `statu`, `axis` → `axi`). `controls` →
    `control`, `targets` → `target`, `colors` → `color` — это то, ради
    чего фолд и заводится: норма пишется во множественном, спрашивают
    в единственном.
    """
    w = w.rstrip(".-")
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        w = w[:-1]
    return w


def tokenize(text):
    """Слова в нижнем регистре без стоп-слов. Дефис и точка живут внутри
    токена: `-apple-system` и `0.4` — это одно слово, а не три."""
    out = []
    for raw in _WORD.findall(text.lower()):
        w = _fold(raw)
        if w and w not in STOP:
            out.append(w)
    return out


def is_bindable(law):
    """Закон связываем, если несёт И число, И направление. Одно число без
    направления — описание ('the default is 17pt'), не норма."""
    return bool(_NUM.search(law)) and bool(_DIR.search(law))


class BM25:
    """BM25 без зависимостей. k1 — насыщение по частоте, b — поправка на
    длину документа. Значения канонические, не подбирались под выдачу."""

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.idf = {}
        self.docs = []
        self.lens = []
        self.avgdl = 0.0
        self.N = 0

    def fit(self, tokenized):
        self.docs = [Counter(t) for t in tokenized]
        self.lens = [len(t) for t in tokenized]
        self.N = len(tokenized)
        self.avgdl = (sum(self.lens) / self.N) if self.N else 0.0
        df = Counter()
        for t in tokenized:
            df.update(set(t))
        for word, freq in df.items():
            self.idf[word] = math.log((self.N - freq + 0.5) / (freq + 0.5) + 1)
        return self

    def score(self, query_tokens, i):
        if not self.lens[i]:
            return 0.0
        doc = self.docs[i]
        dl = self.lens[i]
        s = 0.0
        for tok in query_tokens:
            idf = self.idf.get(tok)
            if idf is None:
                continue
            tf = doc.get(tok, 0)
            if not tf:
                continue
            s += idf * (tf * (self.k1 + 1)) / (
                tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            )
        return s


def load(frameworks=None):
    """Читает библиотеку. Возвращает список записей {fw, id, law}.
    Битые строки пропускаются молча: библиотека пополняется атласом, одна
    испорченная строка не имеет права ронять дознание."""
    out = []
    if not LIBRARY.exists():
        return out
    for path in sorted(LIBRARY.glob("*.jsonl")):
        fw = path.stem
        if frameworks and fw not in frameworks:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            law = d.get("law")
            if not law:
                continue
            out.append({"fw": fw, "id": d.get("id", ""), "law": law})
    return out


def rank(records, query, max_results=MAX_RESULTS, bindable_only=False):
    """Возвращает [(запись, счёт)] по убыванию. Привилегия свода —
    доплата к счёту, а не подмена порядка: сильный закон из справочника
    по-прежнему обходит слабый закон из HIG."""
    if bindable_only:
        records = [r for r in records if is_bindable(r["law"])]
    if not records:
        return []
    qt = tokenize(query)
    if not qt:
        return []
    bm = BM25().fit([tokenize(r["law"]) for r in records])
    scored = []
    for i, rec in enumerate(records):
        s = bm.score(qt, i)
        if s <= 0:
            continue
        if rec["fw"] in PRIVILEGED:
            s *= 1.15
        scored.append((rec, s))
    scored.sort(key=lambda x: (-x[1], x[0]["fw"], x[0]["id"]))

    # Атлас ходит по адресам, различающимся регистром (/SwiftUI/ и /swiftui/),
    # и один и тот же закон лежит в библиотеке дважды. Цитировать норму
    # дважды — расписаться в том, что департамент не знает своей библиотеки.
    # Оставляем первое вхождение: сортировка уже подняла привилегированный
    # свод и лексикографически меньший адрес.
    seen = set()
    unique = []
    for rec, s in scored:
        key = " ".join(rec["law"].lower().split())
        if key in seen:
            continue
        seen.add(key)
        unique.append((rec, s))
    return unique[:max_results]


def report(scored):
    if not scored:
        print("НИЧЕГО. Закона под такой запрос в библиотеке нет — "
              "это ответ, а не сбой: департамент не выдумывает норм.")
        return 1
    for i, (rec, s) in enumerate(scored, 1):
        mark = "СВЯЗЫВАЕМ" if is_bindable(rec["law"]) else "описание"
        print(f"\n{i}. [{rec['fw']}] счёт {s:.2f} · {mark}")
        print(f"   {rec['law']}")
        print(f"   адрес: {rec['id']}")
    print(f"\nнайдено: {len(scored)}")
    return 0


def court():
    """Суд органа. Сеть и живая библиотека не нужны: породу кладём сами."""
    ok = True

    def check(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    print("СУД · дознание по библиотеке законов")

    check("стоп-слова выброшены, значимые оставлены",
          tokenize("The contrast ratio of the text") == ["contrast", "ratio", "text"])
    check("дефисный токен не рвётся на части",
          "-apple-system" in tokenize("Use -apple-system first"))
    check("десятичное число — один токен",
          "0.4" in tokenize("letter-spacing 0.4 px"))
    check("точка конца предложения не приклеивается к слову",
          tokenize("accommodate touch.") == ["accommodate", "touch"])
    check("множественное встречается с единственным",
          tokenize("Controls and targets") == ["control", "target"])
    check("фолд не съедает смысл: less/status/axis целы",
          tokenize("less status axis") == ["less", "status", "axis"])
    check("короткое слово на -s не режется",
          "gas" in tokenize("gas"))

    check("число + направление = связываемый закон",
          is_bindable("Touch targets must be at least 44pt."))
    check("число без направления — описание, не норма",
          not is_bindable("The default body size is 17pt."))
    check("направление без числа — не связывается",
          not is_bindable("You should design with clarity."))

    # Формулировки намеренно разные: одна норма, но два независимых
    # источника. Схлопывание близнецов не должно их путать.
    lib = [
        {"fw": "uikit", "id": "/documentation/uikit/x",
         "law": "Touch targets must be at least 44pt across."},
        {"fw": "human-interface-guidelines", "id": "/design/hig/layout",
         "law": "Touch targets must be at least 44pt in each dimension."},
        {"fw": "metal", "id": "/documentation/metal/y",
         "law": "Encode render commands into a command buffer."},
    ]

    r = rank(lib, "touch target 44pt")
    check("найдено ровно то, что про предмет запроса", len(r) == 2)
    check("при равном счёте свод впереди справочника",
          r and r[0][0]["fw"] == "human-interface-guidelines")
    check("посторонний фреймворк в выдачу не попал",
          all(x[0]["fw"] != "metal" for x in r))

    check("адрес неотделим от закона",
          all(x[0]["id"] and x[0]["law"] for x in r))

    strong = lib + [{"fw": "human-interface-guidelines", "id": "/design/hig/z",
                     "law": "Color conveys meaning."}]
    r2 = rank(strong, "touch target 44pt")
    check("привилегия не подменяет порядок: слабый закон свода не всплыл",
          r2[0][0]["law"].startswith("Touch targets"))

    r3 = rank(lib, "command buffer", bindable_only=True)
    check("фильтр связываемости отсекает описания", r3 == [])

    twins = [
        {"fw": "swiftui", "id": "/documentation/SwiftUI/Scene",
         "law": "This preserves legibility for text and controls."},
        {"fw": "swiftui", "id": "/documentation/swiftui/scene",
         "law": "this  preserves LEGIBILITY for text and controls."},
    ]
    r4 = rank(twins, "legibility text controls")
    check("закон-близнец из адреса-двойника цитируется один раз", len(r4) == 1)

    r5 = rank(twins + [{"fw": "uikit", "id": "/documentation/uikit/q",
                        "law": "Legibility depends on text size."}],
              "legibility text")
    check("схлопывание не съедает разные законы", len(r5) == 2)

    check("пустой запрос не ломает орган", rank(lib, "   ") == [])
    check("пустая библиотека не ломает орган", rank([], "anything") == [])

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--fw", action="append", default=None,
                    help="ограничить фреймворком (можно повторять)")
    ap.add_argument("-n", type=int, default=MAX_RESULTS)
    ap.add_argument("--bindable", action="store_true",
                    help="только законы, годные в кандидаты правил")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()

    if a.court:
        return court()
    if not a.query:
        ap.print_help()
        return 2

    records = load(set(a.fw) if a.fw else None)
    if not records:
        print("Библиотека пуста или недоступна:", LIBRARY, file=sys.stderr)
        return 1
    scored = rank(records, a.query, a.n, a.bindable)

    if a.json:
        print(json.dumps(
            [{"fw": r["fw"], "id": r["id"], "law": r["law"],
              "score": round(s, 4), "bindable": is_bindable(r["law"])}
             for r, s in scored], ensure_ascii=False, indent=2))
        return 0 if scored else 1
    return report(scored)


if __name__ == "__main__":
    sys.exit(main())
