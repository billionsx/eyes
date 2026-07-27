#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СЛУЖБА, модуль M6 — Big7-бриф недели (ст. 56).

Еженедельная выжимка второй кафедры: что нового сказали семь фирм и как
сдвинулась карта фреймворков. Ничего из головы:
  · НОВЫЕ ПОЛОЖЕНИЯ — записи library/big7.jsonl за неделю (по полю ts;
    записи без ts — хвост файла, методика объявлена в брифе), дословно,
    с фирмой и адресом page:;
  · ДВИЖЕНИЕ РАМОК — дифф частот frames против снимка прошлой недели
    (registry/bizlab/frames-week.json);
  · ВОПРОСЫ К ПРОДУКТУ — канонический вопрос каждой выросшей рамки из
    объявленного словаря (вопрос рамки, не выдуманный вывод).
Выход: briefs/ГГГГ-Wнн.md + latest.md · строка эфира.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAIL_FALLBACK = 40

FRAME_QUESTIONS = {
    "ZBB": "какие статьи расходов проекта собрать с нуля, а не от прошлого месяца?",
    "RAPID": "по ключевым решениям недели — кто R·A·P·I·D? нет ли решений без Decide?",
    "Пирамида Минто": "начинаются ли наши документы с ответа, а не с предыстории?",
    "NPS": "что сказали бы промоутеры и детракторы про последний релиз?",
    "Три горизонта": "что в бэклоге относится к H2/H3, а не только к текучке H1?",
    "Jobs to be Done": "какую работу пользователь «нанимает» экран сделать — и делает ли он её?",
    "Юнит-экономика": "сходится ли экономика одной единицы (пользователь/подписка) без усреднений?",
    "Пять сил": "какая из пяти сил давит на продукт сильнее всего в этом квартале?",
    "North Star": "двигает ли работа недели метрику-полярную звезду или локальные прокси?",
    "Design Thinking": "тестировали ли мы прототипом на живом пользователе до кода?",
}


def run() -> dict:
    lib = ROOT / "registry" / "library" / "big7.jsonl"
    rows = []
    if lib.exists():
        for ln in lib.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(ln))
            except Exception:
                pass
    now = datetime.now(timezone.utc)
    week = now.strftime("%G-W%V")
    week_ago = now.timestamp() - 7 * 86400
    fresh = [r for r in rows if r.get("ts") and datetime.fromisoformat(r["ts"]).timestamp() >= week_ago]
    method = "по полю ts (неделя)"
    if not fresh:
        fresh = rows[-TAIL_FALLBACK:]
        method = f"хвост добычи ({len(fresh)} последних записей — ts появится со следующего урожая)"
    st = json.loads((ROOT / "registry" / "bizlab" / "state.json").read_text(encoding="utf-8"))
    frames_now = {k: int(v) for k, v in st.get("frames", {}).items()}
    snapf = ROOT / "registry" / "bizlab" / "frames-week.json"
    frames_prev = json.loads(snapf.read_text(encoding="utf-8")) if snapf.exists() else {}
    drift = sorted(((k, frames_now.get(k, 0) - frames_prev.get(k, 0), frames_now.get(k, 0))
                    for k in set(frames_now) | set(frames_prev)), key=lambda x: -x[1])
    grew = [(k, d, n) for k, d, n in drift if d > 0]
    by_firm = {}
    for r in fresh:
        by_firm.setdefault(r.get("firm", "?"), []).append(r)
    md = [f"# BIG7 · бриф недели {week}",
          f"Кафедра: McKinsey · BCG · Bain · Deloitte · PwC · EY · KPMG. Новые положения: {method}.",
          "Каждое положение — дословно словами фирмы, адрес page:.", ""]
    for firm in sorted(by_firm):
        md.append(f"## {firm} · {len(by_firm[firm])}")
        for r in by_firm[firm][:6]:
            md.append(f"- «{r['text']}»  \n  `{r['at']}`")
        md.append("")
    md.append("## Движение рамок за неделю")
    if any(d for _, d, _ in drift):
        md += [f"- {k}: {'+' if d > 0 else ''}{d} (всего {n})" for k, d, n in drift if d][:12]
    else:
        md.append("- снимка прошлой недели не было — зафиксирован текущий (движение появится со следующего брифа)")
    md += ["", "## Вопросы к продукту (канонические вопросы выросших рамок)"]
    qs = [(k, FRAME_QUESTIONS[k]) for k, d, _ in (grew or [(k, 0, n) for k, n in
          sorted(frames_now.items(), key=lambda x: -x[1])[:3]]) if k in FRAME_QUESTIONS][:5]
    md += [f"- **{k}** — {q}" for k, q in qs] or ["- рамки недели не входят в словарь вопросов"]
    out = ROOT / "briefs"
    out.mkdir(exist_ok=True)
    text = "\n".join(md) + "\n"
    (out / f"{week}.md").write_text(text, encoding="utf-8")
    (out / "latest.md").write_text(text, encoding="utf-8")
    snapf.write_text(json.dumps(frames_now, ensure_ascii=False), encoding="utf-8")
    with (ROOT / "registry" / "state" / "CHANGELOG.md").open("a", encoding="utf-8") as f:
        f.write(f"### · big7-бриф {week}\n- положений в брифе {len(fresh)} · рамок выросло {len(grew)}\n\n")
    return {"week": week, "fresh": len(fresh), "grew": len(grew), "firms": len(by_firm)}


if __name__ == "__main__":
    r = run()
    print(f"бриф {r['week']}: положений {r['fresh']} · фирм {r['firms']} · рамок выросло {r['grew']}")
