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
(ЗКН-Э001 — не выдумывать; отсутствие честнее подмены).
"""
import json
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
    # GIT_TERMINAL_PROMPT=0: без него git на закрытый или несуществующий адрес
    # отвечает «could not read Username» — то есть прячет причину за спросом
    # логина. Диагноз обязан называть предмет, а не симптом.
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="echo")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)
    if r.returncode != 0:
        err = (r.stderr or "").replace(tok, "***") if tok else (r.stderr or "")
        last = err.strip().splitlines()[-1] if err.strip() else "rc=" + str(r.returncode)
        low = err.lower()
        if ("not found" in low or "could not read username" in low
                or "authentication failed" in low or "terminal prompts disabled" in low):
            last = (f"адрес недоступен: репозитория {repo} нет либо он закрыт "
                    f"для департамента")
        elif "remote branch" in low or "not found in upstream" in low:
            last = f"ветки «{branch}» в {repo} нет"
        return name, f"НЕ ЗАБРАН: {last}", 0
    return name, "забран", sum(1 for _ in out.rglob("*") if _.is_file())


def main() -> int:
    """Итог забора кладётся в реестр, а не только в лог прогона.

    Причина «код не забран» бывает разной: адреса не существует, ветка не та,
    доступ закрыт. Раньше эта разница жила в логе, а советник видел только
    пустую папку и писал одинаковое «код не забран» — то есть терял диагноз
    ровно там, где он нужен.
    """
    DEST.mkdir(exist_ok=True)
    ads = projects.enabled(ROOT)
    st = {}
    out = ROOT / "registry" / "state" / "fetch.json"
    if not ads:
        print("паспортов к обслуживанию нет — забирать нечего")
        out.write_text(json.dumps({}, ensure_ascii=False, indent=1), encoding="utf-8")
        return 0
    for name, a in ads.items():
        repo = a.get("repo") or ""
        if not repo:
            print(f"{name}: repo в паспорте не указан — код не забирается")
            st[name] = {"repo": "", "state": "адрес не указан", "files": 0}
            continue
        n, state, files = clone(name, repo, a.get("branch", "main"))
        print(f"{n}: {state} · файлов {files} · {repo}")
        st[n] = {"repo": repo, "state": state, "files": files,
                 "branch": a.get("branch", "main")}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(st, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
