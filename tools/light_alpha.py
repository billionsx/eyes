#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЗАМЕР ПРОЗРАЧНОСТИ НА СВЕТЛОМ ХОЛСТЕ — обратной задачей.

Прозрачность нельзя увидеть прямо: на кадре лежит уже СМЕШАННОЕ значение.
Но если холст известен точно (а он снят: #FFFFFF и #F2F2F7), то смесь
раскладывается: наблюдаемое = α·тон + (1−α)·холст.

Двух неизвестных на одно уравнение много — поэтому берётся ТРИ канала.
Тон полупрозрачных заливок Apple нейтрально-синеватый и ОДИН на всю
систему; если он верен, α, решённая по трём каналам порознь, обязана
СОЙТИСЬ. Схождение и есть доказательство: подобранный наугад тон даёт
три разные α и отсеивается сам.

Тон берётся из ОПУБЛИКОВАННОЙ палитры (цитата, не замер) — это честно
называется в выводе. Замером здесь является α.

Воспроизведение:  python3 light_alpha.py <каталог кадров>
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
ХОЛСТЫ = {"#FFFFFF": np.array([255.0, 255.0, 255.0]),
          "#F2F2F7": np.array([242.05, 242.05, 246.97])}
# Тоны полупрозрачных заливок и меток iOS — ПУБЛИКАЦИЯ Apple, не замер.
ТОНЫ = {"fill (120,120,128)": np.array([120.0, 120.0, 128.0]),
        "label (60,60,67)": np.array([60.0, 60.0, 67.0]),
        "чёрный (0,0,0)": np.array([0.0, 0.0, 0.0])}


def read(p):
    a = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    if a is None or a.dtype != np.uint16 or a.ndim != 3:
        return None
    a = a[::S, ::S, ::-1]
    v = 255.0 * np.rint((a.astype(np.float64) + 1) / 128.0) / 512.0
    return v[TOP_PT:v.shape[0] - BOT_PT]


def решить(наблюд, холст, тон):
    """α по каждому каналу порознь + разброс между каналами."""
    зн = холст - тон
    если = np.abs(зн) > 1e-6
    if если.sum() < 2:
        return None, None
    a = (холст[если] - наблюд[если]) / зн[если]
    return float(a.mean()), float(a.max() - a.min())


def main():
    найдено = Counter()
    сходимость = []
    кадров = 0
    for p in sorted(SRC.glob("*.PNG")):
        a = read(p)
        if a is None:
            continue
        h, w, _ = a.shape
        край = np.concatenate([a[:, 2:6].reshape(-1, 3), a[:, w-6:w-2].reshape(-1, 3)])
        c = Counter(map(tuple, np.round(край, 3)))
        холст, доля = c.most_common(1)[0]
        if доля / len(край) < 0.5 or max(холст) < 128:
            continue
        бел = [col for col in c if min(col) >= 250 and max(col) - min(col) <= 1]
        if not бел:
            continue
        сдвиг = 255.0 - max(max(b) for b in бел)
        if abs(сдвиг) > 1.0:
            continue
        H = np.array(холст) + сдвиг
        имя = None
        for k, v in ХОЛСТЫ.items():
            if np.abs(H - v).max() <= 1.0:
                имя = k
                break
        if not имя:
            continue
        кадров += 1

        # Крупные ровные заливки поверх этого холста.
        ci = Counter(map(tuple, np.round(a[:, 16:w-16].reshape(-1, 3) + сдвиг, 2)))
        всего = sum(ci.values())
        for col, cnt in ci.most_common(20):
            if cnt / всего < 0.01:
                break
            C = np.array(col)
            if np.abs(C - H).max() < 1.5:      # это сам холст
                continue
            if C.max() > H.max() + 0.6:        # светлее холста — не заливка поверх
                continue
            # ВЫРОЖДЕНИЕ. Над нейтральным холстом нейтральный тон
            # раскладывается при ЛЮБОЙ альфе: три канала пропорциональны, и
            # схождение получается само собой, ничего не доказывая. Задача
            # определена только тогда, когда смесь несёт СЛЕД ТОНА — то есть
            # её синий отклоняется от красного сильнее, чем это делает холст.
            след = abs((C[2] - C[0]) - (H[2] - H[0]))
            if след < 1.0:
                continue
            for тон_имя, T in ТОНЫ.items():
                al, разброс = решить(C, np.array(ХОЛСТЫ[имя]), T)
                if al is None or not (0.02 <= al <= 0.95):
                    continue
                if разброс <= 0.02:            # три канала СОШЛИСЬ
                    найдено[(имя, тон_имя, round(al, 3))] += 1
                    сходимость.append(разброс)

    print(f"кадров с известным холстом: {кадров}\n")
    print("СОШЕДШИЕСЯ РАЗЛОЖЕНИЯ (разброс α по каналам ≤ 0.02):")
    for (хол, тон, al), n in найдено.most_common(25):
        print(f"  холст {хол} · тон {тон:20} · α = {al:.3f}  ×{n}")
    if сходимость:
        print(f"\nвсего разложений: {len(сходимость)} · "
              f"средний разброс по каналам {np.mean(сходимость):.4f}")
    json.dump({"frames": кадров,
               "solved": [{"canvas": k[0], "tint": k[1], "alpha": k[2], "n": v}
                          for k, v in найдено.most_common(40)]},
              open("/tmp/alpha.json", "w"), ensure_ascii=False, indent=1)


main()
