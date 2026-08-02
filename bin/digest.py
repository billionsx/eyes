#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ЗНАНИЕ. Детерминированная выжимка стандартов из снимков — без ИИ.

Снимок хранит сырой текст страницы; знание — её нормативную часть:
предложения с маркерами предписания (Use / Avoid / Don't / must / should /
Always / Never / Prefer / minimum / at least) и предложения с величинами
(pt / px / ms / % / ×). Заголовки сохраняются как структура.

Выжимка кладётся в registry/knowledge/<id>.md; индекс по доменам мандата —
knowledge/INDEX.md. Один и тот же снимок даёт один и тот же файл: знание
воспроизводимо, дифф знания честен. Числа ОТСЮДА не попадают в tokens.json —
tokens несут только замеры с адресом (Э002); знание — это текст стандарта,
навигация и сырьё для будущих замеров.
"""
import json
import re
from pathlib import Path

NORM = re.compile(
    r"\b(use|avoid|don[’']t|do not|must|should|always|never|prefer|require[sd]?|"
    r"at least|minimum|maximum|recommended|be sure|make sure|ensure|turn on)\b", re.I)
# Единица измерения в прозе Apple пишется СЛОВОМ: «16 points», а не «16pt».
# Родословная (02.08.2026): сито было построено под CSS-запись и не узнавало
# ни одного написания словом — «points» начинается на «po», а не на «pt».
# Замер: из 29 822 добытых строк число с единицей несли 173, связываемых
# норм — 27. Все числовые нормы HIG терялись именно здесь.
_UNIT = (r"(?:pts?\b|points?\b|px\b|pixels?\b|dp\b|ms\b|milliseconds?\b|"
         r"seconds?\b|hz\b|degrees?\b|%)")
QTY = re.compile(
    r"(?:\b\d+(?:\.\d+)?\s*[x\u00d7]\s*\d+(?:\.\d+)?\s*" + _UNIT + r")"
    r"|(?:\b\d+(?:\.\d+)?\s*" + _UNIT + r")"
    r"|(?:\b\d+\s*[x\u00d7]\s*\d+\b)", re.I)
HEAD = re.compile(r"^={2,4} (.+)$")           # снимок хранит заголовки как ==/===/====
SENT_MAX = 120                                 # предложений на источник — кап детерминизма
LINE_MAX = 300


def _sentences(block: str):
    for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", block).strip()):
        s = s.strip()
        if 25 <= len(s) <= LINE_MAX:
            yield s


def digest_snapshot(text: str) -> list:
    """[(heading|None, sentence), ...] — только нормативное и измеримое."""
    out, cur = [], None
    for raw in text.splitlines():
        m = HEAD.match(raw.strip())
        if m:
            cur = m.group(1).strip()
            continue
        for s in _sentences(raw):
            if NORM.search(s) or QTY.search(s):
                out.append((cur, s))
                if len(out) >= SENT_MAX:
                    return out
    return out


def build(root: Path) -> dict:
    reg = root / "registry"
    srcs = {s["id"]: s for s in json.loads((reg / "sources.json").read_text(encoding="utf-8"))["sources"]}
    kdir = reg / "knowledge"
    kdir.mkdir(exist_ok=True)
    changed, by_domain = [], {}
    for snap in sorted((reg / "snapshots").glob("*.txt")):
        sid = snap.stem
        src = srcs.get(sid, {})
        rows = digest_snapshot(snap.read_text(encoding="utf-8", errors="replace"))
        for d in src.get("domains", ["прочее"]):
            by_domain.setdefault(d, []).append((sid, len(rows)))
        body = [f"# знание · `{sid}`",
                f"Источник: {src.get('url', '?')}",
                f"Домены мандата: {', '.join(src.get('domains', []))}",
                "Нормативных положений: %d (детерминированная выжимка, не пересказ)" % len(rows), ""]
        last_h = object()
        for h, s in rows:
            if h != last_h:
                body.append(f"\n## {h or 'без раздела'}")
                last_h = h
            body.append(f"- {s}")
        new = "\n".join(body) + "\n"
        fp = kdir / f"{sid}.md"
        old = fp.read_text(encoding="utf-8") if fp.exists() else ""
        if new != old:
            fp.write_text(new, encoding="utf-8")
            changed.append(sid)
    idx = ["# ЗНАНИЕ · индекс по доменам мандата",
           "Выжимка нормативных положений из снимков разведки. Числа отсюда в tokens.json НЕ переносятся (Э002).", ""]
    for d in sorted(by_domain):
        idx.append(f"## {d}")
        for sid, n in sorted(by_domain[d]):
            idx.append(f"- [`{sid}`]({sid}.md) · положений: {n}")
        idx.append("")
    (kdir / "INDEX.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    return {"sources": len(list((reg / "snapshots").glob('*.txt'))), "changed": changed}


if __name__ == "__main__":
    r = build(Path(__file__).resolve().parents[1])
    print(f"знание: источников {r['sources']} · обновлено выжимок {len(r['changed'])}")
    for sid in r["changed"]:
        print(f"  Δ {sid}")
