#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СИМВОЛЫ. Поиск по перечню системных глифов Apple.

Родословная. У департамента лежат 9184 имени SF Symbols, снятые
macOS-плечом с настоящего `SF Symbols.app` (`name_availability.plist`) —
первоисточник, точнее которого не бывает: это тот самый файл, по которому
имена резолвит система.

И они лежали мёртвым грузом. Перечень, который нельзя спросить, не
применяется: разработчик, рисующий свою лупу, не узнает, что системная
называется `magnifyingglass`, — не потому что не хотел, а потому что
спросить было негде.

Почему это орган ПОДСКАЗКИ, а не правило. Упрекать за «нарисовал свою
иконку вместо системной» департамент не станет: определить по SVG, что он
означает лупу, можно только догадкой, а догадка в приговоре недопустима.
Зато на прямой вопрос «есть ли системный глиф для поиска» ответ точен и
проверяем. Инструмент предъявляет норму, решение остаётся человеку (ст. 7.4).

Устройство поиска. Имена Apple точечные: `arrow.left.circle.fill`. Ищем по
частям имени, а не по подстроке: запрос `circle` не должен вытаскивать
`semicircle`. Убранства (`.fill`, `.circle`, `.square`) и языковые варианты
(`.ar`, `.hi`, `.he`) опускаются в выдаче: спрашивают обычно базовый глиф.

СЛОВАРЬ ВЕБА объявлен и мал. Веб называет вещи не так, как Apple: `search`
против `magnifyingglass`, `trash` против `trash`, `close` против `xmark`.
Список закрытый — угаданный синоним однажды посоветует не тот глиф, а
подсказка департамента обязана быть точной, иначе ей перестанут верить.

Приложения:
    python3 bin/symbols.py search        — найти системный глиф
    python3 bin/symbols.py "arrow left" -n 8
    python3 bin/symbols.py --court
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = ROOT / "registry" / "standards" / "symbols" / "sf-symbols-names.json"

# Языковые варианты имени: тот же глиф для другой письменности. В ответ на
# общий вопрос они шум.
SCRIPTS = ("ar", "hi", "he", "th", "ja", "ko", "zh", "my", "km", "ta", "te",
           "kn", "ml", "gu", "or", "pa", "si", "bn", "sat", "gurmukhi",
           "devanagari", "arabic", "hebrew", "thai", "chinese", "japanese",
           "korean")
# Убранства: вариации базового глифа.
TRIM = ("fill", "circle", "square", "rectangle", "slash", "badge", "inverse")

# СЛОВАРЬ ВЕБА → части имени Apple. Объявлен, не выведен.
WEB = {
    "search": ["magnifyingglass"],
    "close": ["xmark"], "cross": ["xmark"], "x": ["xmark"],
    "check": ["checkmark"], "tick": ["checkmark"], "done": ["checkmark"],
    "menu": ["line", "3", "horizontal"], "hamburger": ["line", "3", "horizontal"],
    "settings": ["gearshape"], "gear": ["gearshape"], "cog": ["gearshape"],
    "user": ["person"], "profile": ["person"], "account": ["person"],
    "home": ["house"], "delete": ["trash"], "remove": ["trash"],
    "edit": ["pencil"], "write": ["pencil"], "pen": ["pencil"],
    "add": ["plus"], "new": ["plus"], "minus": ["minus"],
    "back": ["chevron", "left"], "forward": ["chevron", "right"],
    "next": ["chevron", "right"], "prev": ["chevron", "left"],
    "up": ["chevron", "up"], "down": ["chevron", "down"],
    "share": ["square", "and", "arrow", "up"],
    "favorite": ["heart"], "like": ["heart"], "star": ["star"],
    "bookmark": ["bookmark"], "save": ["bookmark"],
    "notification": ["bell"], "alert": ["bell"], "bell": ["bell"],
    "calendar": ["calendar"], "clock": ["clock"], "time": ["clock"],
    "image": ["photo"], "picture": ["photo"], "photo": ["photo"],
    "video": ["video"], "camera": ["camera"], "mic": ["mic"],
    "play": ["play"], "pause": ["pause"], "stop": ["stop"],
    "volume": ["speaker", "wave"], "mute": ["speaker", "slash"],
    "download": ["arrow", "down"], "upload": ["arrow", "up"],
    "refresh": ["arrow", "clockwise"], "reload": ["arrow", "clockwise"],
    "link": ["link"], "attach": ["paperclip"], "file": ["doc"],
    "folder": ["folder"], "mail": ["envelope"], "email": ["envelope"],
    "message": ["bubble"], "chat": ["bubble"], "comment": ["bubble"],
    "lock": ["lock"], "unlock": ["lock", "open"], "key": ["key"],
    "info": ["info"], "help": ["questionmark"], "warning": ["exclamationmark"],
    "error": ["exclamationmark"], "filter": ["line", "horizontal", "3", "decrease"],
    "sort": ["arrow", "up", "arrow", "down"], "more": ["ellipsis"],
    "location": ["location"], "map": ["map"], "pin": ["mappin"],
    "cart": ["cart"], "basket": ["basket"], "tag": ["tag"],
    "eye": ["eye"], "hide": ["eye", "slash"], "print": ["printer"],
    "copy": ["doc", "on", "doc"], "paste": ["clipboard"],
}


def load(path=None):
    p = Path(path) if path else NAMES
    if not p.exists():
        return [], ""
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return [], ""
    return list(d.get("names") or []), str(d.get("at") or "")


def parts(name):
    return [x for x in name.lower().split(".") if x]


def is_localized(name):
    return any(p in SCRIPTS for p in parts(name))


def expand(query):
    """Запрос → части имени Apple. Слова веба переводятся по словарю."""
    out = []
    for w in str(query).lower().replace("-", " ").replace("_", " ").split():
        out.extend(WEB.get(w, [w]))
    seen, uniq = set(), []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def rank(names, query, limit=8):
    """Имена по убыванию пригодности.

    Совпадение считается по ЧАСТЯМ имени, а не по подстроке: иначе запрос
    `circle` вытащит `semicircle`, и подсказка соврёт.
    """
    q = expand(query)
    if not q:
        return []
    scored = []
    for n in names:
        ps = parts(n)
        hit = sum(1 for w in q if w in ps)
        if not hit:
            continue
        s = hit * 10.0
        if ps[:len(q)] == q:
            s += 6                      # имя начинается ровно с запроса
        if len(ps) == len(q) and hit == len(q):
            s += 8                      # точное совпадение целиком
        s -= 0.6 * sum(1 for p in ps if p in TRIM)   # убранства ниже
        s -= 0.4 * (len(ps) - hit)                    # лишние части ниже
        if is_localized(n):
            s -= 12                     # языковой вариант — не общий ответ
        scored.append((n, s))
    scored.sort(key=lambda x: (-x[1], len(x[0]), x[0]))
    return scored[:limit]


def court():
    ok = True

    def chk(n, c):
        nonlocal ok
        ok = ok and bool(c)
        print(f"  {'✓' if c else '✗'} {n}")

    print("СУД · символы (перечень системных глифов Apple)")

    names = ["magnifyingglass", "magnifyingglass.circle.fill",
             "circle", "semicircle", "circle.fill",
             "xmark", "xmark.circle.fill", "xmark.ar",
             "chevron.left", "chevron.left.circle",
             "trash", "trash.fill", "person", "person.crop.circle"]

    chk("слово веба переведено в имя Apple",
        expand("search") == ["magnifyingglass"])
    chk("несловарное слово идёт как есть", expand("trash") == ["trash"])
    chk("составной запрос разбирается",
        expand("back") == ["chevron", "left"])
    chk("дефис и подчёркивание — разделители",
        expand("arrow_left-circle") == ["arrow", "left", "circle"])

    r = [n for n, _ in rank(names, "search")]
    chk("поиск лупы находит системное имя", r[0] == "magnifyingglass")
    chk("убранство ниже базового глифа",
        r.index("magnifyingglass") < r.index("magnifyingglass.circle.fill"))

    r2 = [n for n, _ in rank(names, "circle")]
    chk("совпадение по ЧАСТЯМ: semicircle не вылезает",
        "semicircle" not in r2 and "circle" in r2)

    r3 = [n for n, _ in rank(names, "close")]
    chk("языковой вариант не выдаётся за общий ответ",
        r3[0] == "xmark" and (".ar" not in r3[0]))

    r4 = [n for n, _ in rank(names, "back")]
    chk("составной запрос даёт составное имя", r4[0] == "chevron.left")

    chk("несуществующий предмет — пустая выдача, а не выдумка",
        rank(names, "квазар") == [])
    chk("пустой запрос не роняет орган", rank(names, "   ") == [])
    chk("пустой перечень не роняет орган", rank([], "search") == [])

    chk("языковой вариант опознаётся", is_localized("xmark.ar")
        and not is_localized("xmark"))

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("query", nargs="*", default=[])
    ap.add_argument("-n", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()
    q = " ".join(a.query).strip()
    if not q:
        ap.print_help()
        return 2
    names, at = load()
    if not names:
        print("перечень символов недоступен:", NAMES, file=sys.stderr)
        return 1
    res = rank(names, q, a.n)
    if a.json:
        print(json.dumps({"query": q, "at": at,
                          "symbols": [{"name": n, "score": round(s, 1)}
                                      for n, s in res]},
                         ensure_ascii=False, indent=2))
        return 0 if res else 1
    if not res:
        print("Системного глифа под такой запрос нет — "
              "департамент не выдумывает имён.")
        return 1
    print(f"перечень: {len(names)} глифов · {at}\n")
    for n, s in res:
        print(f"  {n:44s} {s:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
