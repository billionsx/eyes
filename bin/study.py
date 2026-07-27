#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ИЗУЧЕННОСТЬ. Машинный ответ на вопрос «изучены ли все пункты».

По каждой статье Кодекса доменов (Раздел III конституции) леджер считает,
ЧЕМ статья изучена:
  ЗАМЕР   — статья несёт измеренные величины (pt/мс/px, hex, ×, доли, 📐);
  ЗНАНИЕ  — дозорные источники статьи принесли нормативные положения
            (registry/knowledge, счёт по каждому);
  🕳      — статья сама объявляет честный долг.
Статья без замера, без знания и без 🕳 — НЕ ИЗУЧЕНО: exit 1, суд красный.
Отчёт: registry/state/STUDY.md. Без ИИ: только разбор текста и счёт.
"""
import json
import re
from pathlib import Path

ART = re.compile(r"\*\*Статья (\d+(?:\.\d+)?) · ([^.*]+)\.\*\*(.*?)(?=\*\*Статья |\Z)", re.S)
MEAS = re.compile(r"\d+(?:[.,]\d+)?\s?(?:pt|px|мс|ms)\b|#[0-9A-Fa-f]{6}|\d+\s?×\s?\d+"
                  r"|±0\.4|\.0?5\b|scale \.\d+|📐")
SRC = re.compile(r"`([a-z0-9][a-z0-9-]+)`")


def run(root: Path) -> dict:
    const = (root / "CONSTITUTION.md").read_text(encoding="utf-8")
    try:
        codex = const.split("## РАЗДЕЛ III")[1].split("## РАЗДЕЛ IV")[0]
    except IndexError:
        codex = const
    src_ids = {s["id"] for s in json.loads(
        (root / "registry" / "sources.json").read_text(encoding="utf-8"))["sources"]}
    kn_dir = root / "registry" / "knowledge"

    def props(sid: str) -> int:
        f = kn_dir / f"{sid}.md"
        if not f.exists():
            return 0
        m = re.search(r"Нормативных положений: (\d+)", f.read_text(encoding="utf-8"))
        return int(m.group(1)) if m else 0

    rows, bad = [], []
    for num, title, body in ART.findall(codex):
        srcs = [s for s in SRC.findall(body) if s in src_ids]
        kn = sum(props(s) for s in srcs)
        meas = bool(MEAS.search(body))
        hole = "🕳" in body
        ways = ([" ЗАМЕР"] if meas else []) + ([f"ЗНАНИЕ {kn}"] if kn else []) + (["🕳"] if hole else [])
        status = " + ".join(w.strip() for w in ways) if ways else "НЕ ИЗУЧЕНО"
        if not ways:
            bad.append(f"ст. {num} · {title.strip()}")
        rows.append((num, title.strip(), " · ".join(srcs) or "—", kn, status))

    out = ["# ИЗУЧЕННОСТЬ · карта по статьям Кодекса доменов",
           "Машинный ответ на «изучены ли все пункты»: чем изучена каждая статья.",
           "", "| Статья | Домен | Дозор | Положений | Статус |", "|---|---|---|---|---|"]
    for num, ttl, s, kn, st in rows:
        out.append(f"| {num} | {ttl} | {s} | {kn} | **{st}** |")
    tot_kn = sum(r[3] for r in rows)
    n_meas = sum(1 for r in rows if "ЗАМЕР" in r[4])
    n_kn = sum(1 for r in rows if "ЗНАНИЕ" in r[4])
    n_hole = sum(1 for r in rows if r[4] == "🕳")
    out += ["", f"Итог: статей {len(rows)} · с замером {n_meas} · со знанием {n_kn} "
                f"(положений {tot_kn}) · честных 🕳 {n_hole} · НЕ ИЗУЧЕНО {len(bad)}"
                + ((" — КРАСНЫЙ: " + "; ".join(bad)) if bad else "")]
    (root / "registry" / "state" / "STUDY.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    return {"articles": len(rows), "knowledge": tot_kn, "measured": n_meas,
            "known": n_kn, "holes": n_hole, "bad": bad}


if __name__ == "__main__":
    import sys
    r = run(Path(__file__).resolve().parents[1])
    print(f"изученность: статей {r['articles']} · замером {r['measured']} · знанием {r['known']} "
          f"(положений {r['knowledge']}) · 🕳 {r['holes']} · не изучено {len(r['bad'])}")
    for b in r["bad"]:
        print("  НЕ ИЗУЧЕНО:", b)
    sys.exit(1 if r["bad"] else 0)
