#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЗАМЕР ГЛУБИНЫ НА СВЕТЛОМ ХОЛСТЕ.

Вопрос, на который отвечает замер: отделяет ли Apple карточку от светлого
холста ТЕНЬЮ — или только ступенью поверхности, как в тёмной теме.

Метод. Тень видна не на карточке, а НА ХОЛСТЕ РЯДОМ С НЕЙ: если она есть,
холст у самой границы темнее, чем тот же холст вдали, и темнота спадает
плавно. Если тени нет, переход ступенчатый: холст ровен вплоть до границы.

Поэтому: находим переходы холст↔карточка по вертикали (верхние и нижние
кромки карточек — там тень видна лучше всего), и снимаем профиль ХОЛСТА
наружу от кромки на 1..14 pt. Сравниваем со значением холста вдали (20..30 pt).
Углы и скругления в замер не идут: берутся только столбцы, где переход
чистый — один шаг между двумя ровными участками.

Воспроизведение:  python3 light_depth.py <каталог кадров>
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "white")
S = 3
TOP_PT, BOT_PT = 62, 40
OUT = 14          # насколько далеко наружу смотрим
FAR = (20, 30)    # где холст считается «вдали»
FLAT = 6          # сколько ровных точек требуется по обе стороны кромки


def read(p):
    a = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    if a is None or a.dtype != np.uint16 or a.ndim != 3:
        return None
    a = a[::S, ::S, ::-1]
    v = 255.0 * np.rint((a.astype(np.float64) + 1) / 128.0) / 512.0
    return v[TOP_PT:v.shape[0] - BOT_PT]


def main():
    профиль = defaultdict(list)
    кромок = 0
    кадров = 0
    пары = Counter()
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
        кадров += 1
        H = np.array(холст)

        # серое расстояние до холста по каждому пикселю
        d = np.abs(a - H).max(axis=2)
        холстовый = d <= 0.6           # пиксель равен холсту

        взято = 0
        for x in range(int(w * 0.2), int(w * 0.8), 5):
            col = холстовый[:, x]
            for y in range(FAR[1] + OUT + 2, h - FAR[1] - OUT - 2):
                # кромка ХОЛСТ→не холст, идём сверху вниз
                if not (col[y] and not col[y + 1]):
                    continue
                # выше кромки холст обязан быть ровным
                if not col[y - FLAT:y + 1].all():
                    continue
                # ниже кромки — ровная НЕ холстовая заливка (карточка)
                низ = a[y + 2:y + 2 + FLAT, x]
                if низ.max() - низ.min() > 1.5:
                    continue
                далеко = a[y - FAR[1]:y - FAR[0], x].mean(axis=0)
                if np.abs(далеко - H).max() > 0.6:
                    continue
                # Кромка должна быть КРОМКОЙ СТУПЕНИ, а не строкой текста и
                # не разделителем: заливка под ней обязана быть светлой
                # поверхностью и отличаться от холста заметно, но не быть
                # содержимым (чёрный текст, картинка, кнопка).
                K = низ.mean(axis=0)
                разн = float(np.abs(K - H).max())
                if разн < 3.0 or min(K) < 200:
                    continue
                for k in range(0, OUT + 1):
                    профиль[k].append(float(a[y - k, x].mean() - далеко.mean()))
                пары[(tuple(np.round(H + сдвиг, 2)),
                      tuple(np.round(низ.mean(axis=0) + сдвиг, 2)))] += 1
                кромок += 1
                взято += 1
                break
            if взято > 60:
                break

    print(f"кадров: {кадров} · чистых кромок холст→карточка: {кромок}\n")
    print("ПРОФИЛЬ ХОЛСТА НАРУЖУ ОТ КРОМКИ (отклонение от холста вдали, в единицах 0..255):")
    итог = {}
    for k in range(0, OUT + 1):
        v = профиль.get(k, [])
        if not v:
            continue
        m = float(np.mean(v))
        med = float(np.median(v))
        итог[k] = {"mean": round(m, 3), "median": round(med, 3), "n": len(v)}
        полоса = "█" * int(min(abs(m) * 6, 40))
        print(f"  {k:2} pt от кромки: среднее {m:+7.3f} · медиана {med:+7.3f} "
              f"· замеров {len(v):5}  {полоса}")
    print("\nЧАСТЫЕ ПАРЫ холст → карточка:")
    for (H, K), n in пары.most_common(6):
        print(f"  {H} → {K}  ×{n}")
    json.dump({"frames": кадров, "edges": кромок, "profile": итог},
              open("/tmp/depth.json", "w"), ensure_ascii=False, indent=1)


main()
