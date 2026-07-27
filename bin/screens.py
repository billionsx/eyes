#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · КАДРОТЕКА. Живые кадры приложений Apple → пиксель-факты в реестр.

Кадр — первоисточник (📐 с адресом screen:<app>/<file>). Орган считает по
каждому кадру детерминированно, без ИИ:
  · класс устройства (1179×2556 = iPhone 393×852 pt @3x — эталон конвейера);
  · долю пикселей ТОЧНЫХ цветов лестницы конституции (ст. 9) и узловых
    заливок (#1C1C1C кнопка · #2C2C2C чип · #38383A волосок);
  · присутствие запрещённого тёплого двойника #8E8E8E (ст. 9/AE6);
  · доминирующие цвета вне лестницы (кандидаты в замер новой базы —
    сырьё MIGRATION, числами становятся только через конвейер замера).
Паспорта: registry/screens/passports/<app>.json · свод: state/SCREENS.md.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

LADDER = {"#000000": "фон", "#1C1C1E": "ступень-1", "#2C2C2E": "ступень-2",
          "#1C1C1C": "кнопка", "#2C2C2C": "чип", "#181818": "полка",
          "#111111": "полка-глубь", "#38383A": "волосок"}
FORBID = {"#8E8E8E": "тёплый двойник (AE6)"}
DEVICES = {(1179, 2556): "iPhone 393×852pt @3x (эталон)",
           (1290, 2796): "iPhone 430×932pt @3x", (1170, 2532): "iPhone 390×844pt @3x"}


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(int(x) for x in rgb[:3])


def passport(png: Path, app: str) -> dict:
    im = Image.open(png).convert("RGB")
    w, h = im.size
    a = np.asarray(im, dtype=np.uint32).reshape(-1, 3)
    n = a.shape[0]
    packed = (a[:, 0] << 16) | (a[:, 1] << 8) | a[:, 2]
    vals, counts = np.unique(packed, return_counts=True)
    order = np.argsort(-counts)[:400]
    top = [(int(counts[i]), int(vals[i])) for i in order]
    cmap = {"#%06X" % v: cnt for cnt, v in top}
    ladder_share = {hx: round(cmap.get(hx, 0) / n, 5) for hx in LADDER}
    forb = {hx: cmap.get(hx, 0) for hx in FORBID if cmap.get(hx, 0) > 0}
    off = []
    for cnt, v in top[:40]:
        hx = "#%06X" % v
        if hx not in LADDER and hx not in FORBID and cnt / n >= 0.01:
            off.append({"hex": hx, "share": round(cnt / n, 4)})
    return {"file": png.name, "at": f"screen:{app}/{png.name}",
            "size_px": [w, h], "device": DEVICES.get((w, h), f"{w}×{h}px (класс не в карте)"),
            "ladder_share": {k: v for k, v in ladder_share.items() if v > 0},
            "forbidden_hits": forb, "off_ladder_top": off[:12]}


def run(root: Path, frames_dir: Path) -> dict:
    out = root / "registry" / "screens" / "passports"
    out.mkdir(parents=True, exist_ok=True)
    apps, total = {}, 0
    for app_dir in sorted(p for p in frames_dir.iterdir() if p.is_dir()):
        app = app_dir.name
        rows = []
        for png in sorted(app_dir.glob("*.PNG")) + sorted(app_dir.glob("*.png")):
            rows.append(passport(png, app))
            total += 1
        if not rows:
            continue
        agg_off = Counter()
        for r in rows:
            for o in r["off_ladder_top"]:
                agg_off[o["hex"]] += o["share"]
        apps[app] = {"frames": len(rows),
                     "ladder_avg": {k: round(sum(r["ladder_share"].get(k, 0) for r in rows) / len(rows), 4)
                                    for k in LADDER},
                     "forbidden_frames": sum(1 for r in rows if r["forbidden_hits"]),
                     "off_ladder_candidates": [{"hex": h, "weight": round(w2, 3)}
                                               for h, w2 in agg_off.most_common(10)]}
        (out / f"{app.replace(' ', '_')}.json").write_text(
            json.dumps({"app": app, "summary": apps[app], "frames": rows},
                       ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# КАДРОТЕКА · живые кадры Apple (поставка основателя, iOS 27)",
          "Кадр — первоисточник 📐 с адресом screen:<app>/<file>. Числа новой базы — только конвейером замера.",
          "", "| Приложение | Кадров | Ø фон #000000 | Ø ступень-1 | Ø чип | Кадров с #8E8E8E | Топ вне лестницы |",
          "|---|---|---|---|---|---|---|"]
    for app, s in sorted(apps.items()):
        offs = " ".join(f"{o['hex']}·{o['weight']}" for o in s["off_ladder_candidates"][:3])
        md.append(f"| {app} | {s['frames']} | {s['ladder_avg'].get('#000000', 0)} | "
                  f"{s['ladder_avg'].get('#1C1C1E', 0)} | {s['ladder_avg'].get('#2C2C2C', 0)} | "
                  f"{s['forbidden_frames']} | {offs} |")
    md += ["", f"Итого кадров: {total} · приложений: {len(apps)}"]
    (root / "registry" / "state" / "SCREENS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return {"apps": len(apps), "frames": total}


if __name__ == "__main__":
    r = run(Path(__file__).resolve().parents[1], Path(sys.argv[1]))
    print(f"кадротека: приложений {r['apps']} · кадров {r['frames']}")
