#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СВЕРКА ОСНОВАНИЙ (ЗКН-Э010).

Зачем орган. 04–05.08.2026 в департаменте нашлись четыре органа, приписавших
клиенту перемену, случившуюся в самом департаменте: храповик долга, реестр
сертификатов, монитор прода, страж App Store. Место разное, ошибка одна,
и потому она стала законом ЗКН-Э010: приговор — только при том же основании.

Но закон исполнялся ВНИМАТЕЛЬНОСТЬЮ. Все четыре случая были найдены глазами,
по одному, в разные часы. Пятый орган, написанный завтра, начнёт с той же
ошибки, и найдётся она так же — случайно и поздно. Способность, зависящая от
чьей-то внимательности, не есть способность департамента (ст. 44).

Что делает орган. Обходит СОХРАНЁННЫЕ СОСТОЯНИЯ — файлы, которые орган пишет
сегодня, чтобы завтра сравнить с ними нынешнее, — и требует машиной:

  1. каждое найденное состояние ОБЪЯВЛЕНО в списке ниже. Новое состояние,
     появившееся без объявления, валит сверку: незамеченное основание и есть
     та самая брешь;
  2. состояние, объявленное ОСНОВАНИЕМ приговора, несёт отпечаток своего
     основания. Нет отпечатка — сравнивать нечем, и приговор невозможен;
  3. состояние, объявленное СВОДКОЙ, отпечатка не требует, но обязано иметь
     названную причину: сводка читается человеком и приговора не выносит.

Долги названы прямо, а не спрятаны: `watch-state.json` сегодня служит
основанием без отпечатка, и это записано долгом со сроком, а не замазано.
Долг, названный вслух, честнее зелёного, купленного молчанием (ЗКН-Э001).

Только stdlib.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Где вообще могут лежать сохранённые состояния. Список нарочно широкий:
# сверка обязана НАХОДИТЬ новое, а не ждать, пока про него вспомнят.
PATTERNS = (
    "registry/state/*.json",
    "registry/live/baseline*.json",
    "registry/atlas/state.json",
    "certificates/*/REGISTER.md",
)

# kind: "основание" — по нему выносится приговор, отпечаток обязателен;
#       "сводка"    — читается человеком, приговора не несёт;
#       "долг"      — служит основанием, отпечатка ПОКА нет, и это названо.
DECLARED = {
    "registry/state/ae-baseline.json": (
        "основание", "sidecar:registry/state/ae-baseline-vision.json",
        "храповик долга: рост приписывается клиенту только при том же "
        "отпечатке зрения (ст. 43.1)"),
    "registry/state/ae-baseline-vision.json": (
        "сводка", None, "сам отпечаток основания, приговора не несёт"),
    "registry/live/baseline.json": (
        "основание", "field:vision",
        "монитор прода: регресс и починка объявляются только при том же "
        "отпечатке (ЗКН-Э010)"),
    "certificates/*/REGISTER.md": (
        "основание", "column:зрение",
        "реестр сертификатов: оценки сравнимы только при равных отпечатках "
        "(ст. 56.2)"),
    "registry/state/watch-state.json": (
        "долг", None,
        "дозор источников Apple: сравнивает заголовки и области страниц с "
        "прошлым снятием и объявляет «источник изменился». Отпечатка СИТА нет "
        "— значит правка разборщика департамента прочитается как перемена у "
        "Apple. Тот же класс, что ЗКН-Э010, но предмет не клиент, а "
        "первоисточник. Закрывается отпечатком сита в состоянии дозора"),
    "registry/atlas/state.json": (
        "сводка", None,
        "очередь и счётчики разведки: приговора о ком-либо не выносит, "
        "решения приёма принимаются по доходности здесь и сейчас (ст. 46.1)"),
    "registry/state/ios27-watch.json": (
        "сводка", None,
        "улики появления iOS 27: перечень найденного с адресами, а не "
        "сравнение с прошлым"),
    "registry/state/harvest.json": (
        "сводка", None, "список пройденных страниц жатвы: указатель, не приговор"),
    "registry/state/fetch.json": (
        "сводка", None, "итог забора кода: диагноз текущего прогона"),
    "registry/state/FRESH.json": (
        "сводка", None, "свежесть источников: числа текущего снятия"),
    "registry/state/keys.json": (
        "сводка", None,
        "дозор сроков: дни до истечения ключей и требований на момент прогона. "
        "Приговора ни о ком не выносит и с прошлым снятием не сравнивается — "
        "срок это дата, а не перемена"),
    "registry/state/loop-review.json": (
        "сводка", None,
        "журнал проходов петли ревью: живёт внутри одной задачи, между "
        "задачами не сравнивается"),
}

EXPECTED_DEBT = {"registry/state/watch-state.json"}


def _match(rel: str) -> str:
    """Объявленный ключ для найденного файла (с учётом звёздочки)."""
    if rel in DECLARED:
        return rel
    for key in DECLARED:
        if "*" not in key:
            continue
        a, _, b = key.partition("*")
        if rel.startswith(a) and rel.endswith(b) and "/" not in rel[len(a):-len(b) or None].strip("/"):
            return key
    return ""


def has_basis(root: Path, rel: str, spec: str) -> bool:
    """Несёт ли состояние отпечаток своего основания."""
    kind, _, val = spec.partition(":")
    if kind == "sidecar":
        f = root / val
        if not f.exists():
            return False
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return False
        return bool(d.get("adapters"))
    p = root / rel
    if not p.exists():
        return False
    if kind == "field":
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return False
        # Пустое состояние отпечатка не требует: сравнивать ещё не с чем.
        if not d or not any(d.get(k) for k in ("findings", "pages")):
            return True
        return bool(d.get(val))
    if kind == "column":
        txt = p.read_text(encoding="utf-8")
        rows = [ln for ln in txt.splitlines() if ln.startswith("| 20")]
        if not rows:
            return True
        return val in txt.splitlines()[txt.splitlines().index(
            next(ln for ln in txt.splitlines() if ln.startswith("| месяц")))]
    return False


def check(root: Path = None) -> dict:
    """Нарушения и названные долги. Пустой `bad` — закон исполняется."""
    root = root or ROOT
    bad, debts, seen = [], [], []
    for pat in PATTERNS:
        for f in sorted(root.glob(pat)):
            rel = str(f.relative_to(root))
            key = _match(rel)
            seen.append(rel)
            if not key:
                bad.append(f"{rel}: сохранённое состояние НЕ ОБЪЯВЛЕНО. "
                           f"Объяви его в bin/grounds.py: основание приговора "
                           f"(и тогда нужен отпечаток) или сводка (и тогда "
                           f"нужна причина)")
                continue
            kind, spec, note = DECLARED[key]
            if kind == "основание":
                if not has_basis(root, rel, spec):
                    bad.append(f"{rel}: объявлено ОСНОВАНИЕМ приговора, но "
                               f"отпечатка нет ({spec}). Сравнивать нечем — "
                               f"приговор невозможен (ЗКН-Э010)")
            elif kind == "долг":
                debts.append(f"{rel}: {note}")
            elif not note:
                bad.append(f"{rel}: объявлено сводкой без причины")
    for rel in sorted(EXPECTED_DEBT):
        if not any(d.startswith(rel) for d in debts) and (root / rel).exists():
            bad.append(f"{rel}: числится долгом, но в обходе не назван")
    return {"bad": bad, "debts": debts, "seen": seen}


if __name__ == "__main__":
    r = check()
    for b in r["bad"]:
        print("  ✗ " + b)
    for d in r["debts"]:
        print("  ⚠ долг: " + d)
    print(f"состояний найдено {len(r['seen'])} · нарушений {len(r['bad'])} "
          f"· названных долгов {len(r['debts'])}")
    sys.exit(1 if r["bad"] else 0)
