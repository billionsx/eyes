#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СВЕРКА ПРАВ ПОДКЛЮЧЕНИЯ (ст. 56).

Зачем орган. 04.08.2026 контур ревью PR был проверен впервые живым PR в
репозитории клиента — и умер до первого шага: `startup_failure`, ноль работ,
ноль сообщений. Причина: с 2023 года GitHub по умолчанию выдаёт токену
прогона ТОЛЬКО ЧТЕНИЕ, а вызываемый контур департамента просит
`pull-requests: write`. Превышение гасит запуск целиком.

Цена ошибки — не сбой, а МОЛЧАНИЕ. Клиент кладёт десять строк, видит, что
файл на месте, и считает, что надзор работает. Надзор при этом не сработал
ни разу: контур ревью имел ноль прогонов за всё время своего существования.
Молчание нельзя предъявлять как чистоту (ЗКН-Э001) — ни клиенту, ни себе.

Что делает орган. Читает вызываемые контуры (`workflow_call`) и шаблоны
подключения и требует машиной: права вызывающего ПОКРЫВАЮТ права
вызываемого. Не покрывают — красный, с именем файла, ключом и недостающим
уровнем.

Только stdlib: разбор YAML здесь узкий и свой — департамент обязан
запускаться на голом python3, а нужны ровно два ключа, `permissions` и
`uses`.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
TPL = ROOT / "templates"

LEVEL = {"none": 0, "read": 1, "write": 2}


def permissions(text: str) -> dict:
    """Все блоки `permissions:` файла, слитые в один словарь по максимуму.

    Вызывающему всё равно, объявлены права наверху файла или в работе:
    важно, что токен их получает. Поэтому берётся максимум по файлу.
    """
    out = {}
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if not re.match(r"^\s*permissions:\s*$", ln):
            continue
        indent = len(ln) - len(ln.lstrip())
        for row in lines[i + 1:]:
            if not row.strip() or row.lstrip().startswith("#"):
                continue
            ri = len(row) - len(row.lstrip())
            if ri <= indent:
                break
            m = re.match(r"^\s*([\w-]+):\s*([\w-]+)\s*$", row)
            if not m:
                break
            k, v = m.group(1), m.group(2).lower()
            if v in LEVEL and LEVEL[v] > LEVEL.get(out.get(k, "none"), 0):
                out[k] = v
    return out


def calls(text: str) -> list:
    """Имена вызываемых контуров департамента: `uses: billionsx/eyes/....yml@ref`."""
    return re.findall(r"uses:\s*billionsx/eyes/\.github/workflows/([\w.-]+\.yml)@", text)


def check(root: Path = None) -> list:
    """Список нарушений. Пустой список — права покрыты везде."""
    root = root or ROOT
    wf, tpl = root / ".github" / "workflows", root / "templates"
    bad = []
    for t in sorted(tpl.glob("*.yml")):
        text = t.read_text(encoding="utf-8")
        granted = permissions(text)
        for name in calls(text):
            f = wf / name
            if not f.exists():
                bad.append(f"{t.name}: зовёт {name}, которого нет в департаменте")
                continue
            need = permissions(f.read_text(encoding="utf-8"))
            for k, v in need.items():
                have = granted.get(k, "none")
                if LEVEL[have] < LEVEL[v]:
                    bad.append(
                        f"{t.name}: зовёт {name}, тот просит {k}: {v}, "
                        f"а вызывающий даёт {have} — прогон умрёт до первого "
                        f"шага (startup_failure), и надзор промолчит")
    return bad


if __name__ == "__main__":
    bad = check()
    for b in bad:
        print("  ✗ " + b)
    print("права подключения покрыты" if not bad
          else f"НЕ ПОКРЫТО: {len(bad)}")
    sys.exit(1 if bad else 0)
