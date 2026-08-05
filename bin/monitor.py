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
import vision as vision_mod  # noqa: E402  отпечаток измерителя

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "registry" / "live"


def _key(f):
    return f"{f[0]}|{f[1]}"


def _page(f):
    return str(f[0]).split(":")[0]


def diff_findings(old: list, new: list, pages_old=None, pages_new=None) -> dict:
    """Расхождение с базовой линией — ТОЛЬКО по страницам, снятым в оба раза.

    Родословная (05.08.2026). Монитор сравнивал списки находок целиком и всякое
    расхождение объявлял «РЕГРЕСС» — со алертом в Slack и комментарием к
    коммиту деплоя клиента. Но расхождение бывает трёх родов, и два из них к
    клиенту не относятся:

      · клиент выложил новое нарушение — это регресс, и алерт по адресу;
      · департамент изменил свои правила или измеренные числа — находка
        появилась «сама», а обвинён деплой клиента;
      · список наблюдаемых страниц изменился — находки целой страницы приходят
        или уходят гуртом, и это читается как обвал или как починка.

    Третий род лечится здесь: страницы, снятые лишь в один из двух разов,
    выводятся из приговора и называются отдельно. Второй род лечится в run()
    сравнением отпечатков измерителя.

    Ложная починка не менее вредна, чем ложное обвинение: департамент,
    хвалящий клиента за то, чего тот не делал, теряет цену своей похвалы
    ровно так же, как обвиняющий — цену обвинения.
    """
    o = {_key(f): f for f in old}
    n = {_key(f): f for f in new}
    if pages_old is not None and pages_new is not None:
        both = set(pages_old) & set(pages_new)
        o = {k: v for k, v in o.items() if _page(v) in both}
        n = {k: v for k, v in n.items() if _page(v) in both}
        added = sorted(set(pages_new) - set(pages_old))
        dropped = sorted(set(pages_old) - set(pages_new))
    else:
        added = dropped = []
    return {"new": [n[k] for k in n.keys() - o.keys()],
            "gone": [o[k] for k in o.keys() - n.keys()],
            "pages_added": added, "pages_dropped": dropped}


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
    pages = sorted(results.keys())
    basef = LIVE / "baseline.json"
    base = (json.loads(basef.read_text(encoding="utf-8")) if basef.exists()
            else {"findings": [], "pages": [], "vision": ""})
    vis = vision_mod.fingerprint(ROOT)
    was = base.get("vision", "")
    # ОСНОВАНИЕ. Пока измеритель тот же — расхождение принадлежит клиенту.
    # Сменился или не записан — приговора нет вовсе: ни регресса, ни починки,
    # ни алерта. Незнание не есть совпадение (ЗКН-Э001).
    comparable = bool(was) and was == vis
    # Граница отпечатка названа прямо. Он снимается прогоном линта по
    # эталонному корпусу и ловит смену правил AE и смену ИЗМЕРЕННЫХ ЧИСЕЛ
    # базы. Правка логики самого liveview.py им НЕ ловится: живой взгляд судит
    # DOM своим кодом. Значит после правки liveview базовую линию надо снимать
    # заново вручную, и это ограничение лучше знать, чем считать, будто
    # отпечаток покрывает всё (ЗКН-Э001 — о себе тоже).
    d = diff_findings(base.get("findings", []), cur,
                      base.get("pages"), pages) if comparable else {
        "new": [], "gone": [], "pages_added": [], "pages_dropped": [],
        "ungrounded": True}
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
    if d.get("pages_added") or d.get("pages_dropped"):
        lines.append("## СПИСОК СТРАНИЦ ИЗМЕНИЛСЯ (из приговора выведены)")
        lines += [f"- добавлена `{p}`" for p in d.get("pages_added", [])]
        lines += [f"- убрана `{p}`" for p in d.get("pages_dropped", [])]
    if d.get("ungrounded"):
        lines.append("## ОСНОВАНИЯ ДЛЯ ПРИГОВОРА НЕТ")
        lines.append(f"- отпечаток измерителя: было `{was or 'не записан'}`, "
                     f"стало `{vis}`. Расхождение с базовой линией снято "
                     f"РАЗНЫМИ измерителями и клиенту не принадлежит: "
                     f"ни регресса, ни починки, ни алерта. Базовая линия "
                     f"взята заново.")
    elif not d["new"] and not d["gone"]:
        lines.append("Изменений против базовой линии нет.")
    (LIVE / "MONITOR.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    basef.write_text(json.dumps({"ts": ts, "sha": sha, "findings": cur,
                                 "pages": pages, "vision": vis},
                                ensure_ascii=False), encoding="utf-8")
    (LIVE / "monitor-state.json").write_text(json.dumps(
        {"ts": ts, "sha": sha, "now": len(cur), "new": len(d["new"]),
         "gone": len(d["gone"]), "vision": vis,
         "grounded": not d.get("ungrounded", False)}), encoding="utf-8")
    sent = []
    if d["new"] or d["gone"]:
        head = f"BXE монитор · деплой {sha[:9]}: новых находок {len(d['new'])} · закрыто {len(d['gone'])}"
        det = "".join(f"\n• РЕГРЕСС {k.split(':')[1]} {sel}: {why[:90]}" for k, sel, why in d["new"][:6]) + \
              "".join(f"\n• закрыто {k.split(':')[1]} {sel}" for k, sel, why in d["gone"][:6])
        sent = alert(head + det, sha)
    with (ROOT / "registry" / "state" / "CHANGELOG.md").open("a", encoding="utf-8") as f:
        f.write(f"### {ts} · монитор прода\n- сейчас {len(cur)} · новых {len(d['new'])} · закрыто {len(d['gone'])}"
                f" · алерт: {','.join(sent) or 'эфир'}\n\n")
    return {"now": len(cur), "new": len(d["new"]), "gone": len(d["gone"]),
            "sent": sent, "grounded": not d.get("ungrounded", False)}


if __name__ == "__main__":
    r = run()
    if not r.get("grounded"):
        print("монитор: приговора нет — отпечаток измерителя сменился, "
              "базовая линия взята заново")
    print(f"монитор: сейчас {r['now']} · новых {r['new']} · закрыто {r['gone']} "
          f"· алерт {','.join(r['sent']) or 'эфир'}")
