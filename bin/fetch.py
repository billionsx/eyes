#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ЗАБОР КОДА ПОДКЛЮЧЁННЫХ ПРОЕКТОВ (ст. 57).

Департамент живёт в своём репозитории, а судит чужой код. Здесь он приносит
код каждого обслуживаемого проекта в `_projects/<имя>` — поверхностной копией
(depth 1, без блобов истории). Публичный репозиторий берётся без токена;
приватный — токеном из EYES_PROJECTS_TOKEN.

Ни одного имени проекта в коде: список — только из `adapters/*.json`.
Выход — строки «проект: файлов N» и код возврата 0, даже если часть
репозиториев недоступна: недоступность фиксируется словами, а не падением
(БТ001 — не выдумывать; отсутствие честнее подмены).
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import projects  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "_projects"


def clone(name: str, repo: str, branch: str = "main") -> tuple:
    tok = os.environ.get("EYES_PROJECTS_TOKEN", "")
    url = (f"https://x-access-token:{tok}@github.com/{repo}.git" if tok
           else f"https://github.com/{repo}.git")
    out = DEST / name
    if out.exists():
        return name, "уже забран", sum(1 for _ in out.rglob("*"))
    cmd = ["git", "clone", "--depth", "1", "--filter=blob:none", "--no-tags",
           "-b", branch, "-q", url, str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        err = (r.stderr or "").replace(tok, "***") if tok else (r.stderr or "")
        return name, f"НЕ ЗАБРАН: {err.strip().splitlines()[-1] if err.strip() else 'rc=' + str(r.returncode)}", 0
    return name, "забран", sum(1 for _ in out.rglob("*") if _.is_file())


def main() -> int:
    DEST.mkdir(exist_ok=True)
    ads = projects.enabled(ROOT)
    if not ads:
        print("паспортов к обслуживанию нет — забирать нечего")
        return 0
    for name, a in ads.items():
        repo = a.get("repo") or ""
        if not repo:
            print(f"{name}: repo в паспорте не указан — код не забирается")
            continue
        n, state, files = clone(name, repo, a.get("branch", "main"))
        print(f"{n}: {state} · файлов {files} · {repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
