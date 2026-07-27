#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СЛУЖБА, модуль M2 — монитор прода (ст. 56).

После каждого успешного деплоя (workflow_run: deploy-web) служба смотрит на
прод живыми глазами (liveview) и сравнивает находки с базовой линией
предыдущего снятия:
  · НОВОЕ  — регресс: чего вчера не было, а сегодня есть → алерт;
  · ЗАКРЫТО — подтверждение починки: находка исчезла с прода.
Алерт: Slack (если задан секрет SLACK_WEBHOOK_URL), иначе — комментарий к
коммиту деплоя + всегда registry/live/MONITOR.md и строка эфира.
Базовая линия обновляется каждым снятием (registry/live/baseline.json).
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import liveview  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "registry" / "live"


def _key(f):
    return f"{f[0]}|{f[1]}"


def diff_findings(old: list, new: list) -> dict:
    o = {_key(f): f for f in old}
    n = {_key(f): f for f in new}
    return {"new": [n[k] for k in n.keys() - o.keys()],
            "gone": [o[k] for k in o.keys() - n.keys()]}


def _post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status


def alert(text: str, deploy_sha: str):
    hook = os.environ.get("SLACK_WEBHOOK_URL")
    sent = []
    if hook:
        try:
            _post(hook, {"text": text}, {})
            sent.append("slack")
        except Exception:
            pass
    tok, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if tok and repo and deploy_sha:
        try:
            _post(f"https://api.github.com/repos/{repo}/commits/{deploy_sha}/comments",
                  {"body": text}, {"Authorization": f"token {tok}",
                                   "Accept": "application/vnd.github+json",
                                   "User-Agent": "bxad-monitor"})
            sent.append("commit-comment")
        except Exception:
            pass
    return sent


def run() -> dict:
    results = liveview.run_live(ROOT)
    cur = []
    for slug, r in results.items():
        for f in r["findings"]:
            cur.append([f"{slug}:{f[0]}", f[1], f[2]])
    basef = LIVE / "baseline.json"
    base = json.loads(basef.read_text(encoding="utf-8")) if basef.exists() else {"findings": []}
    d = diff_findings(base["findings"], cur)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sha = os.environ.get("DEPLOY_SHA", "")
    lines = [f"# МОНИТОР ПРОДА · {ts}",
             f"Деплой: `{sha[:9]}` · страниц снято: {len(results)} · находок сейчас: {len(cur)}", ""]
    if d["new"]:
        lines.append("## НОВОЕ (регресс)")
        lines += [f"- **{k.split(':')[1]}** на `{k.split(':')[0]}` · `{sel}` — {why}" for k, sel, why in d["new"]]
    if d["gone"]:
        lines.append("## ЗАКРЫТО (починено)")
        lines += [f"- {k.split(':')[1]} · `{sel}` — исчезло с прода" for k, sel, why in d["gone"]]
    if not d["new"] and not d["gone"]:
        lines.append("Изменений против базовой линии нет.")
    (LIVE / "MONITOR.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    basef.write_text(json.dumps({"ts": ts, "sha": sha, "findings": cur}, ensure_ascii=False), encoding="utf-8")
    (LIVE / "monitor-state.json").write_text(json.dumps(
        {"ts": ts, "sha": sha, "now": len(cur), "new": len(d["new"]), "gone": len(d["gone"])}), encoding="utf-8")
    sent = []
    if d["new"] or d["gone"]:
        head = f"BXE монитор · деплой {sha[:9]}: новых находок {len(d['new'])} · закрыто {len(d['gone'])}"
        det = "".join(f"\n• РЕГРЕСС {k.split(':')[1]} {sel}: {why[:90]}" for k, sel, why in d["new"][:6]) + \
              "".join(f"\n• закрыто {k.split(':')[1]} {sel}" for k, sel, why in d["gone"][:6])
        sent = alert(head + det, sha)
    with (ROOT / "registry" / "state" / "CHANGELOG.md").open("a", encoding="utf-8") as f:
        f.write(f"### {ts} · монитор прода\n- сейчас {len(cur)} · новых {len(d['new'])} · закрыто {len(d['gone'])}"
                f" · алерт: {','.join(sent) or 'эфир'}\n\n")
    return {"now": len(cur), "new": len(d["new"]), "gone": len(d["gone"]), "sent": sent}


if __name__ == "__main__":
    r = run()
    print(f"монитор: сейчас {r['now']} · новых {r['new']} · закрыто {r['gone']} · алерт {','.join(r['sent']) or 'эфир'}")
