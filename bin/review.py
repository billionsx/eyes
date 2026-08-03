#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СЛУЖБА, модуль M1 — ревью pull request (ст. 56).

На каждый PR — ревью уровня инженера Apple-школы: находки ТОЛЬКО по строкам,
добавленным диффом, каждое замечание — с правилом AE и числом из измеренных
законов (адресность ЗКН-Э002). Ничего из головы: правила = bin/lint.py,
законы = registry/standards/tokens.json + адаптер проекта.

Механика: GitHub API отдаёт файлы PR с патчами → парсим ДОБАВЛЕННЫЕ строки
(номер в новой версии) → прогоняем полный линт по checkout'у head-ветки →
оставляем только находки, чьи (файл, строка) есть в диффе → публикуем один
review: сводка + до 40 строчных комментариев (side=RIGHT). Чистый дифф тоже
получает ответ службы — присутствие контроля видно всегда.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402
import projects  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
MAX_INLINE = 40


def _api(url, token, data=None, method=None):
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "bxad-review"}, method=method or ("POST" if data else "GET"),
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "{}")


def parse_added(patch: str) -> dict:
    """Патч → {номер строки в новой версии: текст добавленной строки}."""
    added, new_ln = {}, 0
    for ln in (patch or "").splitlines():
        m = HUNK.match(ln)
        if m:
            new_ln = int(m.group(1)) - 1
            continue
        if ln.startswith("-"):
            continue
        new_ln += 1
        if ln.startswith("+"):
            added[new_ln] = ln[1:]
    return added


def pr_files(repo: str, num: int, token: str) -> dict:
    out, page = {}, 1
    while True:
        rows = _api(f"https://api.github.com/repos/{repo}/pulls/{num}/files?per_page=100&page={page}", token)
        for f in rows:
            if f.get("status") != "removed":
                out[f["filename"]] = parse_added(f.get("patch", ""))
        if len(rows) < 100:
            return out


def review(repo: str, num: int, token: str, project_root: Path) -> dict:
    globs_env = os.environ.get("EYES_CLIENT_GLOBS")
    if globs_env:
        adapter = projects.client_pick(
            ROOT, globs=[g.strip() for g in globs_env.split(",") if g.strip()],
            report_rules=["AE1", "AE2", "AE3", "AE4", "AE5", "AE6", "AE7", "AE9", "AE10", "AE11"],
            strict_rules=["AE2", "AE4", "AE6"])
        if adapter.get("_disabled"):
            print(f"паспорт «{adapter.get('project')}» выключен — департамент проект не обслуживает")
            return {"checked": 0, "hits": 0, "disabled": True}
    else:
        adapter = projects.pick(ROOT)
    tokens = json.loads((ROOT / "registry" / "standards" / "tokens.json").read_text(encoding="utf-8"))
    diff = pr_files(repo, num, token)
    res = lint.run(ROOT, adapter, tokens, "strict", project_root)
    res_r = lint.run(ROOT, adapter, tokens, "report", project_root)
    hits = []
    for rule, rel, line, msg in res["findings"] + res_r["findings"]:
        if rel in diff and line in diff[rel]:
            hits.append({"path": rel, "line": line, "side": "RIGHT",
                         "body": f"**BXE · {rule}** — {msg}"})
    checked = sum(len(v) for v in diff.values())
    if hits:
        body = (f"## BXE · ревью по измеренным законам\nСтрок в диффе: {checked} · находок: **{len(hits)}** "
                f"(показаны первые {min(len(hits), MAX_INLINE)} построчно).\n"
                f"Каждое число — из замера/первоисточника с адресом (📐/🍎), суд департамента зелёный.")
        payload = {"event": "COMMENT", "body": body, "comments": hits[:MAX_INLINE]}
    else:
        payload = {"event": "COMMENT",
                   "body": f"## BXE · ревью по измеренным законам\nСтрок в диффе: {checked} · находок: 0 — дифф чист по {len(res['rules'])+len(res_r['rules'])} правилам AE."}
    if os.environ.get("BXE_DRY") != "1":
        _api(f"https://api.github.com/repos/{repo}/pulls/{num}/reviews", token, payload)
    return {"checked": checked, "hits": len(hits)}


if __name__ == "__main__":
    r = review(os.environ["GITHUB_REPOSITORY"], int(os.environ["PR_NUMBER"]),
               os.environ["GITHUB_TOKEN"], Path(os.environ.get("PROJECT_ROOT", ".")).resolve())
    print(f"ревью: строк в диффе {r['checked']} · находок {r['hits']}")
