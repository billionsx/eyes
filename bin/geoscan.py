#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ЗАМЕР ГЕОМЕТРИИ ПО КАДРАМ (ст. 36.2, ЗКН-Э002).

Зачем орган существует. В базе iOS 27 семнадцать геометрических значений стоят
дырами «🕳 замерить». Взять их из iOS 26 нельзя — это была бы подмена замера
памятью. Взять из головы нельзя тем более. Единственный честный источник —
кадр экрана: на нём геометрия присутствует физически, в пикселях.

Что орган снимает и чего не снимает. Снимает то, что видно на неподвижном
кадре: масштаб, размер экрана, поверхности (отступ, ширина), радиусы углов,
толщину разделителей, высоту нижней панели. НЕ снимает движение — в кадре нет
времени; для `motion.*` нужна запись экрана, и орган об этом говорит прямо,
а не выдаёт молчание за отсутствие требований.

Правило числа (ЗКН-Э002). Каждое снятое число несёт адрес: имя кадра и
координаты, откуда оно взято. Число без адреса в базу не попадает.

Правило масштаба. Точка (pt) — не пиксель. Масштаб не угадывается по картинке:
он берётся из объявленного канона размеров экранов Apple, и кадр, чья ширина
не сходится ни с одним каноническим произведением pt×scale, ОТВЕРГАЕТСЯ.
Кадр непонятного происхождения хуже отсутствия кадра.

Запуск:  python3 bin/geoscan.py --frames <каталог>   — замер по кадротеке
         python3 bin/geoscan.py --court              — суд, без сети и кадров
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# КАНОН ЭКРАНОВ APPLE (объявлен, не выведен из картинки). Логическая ширина в
# точках для семейств iPhone. Масштаб — 2× или 3×. Кадр принимается, только
# если его ширина в пикселях равна ровно pt × scale для одной пары из канона:
# иначе неизвестно, во что переводить пиксели, и замер будет выдумкой.
SCREEN_PT = (320, 375, 390, 393, 402, 414, 428, 430, 440)
SCALES = (2, 3)

MIN_RUN = 0.40        # доля ширины кадра: короче — не поверхность, а элемент
FLAT_TOL = 10         # допуск «тот же цвет» по каналу, 0..255
CHROMA_MAX = 26       # разброс цвета внутри поверхности: выше — фото/обложка
MIN_SURFACE_PX = 12   # тоньше — это разделитель или кромка, не поверхность
MAX_GAP_PX = 14       # разрыв цвета внутри поверхности: разделитель, не край


def scale_of(width_px: int):
    """Масштаб и ширина экрана в точках по канону. Не сошлось → (None, None).

    Возврат пары, а не догадки: если ширина кадра не равна ни одному
    каноническому pt×scale, орган обязан отказаться от кадра, а не подобрать
    ближайшее (ЗКН-Э001 — отсутствие честнее подмены).
    """
    for s in SCALES:
        for pt in SCREEN_PT:
            if pt * s == width_px:
                return s, pt
    return None, None


def _close(a, b, tol=FLAT_TOL) -> bool:
    return abs(int(a[0]) - int(b[0])) <= tol and abs(int(a[1]) - int(b[1])) <= tol \
        and abs(int(a[2]) - int(b[2])) <= tol


def longest_run(row, tol=FLAT_TOL):
    """Самый длинный отрезок ряда одного цвета → (x0, x1, цвет, длина).

    Именно длиннейший непрерывный отрезок, а не доля ряда: разделитель шириной
    в три пикселя обязан считаться тройкой, а не единицей. Эта строка стоит
    здесь потому, что первая версия органа обрезала его до одного пикселя и
    «намеряла» 0.33pt вместо 1.0pt.
    """
    # Ряд сначала сжимается в отрезки одинакового цвета (это делает numpy за
    # один проход), и только потом отрезки сливаются по правилу допуска.
    # Правило то же самое — «в пределах допуска от цвета начала прогона», —
    # но шагов на порядок меньше: в кадре 1179px цветовых переходов около
    # сотни, а не тысяча с лишним. Без этого замер 195 кадров по три миллиона
    # пикселей занимал почти час и не уложился бы в прогон CI.
    import numpy as np
    a = np.asarray(row, dtype=np.int16)
    if a.ndim == 1:
        a = a.reshape(-1, 1)
    n = len(a)
    if n == 0:
        return (0, -1, None, 0)
    brk = np.nonzero((a[1:] != a[:-1]).any(axis=1))[0] + 1
    starts = np.concatenate(([0], brk))
    ends = np.concatenate((brk - 1, [n - 1]))
    best = (0, -1, None, 0)
    i = 0
    m = len(starts)
    while i < m:
        anchor = a[starts[i]]
        j = i
        while j + 1 < m and int(np.abs(a[starts[j + 1]] - anchor).max()) <= tol:
            j += 1
        x0, x1 = int(starts[i]), int(ends[j])
        ln = x1 - x0 + 1
        if ln > best[3]:
            best = (x0, x1, tuple(int(c) for c in anchor), ln)
        i = j + 1
    return best


def canvas_color(img):
    """Цвет холста: мода по краевой рамке кадра, а не по всему кадру.

    Середина занята содержимым; холст виден по краям. Мода, а не среднее:
    среднее смешало бы холст с элементами и дало бы цвет, которого на экране
    нет ни в одной точке.
    """
    h, w, _ = img.shape
    ring = []
    for y in (0, 1, h - 2, h - 1):
        ring.extend(tuple(int(c) for c in img[y][x]) for x in range(0, w, max(1, w // 64)))
    for x in (0, 1, w - 2, w - 1):
        ring.extend(tuple(int(c) for c in img[y][x]) for y in range(0, h, max(1, h // 64)))
    return Counter(ring).most_common(1)[0][0]


MARGIN_PX = 5         # ширина кромочной полосы, по которой судится ровность


def flat_by_margin(img, y0, y1, x0, x1) -> bool:
    """Ровная ли поверхность — по её КРОМКЕ, а не по всей площади.

    Родословная (04.08.2026). Разброс цвета считался по всей области вместе с
    содержимым. Карточка с надписью давала разброс больше допуска и
    отбраковывалась КАК ФОТОГРАФИЯ. Уцелевали только полосы без текста —
    промежутки между строками высотой 10–30pt, и они попадали в совокупность
    под именем «карточка»: 922 «карточки» на 195 кадров при том, что
    скруглённых среди них нашлось восемь. Мерили промежутки и удивлялись, что
    у них нет радиуса.

    Отличие карточки от фотографии видно на КРОМКЕ: у карточки поля слева и
    справа пусты — текст и картинки не доходят до края, — а у фотографии
    кромка такая же пёстрая, как середина. Тот же приём уже применён к холсту
    (`canvas_color` берёт моду по краевой рамке), здесь он лишь распространён
    на поверхности.
    """
    import numpy as np
    m = max(1, min(MARGIN_PX, (x1 - x0 + 1) // 6))
    left = img[y0:y1 + 1, x0:x0 + m]
    right = img[y0:y1 + 1, max(x0, x1 - m + 1):x1 + 1]
    if left.size == 0 or right.size == 0:
        return False
    band = np.concatenate((left.reshape(-1, 3), right.reshape(-1, 3))).astype(int)
    return bool(band.std(axis=0).max() <= CHROMA_MAX)


def surfaces(img, bg):
    """Поверхности кадра: полосы рядов с одинаковым длинным отрезком цвета.

    Возврат: список словарей y0,y1,x0,x1,color. Фото и обложки отсеиваются по
    разбросу цвета внутри области — у настоящей поверхности он мал.
    """
    h, w, _ = img.shape
    need = int(w * MIN_RUN)
    rows = []
    for y in range(h):
        x0, x1, col, ln = longest_run(img[y])
        rows.append((x0, x1, col, ln) if (ln >= need and col and not _close(col, bg)) else None)
    out, y = [], 0
    while y < h:
        if rows[y] is None:
            y += 1
            continue
        x0, x1, col, _ = rows[y]
        y2 = y
        while True:
            if y2 + 1 < h and rows[y2 + 1] and _close(rows[y2 + 1][2], col):
                y2 += 1
                continue
            # Разрыв цвета не обрывает поверхность, если он тонкий и за ним
            # поверхность продолжается: так выглядит разделитель ВНУТРИ
            # карточки. Без этого допуска карточка распадалась надвое, и
            # разделитель не попадал ни в одну половину — то есть не мерился.
            # КАРТОЧКА КОНЧАЕТСЯ ТАМ, ГДЕ НАЧИНАЕТСЯ ХОЛСТ.
            #
            # Родословная (04.08.2026). Разрыв склеивался, только если он
            # тоньше MAX_GAP_PX = 14px. Разделитель в 1px так склеивался, а
            # СТРОКА ТЕКСТА — нет: при 3× она занимает около 51px, и на ней
            # длинный отрезок цвета карточки короче 40% ширины, то есть ряд
            # выпадал. Карточка рвалась на промежутки между строками: медиана
            # высоты «поверхности» 15pt при том, что карточка в iOS не бывает
            # ниже 44pt. Дальше эти промежутки шли в совокупность под именем
            # «карточка» — 922 штуки на 195 кадров, скруглённых среди них
            # восемь. Мерили щели между строками и удивлялись отсутствию
            # радиуса.
            #
            # Число заменено признаком. Внутри карточки лежит её содержимое —
            # текст, значки, миниатюры; ХОЛСТА там нет. Между двумя карточками
            # холст виден. Поэтому разрыв склеивается, пока в полосе x0..x1 не
            # показался цвет холста, и обрывается, когда показался. Порог
            # остаётся один — предохранитель от склейки всего экрана в одну
            # поверхность: полэкрана.
            k = y2 + 1
            limit = y2 + 1 + h // 2
            while k < h and k < limit and not (rows[k] and _close(rows[k][2], col)):
                seg = img[k][x0:x1 + 1]
                _, _, c2, ln2 = longest_run(seg)
                if c2 is not None and _close(c2, bg) and ln2 >= (x1 - x0 + 1) * MIN_RUN:
                    break                      # показался холст — карточка кончилась
                k += 1
            if k > y2 + 1 and k < h and rows[k] and _close(rows[k][2], col):
                y2 = k
                continue
            break
        if y2 - y + 1 >= MIN_SURFACE_PX:
            if flat_by_margin(img, y, y2, x0, x1):
                xs0 = min(rows[k][0] for k in range(y, y2 + 1) if rows[k])
                xs1 = max(rows[k][1] for k in range(y, y2 + 1) if rows[k])
                out.append({"y0": y, "y1": y2, "x0": xs0, "x1": xs1, "color": col})
        y = y2 + 1
    return out


def corner_radius_px(img, s, bg, side: str = "top"):
    """Радиус угла поверхности по профилю втягивания её левой кромки.

    У прямого угла кромка стоит на месте с первого ряда. У скруглённого она
    втянута и выходит на место через r рядов — это и есть радиус. Меряется по
    левому краю: он не занят полосой прокрутки и реже перекрыт содержимым.

    `side` — с какого конца идти. Оба конца нужны для проверки добротности:
    у настоящей карточки верхние и нижние углы одинаковы, а у ОБЛОМКА
    карточки (её разрезало по цвету содержимого) один конец скруглён, а
    другой прямой. Без этой проверки обломки давали радиус 0 и забивали
    совокупность: 28% «карточек» показывали прямой угол, которого на экране
    нет.
    """
    y0, x0, x1 = (s["y0"], s["x0"], s["x1"]) if side == "top" else (s["y1"], s["x0"], s["x1"])
    col = s["color"]
    depth = min(s["y1"] - s["y0"] + 1, (x1 - x0) // 2, 80)
    if depth < 3:
        return None
    step = 1 if side == "top" else -1
    prof = []
    for d in range(depth):
        row = img[y0 + step * d]
        x = x0
        while x <= x1 and not _close(row[x], col):
            x += 1
        prof.append(x - x0 if x <= x1 else None)
    if prof[0] is None or prof[-1] is None:
        return None
    # Радиус берётся из ВСЕЙ дуги, а не из одной её точки.
    #
    # Почему не из одной. В верхней точке дуги касательная горизонтальна:
    # втянутость там меняется быстрее всего, и сдвиг на треть ряда из-за
    # сглаживания даёт ошибку в несколько пикселей (первая версия так и
    # получила 10.3pt вместо нарисованных 12). В нижней точке касательная
    # вертикальна — там уже втянутость почти не меняется, и шум цвета
    # смещает ответ. Надёжна только дуга целиком.
    #
    # Связь: точка (d, i) лежит на окружности радиуса r с центром (r, r),
    # если (r−i)² + (r−d)² = r². Отсюда r = (i + d) + sqrt(2·i·d).
    # Берётся медиана оценок по всем рядам дуги: она устойчива к выбросам
    # на краях, где сглаживание сильнее всего.
    # ДУГА ДОЛЖНА БЫТЬ ДУГОЙ. Проверка формы, а не только счёт числа.
    #
    # Родословная (04.08.2026). Оценка бралась медианой по всем рядам без
    # проверки, что профиль вообще похож на угол. У нижней кромки карточки
    # часто стоит содержимое — значок или текст с отбивкой от края, — и втяну‑
    # тость там не убывает, а держится. Медиана выдавала числа вроде 138 и
    # 325pt при экране 393pt. Такие концы не отбрасывались как негодные: они
    # шли в сравнение верха с низом, ломали согласие, и 62 карточки из 147
    # вылетали из совокупности радиуса с формулировкой «верх≠низ». Дыра
    # радиуса стояла не из-за нехватки кадров, а из-за негодных чисел,
    # которые выглядели годными.
    #
    # У настоящего угла втянутость МАКСИМАЛЬНА у самой кромки и убывает до
    # нуля. Содержимое такого профиля не даёт. Поэтому:
    #   · профиль обязан убывать (допуск 1px на сглаживание);
    #   · он обязан дойти почти до нуля в пределах просмотра;
    #   · оценки по рядам обязаны сходиться между собой.
    # Не сошлось — возврат None, то есть «не измерено». Отсутствие числа
    # честнее числа неверного (ЗКН-Э001).
    if prof[0] is not None and prof[0] <= 1:
        return 0.0                      # прямой угол: кромка на месте с первого ряда
    seq = [i for i in prof if i is not None]
    if len(seq) < 3:
        return None
    if any(seq[k + 1] > seq[k] + 1 for k in range(len(seq) - 1)):
        return None                     # втянутость растёт — это не угол
    if min(seq) > 1:
        return None                     # до кромки не дошло — просмотра не хватило
    est = []
    for d, i in enumerate(prof):
        if d == 0 or i is None or i <= 0:
            continue
        est.append((i + d) + (2.0 * i * d) ** 0.5)
    if len(est) < 3:
        return None
    est.sort()
    mid = est[len(est) // 2]
    lo, hi = est[len(est) // 4], est[(3 * len(est)) // 4]
    if mid <= 0 or (hi - lo) > 0.5 * mid:
        return None                     # оценки не сходятся — дуге не верим
    return round(mid, 2)


MIN_ROW_PT = 8.0      # ниже — это пара линеек, а не строка списка


def separator_runs(img, s):
    """Разделители внутри поверхности: [(y начала, длина прогона)] в пикселях.

    Возвращается ПОЛОЖЕНИЕ, а не только толщина, потому что положение несёт
    второе число: расстояние между соседними разделителями и есть шаг строки
    списка. Толщину мерили и раньше, а шаг — нет, и семь дыр `rows.*` стояли
    незакрытыми при том, что улика лежала в тех же кадрах.
    """
    col = s["color"]
    half = (s["x1"] - s["x0"] + 1) // 2
    marks = []
    for y in range(s["y0"], s["y1"] + 1):
        seg = img[y][s["x0"]:s["x1"] + 1]
        _, _, c, ln = longest_run(seg)
        marks.append(bool(c and not _close(c, col) and ln >= half))
    out, run, start = [], 0, 0
    for i, m in enumerate(marks):
        if m:
            if not run:
                start = s["y0"] + i
            run += 1
        elif run:
            out.append((start, run))
            run = 0
    if run:
        out.append((start, run))
    return out


def row_pitches_px(img, s):
    """Шаги строк внутри поверхности: расстояния между началами разделителей.

    Порог MIN_ROW_PT объявлен, а не подобран: две линейки, стоящие в пикселе
    друг от друга, — это рамка, а не две строки. Всё, что выше порога, идёт
    в совокупность как есть, и решение о согласии принимает geofill, а не
    этот порог.
    """
    ys = [y for y, _ in separator_runs(img, s)]
    return [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]


def separators_px(img, s):
    """Толщина разделителей внутри поверхности, в пикселях.

    Ряды, чей цвет отличается от цвета поверхности и чей отрезок занимает
    больше половины её ширины. Считается ДЛИНА НЕПРЕРЫВНОГО ПРОГОНА таких
    рядов: три пикселя подряд — это три, а не один.
    """
    return [ln for _, ln in separator_runs(img, s)]


def page_inset_of(recs: list):
    """Отступ СТРАНИЦЫ: самый частый отступ поверхностей кадра.

    Нужен потому, что отступ элемента и отступ страницы — разные вещи, а роль
    обязана считаться от страницы. Возврат None, если частого отступа нет:
    тогда точки отсчёта у кадра просто не существует, и выдумывать её нельзя.
    """
    from collections import Counter
    q = Counter(round(r["inset_pt"] * 2) / 2 for r in recs if r["inset_pt"] > 1.0)
    if not q:
        return None
    v, n = q.most_common(1)[0]
    return v if n >= 2 else None


def role_of(rec: dict, screen_pt_w: int, page_inset=None) -> str:
    """Роль элемента по его собственной геометрии. Объявлена, не угадана.

    Роль нужна потому, что радиус — не одно число на экран. У полосы во всю
    ширину углов нет, у капсулы радиус равен половине высоты и токеном не
    является вовсе, у плитки он свой. Смешивать их в одну совокупность
    значит не получить согласия никогда.
    """
    ins, w, h = rec["inset_pt"], rec["width_pt"], rec["height_pt"]
    r = rec.get("radius_pt")
    if r is not None and h > 0 and abs(r - h / 2) <= max(1.5, h * 0.08):
        return "capsule"
    if ins <= 1.0 and w >= screen_pt_w - 2:
        return "full_bleed"
    # ТОЧКА ОТСЧЁТА — СТРАНИЦА, А НЕ САМ ЭЛЕМЕНТ.
    #
    # Родословная (04.08.2026). Свободная ширина считалась от отступа САМОГО
    # элемента: avail = экран − 2·его_отступ. Отсюда следовало, что ЛЮБОЙ
    # элемент, заполняющий свою строку, объявлялся карточкой, — миниатюра при
    # отступе 103pt считала свободной шириной 187pt и проходила как карточка.
    # Совокупность радиуса карточки набивалась вложенными элементами: она
    # оказалась трёхгорбой не потому, что у карточек разные радиусы, а потому,
    # что в ней лежали не только карточки.
    #
    # Карточка — то, что стоит НА отступе страницы и занимает её ширину.
    # Стоящее глубже — вложенный элемент, и своё имя у него своё.
    if page_inset is None:
        avail = screen_pt_w - 2 * ins          # точки отсчёта нет — старое правило
        return "card" if w >= 0.75 * avail else "tile"
    if ins > page_inset + 1.5:
        return "nested"
    avail = screen_pt_w - 2 * page_inset
    return "card" if w >= 0.75 * avail else "tile"


def measure(path: Path) -> dict:
    """Замер одного кадра. Отказ — со словами о причине, а не молча."""
    try:
        import numpy as np
        from PIL import Image
    except Exception as e:
        return {"frame": path.name, "ok": False, "why": f"нет инструментов: {e}"}
    try:
        im = Image.open(path).convert("RGB")
    except Exception as e:
        return {"frame": path.name, "ok": False, "why": f"кадр не открылся: {e}"}
    arr = np.asarray(im)
    h, w, _ = arr.shape
    scale, pt_w = scale_of(w)
    if scale is None:
        return {"frame": path.name, "ok": False,
                "why": f"ширина {w}px не сходится ни с одним каноном pt×scale"}
    bg = canvas_color(arr)
    surf = surfaces(arr, bg)
    out = {"frame": path.name, "ok": True, "scale": scale,
           "screen_pt": [pt_w, round(h / scale)], "canvas": bg,
           "surfaces": [], "separators_pt": [], "radii_pt": [],
           "rows_pt": [], "bottom_bars_pt": [], "capsules_pt": []}
    for s in surf:
        rec = {"inset_pt": round(s["x0"] / scale, 2),
               "width_pt": round((s["x1"] - s["x0"] + 1) / scale, 2),
               "height_pt": round((s["y1"] - s["y0"] + 1) / scale, 2),
               "at": f"{path.name}:y{s['y0']}-{s['y1']},x{s['x0']}-{s['x1']}"}
        rt = corner_radius_px(arr, s, bg, "top")
        rb = corner_radius_px(arr, s, bg, "bottom")
        if rt is not None and rb is not None:
            if abs(rt - rb) <= max(1.5, 0.08 * max(rt, rb, 1)):
                rec["radius_pt"] = round((rt + rb) / 2 / scale, 2)
                out["radii_pt"].append(rec["radius_pt"])
            else:
                rec["radius_unstable"] = [round(rt / scale, 2), round(rb / scale, 2)]
        elif rt is not None or rb is not None:
            # Один конец негоден (не «прямой», а НЕ ИЗМЕРЕН: у кромки стояло
            # содержимое). Обломок карточки так не проскочит: его срез даёт
            # честный ноль, а ноль — измеренное значение, и тогда сработает
            # сравнение выше. Здесь принимается только случай, когда второго
            # числа нет вовсе.
            good = rt if rt is not None else rb
            rec["radius_pt"] = round(good / scale, 2)
            rec["radius_one_end"] = "верх" if rt is not None else "низ"
            out["radii_pt"].append(rec["radius_pt"])
        out["surfaces"].append(rec)
        rec["_s"] = s
    # Роли назначаются ПОСЛЕ обхода: отступ страницы виден только по всем
    # поверхностям кадра, а роль считается от него.
    pin = page_inset_of(out["surfaces"])
    out["page_inset_pt"] = pin
    for rec in out["surfaces"]:
        rec["role"] = role_of(rec, pt_w, pin)
    for rec in out["surfaces"]:
        s = rec.pop("_s")
        for t in separators_px(arr, s):
            out["separators_pt"].append(round(t / scale, 2))
        for d in row_pitches_px(arr, s):
            v = round(d / scale, 2)
            if v >= MIN_ROW_PT:
                out["rows_pt"].append(v)
        # Нижняя панель: поверхность, ДОХОДЯЩАЯ до низа кадра. Признак
        # объявлен геометрией, а не догадкой по цвету или содержимому.
        if s["y1"] >= h - 2 and rec["width_pt"] >= 0.9 * pt_w:
            out["bottom_bars_pt"].append(rec["height_pt"])
        if rec.get("role") == "capsule":
            out["capsules_pt"].append(rec["height_pt"])
    return out


# ─────────────────────────────── суд ───────────────────────────────
def _draw_reference(path: Path, scale: int = 3, pt_w: int = 393, pt_h: int = 852,
                    inset_pt: int = 16, radius_pt: int = 12, sep_pt: float = 1.0):
    """Эталон с НАРИСОВАННОЙ геометрией: орган обязан вернуть ровно её."""
    from PIL import Image, ImageDraw
    W, H = pt_w * scale, pt_h * scale
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, x1 = inset_pt * scale, W - inset_pt * scale - 1
    y0, y1 = 200, 200 + 240 * scale
    d.rounded_rectangle([x0, y0, x1, y1], radius=radius_pt * scale, fill=(28, 28, 30))
    t = max(1, int(round(sep_pt * scale)))
    ys = y0 + 120 * scale
    d.rectangle([x0 + 8, ys, x1 - 8, ys + t - 1], fill=(84, 84, 88))
    im.save(path)
    return {"scale": scale, "screen_pt": [pt_w, pt_h], "inset_pt": inset_pt,
            "width_pt": pt_w - 2 * inset_pt, "radius_pt": radius_pt,
            "sep_px": t, "sep_pt": round(t / scale, 2)}


def court() -> int:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  ✓ " if cond else "  ✗ ") + name)
        ok = ok and cond

    print("СУД · замер геометрии (эталон рисуется на месте, без сети)")
    check("масштаб по канону: 1179px → 3× и 393pt", scale_of(1179) == (3, 393))
    check("масштаб по канону: 750px → 2× и 375pt", scale_of(750) == (2, 375))
    check("ломаю → красный: ширина не из канона отвергается, а не подгоняется",
          scale_of(1000) == (None, None))

    row = [(0, 0, 0)] * 10 + [(84, 84, 88)] * 3 + [(0, 0, 0)] * 4
    x0, x1, c, ln = longest_run(row)
    check("длиннейший прогон найден: чёрный 10", (x0, ln) == (0, 10))
    row2 = [(84, 84, 88)] * 3 + [(0, 0, 0)] * 2
    check("прогон в три пикселя считается тройкой, а не единицей",
          longest_run(row2)[3] == 3)

    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="eyes-geo-"))
    try:
        want = _draw_reference(tmp / "ref.png")
        r = measure(tmp / "ref.png")
        check("эталон принят, масштаб и экран сняты точно",
              r["ok"] and r["scale"] == want["scale"] and r["screen_pt"] == want["screen_pt"])
        s = max(r["surfaces"], key=lambda z: z["height_pt"]) if r["surfaces"] else None
        check("поверхность найдена", s is not None)
        if s:
            check(f"отступ снят точно: нарисовано {want['inset_pt']}pt, снято {s['inset_pt']}pt",
                  abs(s["inset_pt"] - want["inset_pt"]) <= 0.34)
            check(f"ширина снята точно: нарисовано {want['width_pt']}pt, снято {s['width_pt']}pt",
                  abs(s["width_pt"] - want["width_pt"]) <= 0.67)
            check(f"радиус снят точно: нарисовано {want['radius_pt']}pt, снято {s.get('radius_pt')}pt",
                  s.get("radius_pt") is not None
                  and abs(s["radius_pt"] - want["radius_pt"]) <= 1.0)
        check(f"разделитель снят точно: нарисовано {want['sep_pt']}pt, снято {r['separators_pt']}",
              any(abs(t - want["sep_pt"]) <= 0.34 for t in r["separators_pt"]))

        want2 = _draw_reference(tmp / "ref2.png", inset_pt=24, radius_pt=24, sep_pt=2.0)
        r2 = measure(tmp / "ref2.png")
        s2 = max(r2["surfaces"], key=lambda z: z["height_pt"]) if r2["surfaces"] else None
        check("чиню → зелёный: другая нарисованная геометрия даёт другие числа",
              s2 is not None and abs(s2["inset_pt"] - 24) <= 0.34
              and any(abs(t - 2.0) <= 0.34 for t in r2["separators_pt"]))
        check("подмена ловится: 16pt и 24pt не путаются между собой",
              s is not None and s2 is not None and abs(s["inset_pt"] - s2["inset_pt"]) > 5)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames")
    ap.add_argument("--out")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()
    if not a.frames:
        print("нечего мерить: не задан --frames")
        return 1
    files = sorted(p for p in Path(a.frames).rglob("*")
                   if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if a.limit:
        files = files[:a.limit]
    res, bad = [], Counter()
    for f in files:
        m = measure(f)
        (res.append(m) if m.get("ok") else bad.update([m.get("why", "?")[:60]]))
    # ПРИЧИНЫ ОТКАЗА СОХРАНЯЮТСЯ, А НЕ ТОЛЬКО ПЕЧАТАЮТСЯ.
    #
    # Родословная (05.08.2026). Замерщик прочитал 50 добытых кадров и не принял
    # НИ ОДНОГО. Причины он назвал — в журнал прогона, который департаменту
    # недоступен. Наружу вышел пустой список, неотличимый от «кадров не было».
    # Полдня ушло на то, чтобы узнать у собственного органа то, что он уже знал.
    #
    # Причина отказа — такая же улика, как принятый замер, и живёт рядом с ним.
    print(f"замер: кадров {len(files)} · принято {len(res)} · отвергнуто {sum(bad.values())}")
    for why, n in bad.most_common(6):
        print(f"  отвергнуто {n}×: {why}")
    for why, n in bad.most_common(3):
        print(f"  отвергнуто {n}: {why}")
    if a.out:
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        Path(str(a.out) + ".rejected.json").write_text(json.dumps(
            {"files": len(files), "accepted": len(res),
             "rejected": sum(bad.values()),
             "reasons": dict(bad.most_common())},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"замеры записаны: {a.out}")
    if files and not res:
        # Прочитал всё и не принял ничего — это отказ ОРГАНА, а не свойство
        # кадров. Молчаливый ноль здесь означал бы, что департамент объявил
        # свою слепоту отсутствием предмета (ЗКН-Э001).
        print("::error::замерщик прочитал все кадры и НЕ ПРИНЯЛ НИ ОДНОГО — "
              "это отказ органа, а не отсутствие кадров")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
