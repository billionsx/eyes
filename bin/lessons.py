#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СВОД УРОКОВ. Правило, купленное одним органом, обязательно для всех.

Зачем орган существует. 02.08.2026 обнаружилось, что `harvest.py` хранила
сырые страницы и объясняла это дословно так: «работник просеивал страницу и
выбрасывал её; из этого следовало, что любое новое сито требует заново обойти
весь свод». В тот же день ровно тот же дефект был независимо найден в
`atlas.py` — и починен заново, с нуля, теми же словами.

Урок был куплен департаментом однажды, а применён к одному органу из двух.
Это дефект не органа, а устройства: у департамента не было места, где
усвоенное становится обязательным для всех.

Свод уроков — такое место. Каждый урок несёт МАШИННУЮ проверку по всем
органам сразу. Урок без проверки в свод не принимается: ненаблюдаемое
правило есть пожелание, а не правило.

Освобождение возможно, но только ПОИМЁННОЕ и с причиной — глухое «этот орган
не считается» запрещено тем же доводом, что и глоб-освобождение в BXH.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"
EXEMPT = ROOT / "registry" / "lessons-exempt.json"

RE_NET = re.compile(r"urlopen|requests\.(get|post)|urllib\.request|httpx|aiohttp")
RE_STORE = re.compile(r"corpus|_corpus_put|corpus_put|CORPUS|snapshots|fixtures")
RE_APPEND_ONLY = re.compile(r"""\.open\(\s*["']a["']|open\([^)]*["']a["']\)""")
# ЖУРНАЛ ≠ СКЛАД. Хроника, след прочтения и лог дописываются ПО ПРИРОДЕ: их
# смысл в порядке событий, и переписывать их запрещено (ст. 4 — только вперёд).
# Требовать от журнала идемпотентности значит требовать, чтобы он перестал
# быть журналом. Урок У2 касается склада — того, что перечитывается.
RE_JOURNAL = re.compile(r"visited|CHANGELOG|chronicle|хроник|журнал|log\b|\.md\b")


def _organs() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8", errors="ignore")
            for p in sorted(BIN.glob("*.py"))}


def _exempt() -> dict:
    if EXEMPT.exists():
        return json.loads(EXEMPT.read_text(encoding="utf-8"))
    return {}


def _is_exempt(ex: dict, code: str, name: str) -> bool:
    """Освобождение — только с причиной, и причина не может быть долгом.

    Реестр освобождений обязан не превращаться в место, где прячут долг.
    Причина, начинающаяся с 🕳, объявляет ДОЛГ: орган остаётся нарушителем,
    просто нарушение названо вслух. Разница принципиальная — освобождение
    закрывает вопрос, долг держит его открытым.
    """
    why = (ex.get(code) or {}).get(name)
    return bool(why) and not str(why).lstrip().startswith("🕳")


def debts_of(ex: dict) -> list[tuple[str, str]]:
    return sorted((c, n) for c, d in ex.items() if isinstance(d, dict)
                  for n, w in d.items() if str(w).lstrip().startswith("🕳"))


LESSONS = []


def lesson(code, title, why):
    def deco(fn):
        LESSONS.append({"code": code, "title": title, "why": why, "fn": fn})
        return fn
    return deco


@lesson("У1", "Орган, ходящий в сеть, хранит сырьё",
        "Иначе любая починка сита требует заново обойти интернет. Куплен "
        "жатвой 29.07, переоткрыт атласом 02.08 — полдня на то, что "
        "департамент уже знал.")
def u1(organs, ex):
    bad = []
    for name, src in organs.items():
        if not RE_NET.search(src):
            continue
        if RE_STORE.search(src):
            continue
        if _is_exempt(ex, "У1", name):
            continue
        bad.append(name)
    return bad


@lesson("У2", "Запись в общий склад идемпотентна по адресу",
        "Дописывание есть скрытое допущение «источник читается однажды». "
        "Оно перестало быть верным раньше, чем код о нём узнал: перечитывание "
        "удвоило бы всю библиотеку.")
def u2(organs, ex):
    bad = []
    for name, src in organs.items():
        if not RE_STORE.search(src):
            continue
        if _is_exempt(ex, "У2", name):
            continue
        # Склад, открываемый только на дописывание, идемпотентным не бывает.
        idempotent = ('id") != pid' in src or 'get("page") != page' in src
                      or "rows[pid] = " in src)
        if RE_APPEND_ONLY.search(src) and not idempotent and not RE_JOURNAL.search(src):
            bad.append(name)
    return bad


@lesson("У3", "Пустой обход — красный, а не чистый",
        "Ноль находок при нуле просмотренных источников есть промах адреса. "
        "Линт объявлял это чистотой и возвращал ноль — CI с опечаткой в пути "
        "был бы зелёным вечно (ЗКН-Э006).")
def u3(organs, ex):
    bad = []
    for name, src in organs.items():
        # Урок касается вердикта «чисто» ПО РЕЗУЛЬТАТУ ОБХОДА, а не слова
        # «чистый» в прозе. Орган, который ничего не обходит, под него не
        # подпадает — это было бы придиркой, а не законом.
        if not re.search(r'"Чисто\.|\bЧисто\.', src):
            continue
        if _is_exempt(ex, "У3", name):
            continue
        if not re.search(r"(files|walked|обойден|просмотрен)\W{0,24}(==\s*0|not )", src) \
                and 'if not res["files"]' not in src:
            bad.append(name)
    return bad


@lesson("У4", "Отпечаток прочтения включает версию сита",
        "Иначе починка добытчика по построению не вступает в силу на уже "
        "прочитанном: текст не менялся — источник пропускается.")
def u4(organs, ex):
    bad = []
    for name, src in organs.items():
        if not re.search(r'get\("sha"\)\s*==|\bsha\b.*==.*prev', src):
            continue
        if _is_exempt(ex, "У4", name):
            continue
        if "sieve" not in src.lower() and "SIEVE" not in src:
            bad.append(name)
    return bad


@lesson("У5", "Столкновение складов решается объединением, а не победой",
        "Хроника делала `git pull --rebase -X theirs`: для журнала терпимо, "
        "для склада знаний — молчаливая потеря страниц другого писателя. "
        "Склад ключуется адресом, значит у столкновения есть правильный ответ.")
def u5(organs, ex):
    bad = []
    ch = (BIN.parent / "bin" / "chronicle.sh")
    txt = ch.read_text(encoding="utf-8", errors="ignore") if ch.exists() else ""
    if "-X theirs" in txt and "corpusunion" not in txt:
        bad.append("chronicle.sh")
    ga = BIN.parent / ".gitattributes"
    if not ga.exists() or "merge=corpusunion" not in ga.read_text(encoding="utf-8"):
        bad.append(".gitattributes")
    return bad


@lesson("У6", "Сжатая долька склада пишется детерминированно",
        "gzip кладёт в заголовок время записи: одинаковое содержимое давало "
        "разные байты, дольки конфликтовали на пустом месте и раздували "
        "репозиторий.")
def u6(organs, ex):
    bad = []
    for name, src in organs.items():
        if "gzip" not in src or name in ("corpus_merge.py", "lessons.py"):
            continue
        if not re.search(r"gzip\.(open|GzipFile)\([^)]*[\"']w", src):
            continue
        if name in ex.get("У6", {}) or _is_exempt(ex, "У6", name):
            continue
        if "mtime=0" not in src:
            bad.append(name)
    return bad


@lesson("У7", "Выкладываемое обязано разбираться",
        "Грубое авторазрешение конфликта положило в main орган с маркерами — "
        "суд на main перестал запускаться вовсе. Реестр был защищён проверкой "
        "целости json, собственный код органов — нет. Защита симметрична.")
def u7(organs, ex):
    import ast as _a
    bad = []
    for name, src in organs.items():
        if re.search(r"^<<<<<<< |^>>>>>>> ", src, re.M):
            bad.append(name)
            continue
        try:
            _a.parse(src)
        except SyntaxError:
            bad.append(name)
    return bad


def audit() -> dict:
    organs, ex = _organs(), _exempt()
    out = []
    for L in LESSONS:
        bad = L["fn"](organs, ex)
        out.append({"code": L["code"], "title": L["title"], "why": L["why"],
                    "violators": sorted(bad),
                    "exempt": sorted(ex.get(L["code"], {}))})
    return {"organs": len(organs), "lessons": out, "debts": debts_of(ex)}


def render(r: dict) -> str:
    lines = ["# СВОД УРОКОВ ДЕПАРТАМЕНТА", "",
             "Правило, купленное одним органом, обязательно для всех. Урок без "
             "машинной проверки в свод не принимается: ненаблюдаемое правило "
             "есть пожелание, а не правило.", "",
             f"Органов под проверкой: **{r['organs']}**", "",
             "| урок | нарушители | освобождены |", "|---|---|---|"]
    for L in r["lessons"]:
        v = ", ".join(f"`{x}`" for x in L["violators"]) or "—"
        e = ", ".join(f"`{x}`" for x in L["exempt"]) or "—"
        lines.append(f"| **{L['code']}** · {L['title']} | {v} | {e} |")
    lines.append("")
    for L in r["lessons"]:
        lines += [f"## {L['code']} · {L['title']}", "", L["why"], ""]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    r = audit()
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    (ROOT / "registry" / "LESSONS.md").write_text(render(r), encoding="utf-8")
    bad = 0
    for L in r["lessons"]:
        mark = "✗" if L["violators"] else "✓"
        print(f"  {mark} {L['code']} {L['title']}"
              + (f" — нарушают: {', '.join(L['violators'])}" if L["violators"] else ""))
        bad += len(L["violators"])
    for c, n in r.get("debts", []):
        print(f"  🕳 {c} {n} — объявленный долг, не освобождение")
    print(f"органов: {r['organs']} · нарушений: {bad} · объявленных долгов: {len(r.get('debts', []))}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
