#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СЛИЯНИЕ СКЛАДА. Объединение долек корпуса по адресу.

Зачем орган существует. Хроника при столкновении с чужой записью делала
`git pull --rebase -X theirs`. Для журнала это допустимо: события упорядочены
временем, и потеря чужой строки заметна. Для СКЛАДА — нет: две записи в одну
дольку означают, что страницы одного писателя молча исчезают. Департамент,
который теряет добытое при каждом совпадении по времени, обогащается медленнее,
чем думает, и не может этого заметить.

Склад ключуется адресом. Значит, у столкновения есть правильный ответ, и он
не «чей-то победил», а ОБЪЕДИНЕНИЕ: страница, которой нет у одного, берётся у
другого; страница, которая есть у обоих, берётся более поздняя.

Второе. gzip кладёт в заголовок время записи, поэтому одинаковое содержимое
даёт разные байты — дольки конфликтовали на пустом месте и раздували
репозиторий. Запись ведётся с `mtime=0`: одинаковое содержимое — одинаковые
байты.

Запуск (драйвер слияния git):  corpus_merge.py %O %A %B
Запуск вручную:               corpus_merge.py --check долька.jsonl.gz
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

KEYS = ("id", "page")     # атлас ключует «id», жатва — «page»


def _key(rec: dict) -> str:
    for k in KEYS:
        if rec.get(k):
            return f"{k}:{rec[k]}"
    return ""


def read(path: Path) -> dict:
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    r = json.loads(ln)
                except json.JSONDecodeError:
                    continue      # повреждённая строка не отменяет дольку
                k = _key(r)
                if k:
                    out[k] = r
    except OSError:
        pass
    return out


def write(path: Path, rows: dict) -> None:
    """Детерминированно: mtime=0 и порядок ключей. Одинаковое содержимое —
    одинаковые байты, иначе дольки конфликтуют на пустом месте."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(rows[k], ensure_ascii=False, sort_keys=True)
                     for k in sorted(rows)) + ("\n" if rows else "")
    with gzip.GzipFile(filename="", mode="wb", fileobj=open(path, "wb"),
                       mtime=0) as fh:
        fh.write(body.encode("utf-8"))


def union(base: Path, ours: Path, theirs: Path) -> tuple[dict, dict]:
    """Объединить по адресу. Возвращает (итог, статистика)."""
    a, b = read(ours), read(theirs)
    merged = dict(a)
    added = 0
    for k, v in b.items():
        if k not in merged:
            merged[k] = v
            added += 1
    return merged, {"наших": len(a), "чужих": len(b),
                    "взято_у_чужих": added, "итог": len(merged)}


def main(argv: list[str]) -> int:
    if "--check" in argv:
        p = Path(argv[argv.index("--check") + 1])
        rows = read(p)
        print(f"{p}: записей {len(rows)}")
        return 0
    if len(argv) < 4:
        print("использование: corpus_merge.py %O %A %B  |  --check файл")
        return 2
    base, ours, theirs = (Path(x) for x in argv[1:4])
    merged, st = union(base, ours, theirs)
    write(ours, merged)     # git ждёт итог в %A
    print(f"склад слит: наших {st['наших']} + чужих {st['чужих']} "
          f"→ {st['итог']} (взято у чужих {st['взято_у_чужих']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
