#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ГРАДУИРОВКА БИБЛИОТЕКИ · честная мера того, чем департамент владеет.

Родословная (02.08.2026): библиотека объявляла 30 125 «законов». Замер показал,
что число с единицей несут 173 строки, число вместе с модальностью — 28, а
числовых дизайн-норм с адресом — 27. Остальное есть выжимка прозы из
туториалов и справочника API: «On iPad, people can use this sample…» законом
не является ни в каком смысле.

Это прямое нарушение ЗКН-Э001: правдоподобное хуже отсутствующего. Число
«30 125» правдоподобно и потому вреднее честного «27» — оно создаёт у
владельца ложную картину силы инструмента.

Орган не удаляет добытое. Он его РАЗМЕЧАЕТ, чтобы никто — включая департамент —
не принимал пересказ за норму.

Ступени:
  СВЯЗЫВАЕМАЯ — число + единица + дизайн-предмет + адрес. Кандидат в правило.
  ЧИСЛОВАЯ    — число + единица + адрес, предмет вне мандата.
  НОРМАТИВНАЯ — модальность без числа. Проверке машиной не поддаётся.
  ПРОЗА       — пересказ, пример, описание образца.
  БЕЗАДРЕСНАЯ — адреса нет. В библиотеке законов находиться не имеет права.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "registry" / "library"

NUM = re.compile(r"\b(\d+(?:\.\d+)?)\s?(pt|points?|px|pixels?|ms|%|dp)\b", re.I)
MODAL = re.compile(
    r"\b(must|should|always|never|don't|do not|avoid|ensure|prefer|require[sd]?|"
    r"at least|no more than|minimum|maximum|need to)\b", re.I)
DESIGN = re.compile(
    r"\b(margin|padding|spacing|corner|radius|size|width|height|tap target|touch|"
    r"font|text|weight|opacity|blur|duration|animation|contrast|ratio|inset|icon|"
    r"thumbnail|glyph|stroke|shadow|glow|tint)\b", re.I)
NARRATIVE = re.compile(
    r"\b(for example|this sample|in this tutorial|tapping|you can|people can|"
    r"the sample|for instance|shown in|the following|learn more)\b", re.I)

BINDABLE, NUMERIC, NORMATIVE, PROSE, NOADDR, CHROME = (
    "СВЯЗЫВАЕМАЯ", "ЧИСЛОВАЯ", "НОРМАТИВНАЯ", "ПРОЗА", "БЕЗАДРЕСНАЯ", "ОБВЯЗКА")

# Обвязка страницы: куки-баннеры, навигация, кнопки. Прошла извлечение и села
# в библиотеку законов. Не норма, не проза — мусор обходчика, и он опаснее
# прозы: он выглядит как текст источника и раздувает счёт.
CHROME_RX = re.compile(
    r"(consent to all cookies|cookie settings|modify cookie|visit page|learn more|"
    r"subscribe|newsletter|all rights reserved|privacy policy|terms of use|"
    r"skip to (main )?content|share this|follow us|sign in|log in|"
    r"to view this video|accept all|manage preferences)", re.I)


def grade_line(text: str, address: str) -> str:
    if not address:
        return NOADDR
    if CHROME_RX.search(text):
        return CHROME
    has_num = bool(NUM.search(text))
    has_design = bool(DESIGN.search(text))
    if has_num and has_design:
        return BINDABLE
    if has_num:
        return NUMERIC
    if MODAL.search(text) and not NARRATIVE.search(text):
        return NORMATIVE
    return PROSE


def grade_library(lib: Path = LIB) -> dict:
    tally = Counter()
    by_fw: dict[str, Counter] = {}
    bindable: list[dict] = []
    homeless: dict[str, int] = Counter()
    chrome: dict[str, int] = Counter()

    for f in sorted(lib.glob("*.jsonl")):
        fw = f.stem
        by_fw[fw] = Counter()
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = d.get("law") or d.get("text") or ""
            addr = d.get("id") or d.get("url") or d.get("address") or d.get("at") or ""
            if not text:
                continue
            g = grade_line(text, addr)
            tally[g] += 1
            by_fw[fw][g] += 1
            if g == NOADDR:
                homeless[fw] += 1
            elif g == CHROME:
                chrome[fw] += 1
            elif g == BINDABLE:
                bindable.append({"framework": fw, "address": addr, "law": text.strip()})

    total = sum(tally.values())
    return {
        "всего_строк": total,
        "ступени": dict(tally),
        "доля_связываемых": round(tally[BINDABLE] / total, 5) if total else 0,
        "безадресные_по_фреймворкам": dict(homeless),
        "обвязка_по_фреймворкам": dict(chrome),
        "связываемые": bindable,
        "по_фреймворкам": {k: dict(v) for k, v in by_fw.items()},
    }


def render(r: dict) -> str:
    t = r["ступени"]
    n = r["всего_строк"]
    out = ["# ГРАДУИРОВКА БИБЛИОТЕКИ",
           "",
           "Честная мера того, чем департамент владеет. Число «строк в библиотеке» "
           "не есть число законов: правдоподобное хуже отсутствующего (ЗКН-Э001).",
           "",
           f"| ступень | строк | доля |", "|---|---|---|"]
    for k in (BINDABLE, NUMERIC, NORMATIVE, PROSE, CHROME, NOADDR):
        v = t.get(k, 0)
        out.append(f"| {k} | {v} | {v / n:.1%} |" if n else f"| {k} | {v} | — |")
    out += ["", f"**Связываемых в правило: {t.get(BINDABLE, 0)} из {n}.** "
                f"Это и есть настоящий надзорный запас библиотеки.", ""]
    ch = r.get("обвязка_по_фреймворкам") or {}
    if ch:
        out += ["## Обвязка страницы — мусор обходчика", "",
                "Куки-баннеры, навигация и кнопки, прошедшие извлечение. "
                "Опаснее прозы: выглядит как текст источника и раздувает счёт.", ""]
        for k, v in sorted(ch.items(), key=lambda x: -x[1]):
            out.append(f"- `{k}` — {v}")
        out.append("")
    if r["безадресные_по_фреймворкам"]:
        out += ["## Безадресные — нарушение ЗКН-Э002", "",
                "Строка без адреса не существует. Этим файлам в библиотеке "
                "законов места нет:", ""]
        for k, v in sorted(r["безадресные_по_фреймворкам"].items(), key=lambda x: -x[1]):
            out.append(f"- `{k}` — {v}")
        out.append("")
    out += ["## Связываемые нормы", ""]
    for b in r["связываемые"]:
        out.append(f"- `{b['address']}`  \n  {b['law'][:200]}")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    r = grade_library()
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    out = LIB / "GRADE.md"
    out.write_text(render(r), encoding="utf-8")
    t = r["ступени"]
    print(f"строк: {r['всего_строк']}")
    for k in (BINDABLE, NUMERIC, NORMATIVE, PROSE, CHROME, NOADDR):
        print(f"  {k:14} {t.get(k, 0)}")
    print(f"связываемых в правило: {t.get(BINDABLE, 0)} → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
