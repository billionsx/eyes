#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЗАМЕР СВЕТЛОЙ ОСИ по всему корпусу. Точное 16-битное чтение, покадровая
привязка к собственному белому, перевод Display P3 → sRGB матрицами.

Воспроизведение:
    python3 light_full.py <каталог кадров>
"""
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "white")
S = 3
TOP_PT, BOT_PT = 62, 40

M_SRGB = np.array([[0.4123908, 0.3575843, 0.1804808],
                   [0.2126390, 0.7151687, 0.0721923],
                   [0.0193308, 0.1191948, 0.9505322]])
M_P3 = np.array([[0.4865709, 0.2656677, 0.1982173],
                 [0.2289746, 0.6917385, 0.0792869],
                 [0.0000000, 0.0451134, 1.0439444]])
P3_TO_SRGB = np.linalg.inv(M_SRGB) @ M_P3


def lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def enc(l):
    l = np.clip(np.asarray(l, float), 0, 1)
    return 255 * np.where(l <= 0.0031308, l * 12.92,
                          1.055 * l ** (1 / 2.4) - 0.055)


def p3_to_srgb(v):
    return enc(P3_TO_SRGB @ lin(np.asarray(v, float) / 255.0))


def read(p):
    """Кадр в точных долях P3 0..255, каждый третий пиксель (логическая точка)."""
    a = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    if a is None or a.dtype != np.uint16 or a.ndim != 3:
        return None
    a = a[::S, ::S, ::-1]                       # BGR → RGB
    k = np.rint((a.astype(np.float64) + 1) / 128.0)   # 9-битная ступень
    v = 255.0 * k / 512.0
    return v[TOP_PT:v.shape[0] - BOT_PT]


def key(v):
    return tuple(np.round(v, 3))


def main():
    files = sorted(SRC.glob("*.PNG"))
    поля, внутри, любые = Counter(), Counter(), Counter()
    n, тёмных, шумных = 0, 0, 0
    for p in files:
        a = read(p)
        if a is None:
            continue
        h, w, _ = a.shape
        край = np.concatenate([a[:, 2:6].reshape(-1, 3),
                               a[:, w - 6:w - 2].reshape(-1, 3)])
        c = Counter(map(key, край))
        холст, доля = c.most_common(1)[0]
        if доля / len(край) < 0.5:
            шумных += 1
            continue
        if max(холст) < 128:
            тёмных += 1
            continue
        # Опора кадра: белый известен точно (#FFFFFF). Кодировщик кладёт его
        # то на ступень 512 (255.00), то на 511 (254.50) — сдвиг всего кадра.
        бел = [col for col in c if min(col) >= 250 and max(col) - min(col) <= 1]
        if not бел:
            continue
        сдвиг = 255.0 - max(max(b) for b in бел)
        if abs(сдвиг) > 1.0:
            continue
        n += 1
        поля[key(np.array(холст) + сдвиг)] += 1

        ci = Counter(map(key, a[:, 16:w - 16].reshape(-1, 3)))
        всего = sum(ci.values())
        взял = False
        for col, cnt in ci.most_common(12):
            col2 = key(np.array(col) + сдвиг)
            if cnt / всего >= 0.03 and max(col2) >= 128:
                любые[col2] += 1
                if not взял and col2 != key(np.array(холст) + сдвиг):
                    внутри[col2] += 1
                    взял = True

    print(f"светлых кадров в замере: {n} · тёмных отсеяно: {тёмных} · "
          f"неоднородных полей: {шумных} · всего файлов: {len(files)}\n")

    def показать(имя, счёт, k=8):
        print(f"{имя}:")
        строки = []
        for col, cnt in счёт.most_common(k):
            s = p3_to_srgb(col)
            snap = np.rint(s)
            ост = float(np.max(np.abs(s - snap)))
            hx = "#%02X%02X%02X" % tuple(int(x) for x in np.clip(snap, 0, 255))
            print(f"  {hx}  ×{cnt:4} ({100*cnt/n:4.1f}%)  "
                  f"sRGB ({s[0]:6.2f},{s[1]:6.2f},{s[2]:6.2f})  остаток {ост:.2f}")
            строки.append({"hex": hx, "frames": cnt,
                           "srgb": [round(float(x), 2) for x in s],
                           "residual": round(ост, 3)})
        print()
        return строки

    out = {"frames": n,
           "canvas": показать("ХОЛСТ (боковые поля)", поля),
           "card": показать("КАРТОЧКА НА ХОЛСТЕ (≥3% площади, ≠ холст)", внутри),
           "any": показать("ВСЕ КРУПНЫЕ ЗАЛИВКИ (≥3% площади)", любые, 12)}
    json.dump(out, open("/tmp/light_full.json", "w"), ensure_ascii=False, indent=1)


main()
