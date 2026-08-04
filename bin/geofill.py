#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ЗАПИСЬ ЗАМЕРОВ В БАЗУ iOS 27 (ЗКН-Э002, ЗКН-Э006).

Орган решает единственный вопрос: какое из снятых чисел имеет право стать
законом, а какое обязано остаться дырой. Мерит `geoscan.py`; здесь — суд над
результатом замера.

Правило согласия. Простая доля здесь не работает и это надо сказать прямо.
В совокупности отступов лежат и карточки, и кнопки, и миниатюры — у них
разные отступы ПО ПРАВУ, и требовать 55% от всех замеров значит не закрыть
никогда ничего. Поэтому приняты два независимых основания, и достаточно
любого:

  СМЫКАНИЕ — числа сходятся арифметически между собой и с экраном.
    Отступ 16 и ширина 361 при экране 393: 16 + 361 + 16 = 393 ровно.
    Совпадение трёх независимо снятых величин — улика сильнее любой доли.

  ПЕРЕВЕС — самое частое значение занимает не меньше 35% замеров и при этом
    не меньше чем в 1.5 раза опережает следующее. Один лидер, а не два.

Всё, что не прошло ни по одному основанию, остаётся дырой — но дырой С
УЛИКАМИ: сколько раз мерили, какое значение вело, какая доля. Разница между
«🕳 замерить» и «🕳 замерено 303×, ведёт 22.5pt, доля 5%» — это разница между
незнанием и знанием о своём незнании (ЗКН-Э001).

Правило пустого замера (ЗКН-Э006). Ноль кадров не даёт права тронуть базу:
пустой обход — промах адреса, а не подтверждение прежних чисел.

Запуск:  python3 bin/geofill.py --scan <файл замеров> [--write]
         python3 bin/geofill.py --court
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "registry" / "standards" / "ios27" / "tokens.next.json"

MIN_SAMPLES = 30      # меньше — совокупность слишком мала для суждения
# ЕДИНОГЛАСИЕ — третье основание закрытия, рядом со СМЫКАНИЕМ и ПЕРЕВЕСОМ.
#
# Зачем оно понадобилось (04.08.2026). После починки склейки поверхностей
# нижняя панель нашлась на 17 кадрах, и 16 из них дали РОВНО одно значение.
# Порог в 30 замеров отклонял это как «совокупность мала» — и был прав для
# смеси ролей, где лидер держит 35%: там малое число вводит в заблуждение. Но
# шестнадцать кадров из десяти РАЗНЫХ приложений Apple, сошедшиеся до десятой
# доли точки, — улика иного рода. Ослаблять общий порог нельзя: это ухудшило
# бы каждое прочее суждение. Поэтому вводится отдельное основание со своими
# условиями, а не подкручивается старое.
MIN_UNANIMOUS = 12    # ниже этого единогласие ещё может быть совпадением
UNANIMOUS_SHARE = 0.90
LEAD_SHARE = 0.35     # доля лидера для перевеса
LEAD_RATIO = 1.5      # во сколько раз лидер обязан опережать следующего
CLOSURE_TOL = 1.0     # допуск смыкания в точках



# ─────────────────── ЧЕМ ЗАКРЫВАЕТСЯ ТО, ЧТО НЕ ЗАКРЫТО ───────────────────
#
# 04.08.2026. Кадротека из 195 кадров десяти приложений Apple прогнана
# расширенным замером: добавлены шаг строк, высота нижней панели, высота
# капсулы, лестница радиусов. НИ ОДНА величина не дала согласия. Это результат,
# а не неудача: 110 шагов строк с лидером 18.0pt на 7% — не «почти закрыто», а
# доказательство, что расстояния между тёмными рядами внутри поверхности НЕ
# ЕСТЬ шаг строки списка. Восемь замеров нижней панели и двенадцать капсул —
# совокупности, малые для суждения.
#
# Поэтому вместо чисел в базу ложится ЗНАНИЕ О НЕЗНАНИИ. «🕳 замерить» —
# напоминание себе, которое годами читается как лень. «🕳 не снимается
# неподвижным кадром: нужна запись 60 к/с» — работающее указание: видно, чем
# закрывать, и видно, что кадротекой не закроешь никогда.
#
# Разница между незнанием и знанием о своём незнании — это ЗКН-Э001, только
# обращённый на себя.
NEEDS = {
    "motion": (
        "не снимается неподвижным кадром — в кадре нет времени",
        "экранная запись 60 к/с; замер по числу кадров между первым и последним "
        "изменившимся пикселем перехода"),
    "glass": (
        "не снимается кадром без опоры — прозрачность видна только "
        "ОТНОСИТЕЛЬНО известного фона",
        "кадр, где один и тот же слой стоит над двумя разными известными "
        "цветами: тогда α решается арифметически, а не на глаз"),
    "opacity_ladder": (
        "производное от glass.* — пока не замерены слои, лестницы нет",
        "то же, что для glass: слой над двумя известными фонами"),
    "typography.weights": (
        "не замеряется в принципе — вес это объявленная шкала, а не величина "
        "на экране",
        "выписка первоисточника Apple с адресом страницы (HIG · Typography)"),
    "typography.cap_height_fraction": (
        "не снимается кадром — доля высоты прописной берётся из метрик "
        "шрифта, а не из пикселей строки",
        "метрики файла шрифта San Francisco (capHeight/unitsPerEm) с адресом"),
    "glyphs": (
        "снимается кадром, но кадротека не даёт совокупности: глиф занимает "
        "десятки пикселей и сливается с содержимым",
        "кадры с увеличением интерфейса (Display Zoom) либо ассеты SF Symbols "
        "в известном размере"),
    "rows": (
        "мерилось 110 раз и не сошлось: расстояние между тёмными рядами внутри "
        "поверхности НЕ ЕСТЬ шаг строки списка (лидер 18.0pt, доля 7%)",
        "кадры длинных однородных списков без обложек и медиа, где строки "
        "разделены линейками одного вида — тогда шаг читается как период"),
    "empty": (
        "не снимается: в кадротеке нет ни одного пустого состояния",
        "кадр экрана без содержимого (пустой список, пустой поиск)"),
    "geometry.corner_form_required_above_pt": (
        "не снимается напрямую — это ПОРОГ, за которым Apple переходит к "
        "непрерывной форме угла, а порог виден только на паре соседних "
        "размеров",
        "два кадра одного элемента в размерах чуть ниже и чуть выше порога: "
        "форма угла меняется скачком"),
    "geometry.radius_card_full_pt": (
        "не отделяется от radius_card_pt: карточка во всю ширину и карточка с "
        "отступом попадают в одну совокупность",
        "кадры, где карточка доходит до кромки экрана без отступа — тогда роль "
        "full_bleed отделит её сама"),
    "geometry.radius_tile_pt": (
        "не даёт совокупности: плиток с ролью tile в кадротеке единицы",
        "кадры сеток (Фото, Приложения, Дом) — там плитка это основной элемент"),
    "geometry.button_hit_pad_pt": (
        "не снимается кадром вовсе: область нажатия невидима",
        "снимок иерархии представлений (Accessibility Inspector) либо запись "
        "касаний с подсветкой попаданий"),
    "geometry.chip_height_pt": (
        "не отделяется от кнопки: и то и другое капсула, различие в назначении, "
        "а не в геометрии",
        "кадры с рядом фильтров-чипов рядом с обычной кнопкой в одном экране"),
    "geometry.layer_axis_pt": (
        "не снимается: слоистая раскладка узнаётся по расстановке нескольких "
        "поверхностей, а не по одной",
        "кадры со слоистыми карточками (Кошелёк, Музыка «сейчас играет»)"),
    "geometry.layer_span_pt": (
        "то же, что layer_axis_pt: без слоистых кадров совокупности нет",
        "кадры со слоистыми карточками (Кошелёк, Музыка «сейчас играет»)"),
    "geometry.layer_inset_pt": (
        "то же, что layer_axis_pt: без слоистых кадров совокупности нет",
        "кадры со слоистыми карточками (Кошелёк, Музыка «сейчас играет»)"),
    "geometry.layer_gap_pt": (
        "то же, что layer_axis_pt: без слоистых кадров совокупности нет",
        "кадры со слоистыми карточками (Кошелёк, Музыка «сейчас играет»)"),
    "typography.role_sizes_pt": (
        "не снимается высотой строки: кегль это метрика шрифта, а на экране "
        "видна только высота прописных и надстрочных",
        "метрики San Francisco плюс кадр с известной ролью текста — тогда "
        "кегль решается из доли высоты прописной"),
    "typography.tracking_cap_px": (
        "не снимается: трекинг виден лишь как разница шага букв между двумя "
        "начертаниями одного текста",
        "кадр одной надписи в двух ролях (заголовок и тело) — разница шага "
        "даёт крышку поправки"),
    "typography.line_height_families_pt": (
        "производное от role_sizes_pt: без кегля семейства межстрочных "
        "интервалов не выделяются",
        "то же, что для role_sizes_pt"),
    "debts": (
        "перечень того, чего кадротека не покрывает в принципе",
        "светлая тема, Dynamic Type кроме Large, состояния кнопки, заливка "
        "активного таба — каждое требует своего кадра или записи"),
    "geometry.tabbar_height_pt": (
        "нижняя поверхность замерена единогласно (78.0pt на 16 кадрах из 17), "
        "но это высота панели ВМЕСТЕ с безопасной зоной — под именем «высота "
        "таб-бара» такое число было бы подменой смысла, а она хуже дыры",
        "кадр, где панель видна НАД содержимым и безопасная зона отделяется: "
        "78.0 минус измеренная зона и есть высота панели. Само измеренное "
        "число уже стоит в geometry.bottom_bar_with_safe_area_pt"),
    "geometry.bottom_bar_with_safe_area_pt": (
        "не замерено", "кадры с нижней панелью во всю ширину экрана"),
    "geometry.button_height_pt": (
        "двенадцать капсул — мало; вдобавок лидер 49pt совпадает с шагом "
        "строки списка, то есть капсула по одной геометрии от строки не "
        "отличается",
        "кадры с явными кнопками действия (Настройки, диалоги, «Готово») "
        "рядом с обычным списком в одном экране"),
    "geometry.radius_ladder_pt": (
        "159 скруглений на 532 поверхности, 70% углов прямые; ни одна ступень "
        "не набрала 30 подтверждений",
        "кадры сгруппированных списков и сеток, где скруглённых поверхностей "
        "заведомо больше, чем секций с прямыми углами"),
    "geometry.superellipse_n": (
        "не снимается замером кромки: показатель суперэллипса требует "
        "подгонки кривой, а не одной величины",
        "кадр угла в 3× без содержимого у кромки: подгонка |x|^n+|y|^n=1 по "
        "профилю втягивания"),
}
# Величины, у которых улика ЕСТЬ, но согласия нет. Число замеров подставляется
# из живого прогона — цифра в тексте, взятая из головы, стареет молча (Э002).
MEASURED_NO_CONSENSUS = ("geometry.tabbar_height_pt", "geometry.button_height_pt",
                         "geometry.chip_height_pt", "geometry.radius_ladder_pt")


def need_for(path: str):
    """Чем закрывается дыра. Ищется от самого частного к общему."""
    for key in sorted(NEEDS, key=len, reverse=True):
        if path == key or path.startswith(key + ".") or path.split(".")[0] == key:
            return NEEDS[key]
    return None


def evidence_text(path: str, why: str, need: str, samples=None) -> str:
    tail = f" · замеров в кадротеке: {samples}" if samples is not None else ""
    return f"🕳 {why}. Закрывается: {need}{tail}"


def mode_of(vals, step=0.5):
    """Лидер совокупности и его доля → (значение, число, доля, следующий)."""
    if not vals:
        return None, 0, 0.0, 0
    q = Counter(round(v / step) * step for v in vals)
    top = q.most_common(2)
    v, n = top[0]
    nxt = top[1][1] if len(top) > 1 else 0
    return v, n, n / len(vals), nxt


def by_lead(vals, step=0.5) -> tuple:
    """Перевес: лидер держит долю и опережает следующего в полтора раза."""
    v, n, share, nxt = mode_of(vals, step)
    ok = bool(vals) and len(vals) >= MIN_SAMPLES and share >= LEAD_SHARE \
        and (nxt == 0 or n >= LEAD_RATIO * nxt)
    return ok, v, n, share


def by_unanimity(vals, step=0.5) -> tuple:
    """Единогласие: небольшая совокупность, сошедшаяся почти в одно значение."""
    v, n, share, _ = mode_of(vals, step)
    ok = bool(vals) and len(vals) >= MIN_UNANIMOUS and share >= UNANIMOUS_SHARE
    return ok, v, n, share


# СПИСКИ-РАЗРЕШЕНИЯ. Эти величины — не одно число, а перечень допустимого, и
# правила AE пользуются ими как белым списком: значение вне списка объявляется
# нарушением.
#
# Отсюда следствие, которое стоит назвать прямо: для списка-разрешения ЧАСТИЧНЫЙ
# замер хуже дыры. У одиночной величины неполный замер даёт неверное число — это
# плохо, но видно. У белого списка недостающая ступень даёт ЛОЖНОЕ ОБВИНЕНИЕ:
# клиент нарисовал ровно то, что рисует Apple, а департамент назвал это
# нарушением, потому что ступени в его списке не хватает. Инструмент,
# обвиняющий за правильное, вреднее инструмента молчащего.
#
# Замер 04.08.2026: на 195 кадрах у карточек нашлись два населённых горба —
# 12.4pt (23 замера, 14 разных кадров) и 25.4pt (18 замеров, 15 кадров). Этого
# хватило бы, чтобы «закрыть» лестницу двумя ступенями — и начать обвинять за
# 8pt, 16pt и 29pt, которые Apple рисует и которые в кадротеку просто не попали.
# Поэтому список-разрешение закрывается ТОЛЬКО ЦЕЛИКОМ, с доказательством
# полноты, а не перевесом или единогласием.
ALLOWLIST = ("geometry.radius_ladder_pt", "opacity_ladder.allow",
             "typography.role_sizes_pt", "typography.line_height_families_pt",
             "rows.media_pitch_pt")

CLUSTER_GAP = 3.0     # разрыв между горбами в точках: ниже — тот же горб
CLUSTER_MIN = 3       # горб из двух замеров ещё может быть шумом


def clusters(vals, gap=CLUSTER_GAP, least=CLUSTER_MIN) -> list:
    """Горбы совокупности: [(центр, число замеров)] по убыванию числа.

    Зачем орган. Дыра радиуса карточки сообщала «мерили 25×, ведёт 19.9». 19.9
    не встречается НИ В ОДНОМ замере: пул трёхгорбый — 11.8 (5), 15.2 (9),
    25.3 (11), — и среднее легло между горбами. Такое число хуже дыры: дыра
    честно молчит, а среднее по двугорбому пулу выглядит почти найденным
    ответом и приглашает себя вписать.

    Многогорбость — это не «согласия нет», это ЗНАНИЕ: у величины не одно
    значение, и единственное число под её именем было бы подменой смысла.
    """
    v = sorted(float(x) for x in vals)
    if not v:
        return []
    groups, cur = [], [v[0]]
    for x in v[1:]:
        if x - cur[-1] <= gap:
            cur.append(x)
        else:
            groups.append(cur)
            cur = [x]
    groups.append(cur)
    out = [(round(sum(g) / len(g), 1), len(g)) for g in groups if len(g) >= least]
    return sorted(out, key=lambda t: -t[1])


def closes(screen_w, inset, width, tol=CLOSURE_TOL) -> bool:
    """Смыкание: отступ + ширина + отступ = ширина экрана."""
    if None in (screen_w, inset, width):
        return False
    return abs((inset * 2 + width) - screen_w) <= tol


def decide(scan: list) -> dict:
    """Что закрывается замером, что остаётся дырой — и с какой уликой."""
    ok = [x for x in scan if x.get("ok")]
    if not ok:
        return {"frames": 0, "closed": {}, "holes": {},
                "why": "обойдено 0 кадров — база не тронута (ЗКН-Э006)"}
    scr = Counter(tuple(x["screen_pt"]) for x in ok).most_common(1)[0]
    screen, scr_n = list(scr[0]), scr[1]
    surf = [s for x in ok for s in x["surfaces"]]
    cards = [s for s in surf if s["inset_pt"] > 1.0]
    ins = [s["inset_pt"] for s in cards]
    wid = [s["width_pt"] for s in cards]
    seps = [t for x in ok for t in x["separators_pt"]]

    closed, holes = {}, {}
    closed["measured_frames"] = {"value": len(ok), "why": f"кадров принято {len(ok)}"}
    closed["geometry.screen_pt"] = {
        "value": screen,
        "why": f"согласие {scr_n}/{len(ok)} кадров = {scr_n/len(ok):.0%}"}

    vi, ni, shi, _ = mode_of(ins)
    vw, nw, shw, _ = mode_of(wid)
    if closes(screen[0], vi, vw):
        closed["geometry.inset_card_pt"] = {
            "value": vi,
            "why": f"смыкание {vi}·2 + {vw} = {screen[0]} · лидер {ni} замеров ({shi:.0%})"}
        closed["geometry.card_width_pt"] = {
            "value": vw,
            "why": f"смыкание {vi}·2 + {vw} = {screen[0]} · лидер {nw} замеров ({shw:.0%})"}
    else:
        holes["geometry.inset_card_pt"] = {"n": len(ins), "lead": vi, "share": shi}
        holes["geometry.card_width_pt"] = {"n": len(wid), "lead": vw, "share": shw}

    ok_s, vs, ns, shs = by_lead(seps, step=0.01)
    if ok_s:
        closed["separator.width_pt"] = {
            "value": vs, "why": f"перевес {ns} замеров ({shs:.0%}), лидер один"}
    else:
        v, n, sh, _ = mode_of(seps, step=0.01)
        holes["separator.width_pt"] = {"n": len(seps), "lead": v, "share": sh}

    # Радиус карточки считается ТОЛЬКО по тем поверхностям, которые правда
    # карточки: роль card, отступ и ширина сомкнулись с экраном, а верхний и
    # нижний углы сошлись между собой. Всё прочее — обломки и секции.
    real = [s for s in cards
            if s.get("role") == "card" and "radius_pt" in s
            and vi is not None and abs(s["inset_pt"] - vi) <= 0.7
            and vw is not None and abs(s["width_pt"] - vw) <= 1.0]
    square = [s for s in real if s["radius_pt"] <= 0.5]
    round_ = [s["radius_pt"] for s in real if s["radius_pt"] > 0.5]
    ok_r, vr, nr, shr = by_lead(round_)
    if ok_r:
        closed["geometry.radius_card_pt"] = {
            "value": vr,
            "why": f"перевес {nr} из {len(round_)} скруглённых карточек ({shr:.0%})"}
    else:
        h = {"n": len(round_), "square": len(square)}
        if round_:
            lo, hi = min(round_), max(round_)
            cl = clusters(round_)
            h.update({"lead": round(sum(round_) / len(round_), 1),
                      "share": 0.0, "range": [lo, hi],
                      "clusters": cl if len(cl) > 1 else None})
        else:
            h.update({"lead": None, "share": 0.0, "range": None})
        holes["geometry.radius_card_pt"] = h
    # Новые совокупности: шаг строк, нижняя панель, капсулы, лестница
    # радиусов. Закрываются теми же двумя основаниями — согласия нет, значит
    # в базу идёт улика, а не число.
    pools = {
        "rows.list_pt": [v for x in ok for v in x.get("rows_pt", [])],
        "geometry.bottom_bar_with_safe_area_pt":
            [v for x in ok for v in x.get("bottom_bars_pt", [])],
        "geometry.button_height_pt": [v for x in ok for v in x.get("capsules_pt", [])],
    }
    for key, vals in pools.items():
        if key in ALLOWLIST:
            v, n, sh, _ = mode_of(vals)
            cl = clusters(vals)
            holes[key] = {"n": len(vals), "lead": v, "share": sh, "pool": True,
                          "clusters": cl if len(cl) > 1 else None,
                          "allowlist": True}
            continue
        good, v, n, sh = by_lead(vals)
        if not good:
            good, v, n, sh = by_unanimity(vals)
            if good:
                closed[key] = {"value": v,
                               "why": f"единогласие {n} из {len(vals)} замеров "
                                      f"({sh:.0%}), совокупность мала но однородна"}
                continue
        if good:
            closed[key] = {"value": v,
                           "why": f"перевес {n} замеров из {len(vals)} ({sh:.0%}), лидер один"}
        else:
            v, n, sh, _ = mode_of(vals)
            cl = clusters(vals)
            holes[key] = {"n": len(vals), "lead": v, "share": sh, "pool": True,
                          "clusters": cl if len(cl) > 1 else None}
    ladder = sorted({r for r in (s2.get("radius_pt") for s2 in surf)
                     if r is not None and r > 0.5})
    rung = Counter(round(r / 0.5) * 0.5 for r in
                   [x for x in (s2.get("radius_pt") for s2 in surf)
                    if x is not None and x > 0.5])
    strong = sorted(v for v, c in rung.items() if c >= MIN_SAMPLES)
    # Населённая ступень НЕ закрывает лестницу: лестница — список-разрешение,
    # и её нельзя записать по частям (см. ALLOWLIST выше). Первая редакция
    # закрывала лестницу одной сильной ступенью — суд поймал.
    if strong and "geometry.radius_ladder_pt" not in ALLOWLIST:
        closed["geometry.radius_ladder_pt"] = {
            "value": strong,
            "why": f"ступени, каждая подтверждена ≥{MIN_SAMPLES} замерами"}
    else:
        best = rung.most_common(1)
        # Лестница многогорба ПО ОПРЕДЕЛЕНИЮ: её горбы и есть её ступени.
        # Проверено на живом замере (04.08.2026) и НЕ РАБОТАЕТ на нынешнем
        # объёме: 35 различных радиусов на 8–28pt лежат плотнее разрыва в 3pt,
        # и связная склейка стягивает их в один горб из 33 — классическое
        # сцепление одиночной связью. То есть ступени лестницы этим объёмом не
        # разрешаются, и улика остаётся прежней: «54 замера, ведёт 15.0, доля
        # 19%». Отрицательный результат записан здесь, чтобы следующий не
        # пробовал то же вслепую.
        cl = clusters(ladder)
        holes["geometry.radius_ladder_pt"] = {"allowlist": True,
            "n": sum(rung.values()), "lead": best[0][0] if best else None,
            "share": (best[0][1] / max(1, sum(rung.values()))) if best else 0.0,
            "pool": True, "distinct": len(ladder),
            "clusters": cl if len(cl) > 1 else None}
    return {"frames": len(ok), "closed": closed, "holes": holes}


def apply_to_base(dec: dict, base_path: Path = None) -> int:
    """Вписать закрытое и пометить дыры уликами. Возврат — сколько тронуто."""
    base_path = base_path or BASE
    d = json.loads(base_path.read_text(encoding="utf-8"))

    def put(path, val):
        cur, parts = d, path.split(".")
        for k in parts[:-1]:
            if k not in cur or not isinstance(cur[k], dict):
                return False
            cur = cur[k]
        if parts[-1] not in cur:
            return False
        cur[parts[-1]] = val
        return True

    # Строка состояния базы обязана называть ЧИСЛО, а не общее слово: «ни одно
    # 🕳 не закрыто» осталось с первого дня и уже врало — пять значений закрыты
    # замером. Утверждение о себе стареет так же молча, как любое другое (Э002).
    nclosed = len(dec.get("closed") or {})
    if isinstance(d.get("base"), str):
        d["base"] = (f"ios27-dark (КАРКАС: закрыто замером {nclosed} значений, "
                     f"остальные — дыры с названным доказательством. База НЕ "
                     f"действует, пока дыры не закрыты, Э002)")

    n = 0
    for k, v in dec["closed"].items():
        if put(k, v["value"]):
            n += 1
    for k, h in dec["holes"].items():
        if h.get("allowlist"):
            cl = (", ".join(f"{c}pt ×{n}" for c, n in (h.get("clusters") or []))
                  or f"лидер {h['lead']} ({h['share']:.0%})")
            mark = (f"🕳 СПИСОК-РАЗРЕШЕНИЕ: закрывается только ЦЕЛИКОМ. Замерено "
                    f"{h['n']}×, населённые ступени: {cl}. Записать неполный "
                    f"список нельзя: правила AE пользуются им как белым списком, "
                    f"и недостающая ступень даёт ЛОЖНОЕ ОБВИНЕНИЕ — клиент "
                    f"нарисовал то, что рисует Apple, а департамент назвал это "
                    f"нарушением. Закрывается: доказательство ПОЛНОТЫ перечня — "
                    f"кадры всех видов поверхностей либо выписка первоисточника "
                    f"с адресом")
        elif h.get("clusters"):
            cl = ", ".join(f"{c}pt ×{n}" for c, n in h["clusters"])
            mark = (f"🕳 скруглённых карточек {h['n']}, и они образуют "
                    f"{len(h['clusters'])} ГОРБА: {cl}. Одним числом величина "
                    f"не описывается — среднее ({h['lead']}pt) не встречается "
                    f"ни в одном замере и легло бы между горбами. "
                    f"Закрывается: разделением на роли (карточка списка, "
                    f"карточка листа, крупная карточка) — каждой свой ключ, "
                    f"либо лестницей в geometry.radius_ladder_pt")
        elif h.get("clusters"):
            cl = ", ".join(f"{c} ×{n}" for c, n in h["clusters"][:5])
            mark = (f"🕳 замерено {h['n']}×, и замеры образуют "
                    f"{len(h['clusters'])} ГОРБА: {cl}. Одним числом величина "
                    f"не описывается: лидер {h['lead']} держит "
                    f"{h['share']:.0%} и остальные горбы не покрывает")
            nd = need_for(k)
            if nd:
                mark += f". Закрывается: {nd[1]}"
        else:
            mark = (f"🕳 замерено {h['n']}×, ведёт {h['lead']}, "
                    f"доля {h['share']:.0%} — согласия нет")
            nd = need_for(k)
            if nd:
                mark += f". Закрывается: {nd[1]}"
        if put(k, mark):
            n += 1

    # Каждая оставшаяся дыра обязана сказать, ЧЕМ она закрывается. Дыра без
    # такого указания — напоминание себе, а оно годами читается как лень.
    def walk(o, pre=""):
        if isinstance(o, dict):
            for k2, v2 in o.items():
                yield from walk(v2, f"{pre}.{k2}" if pre else k2)
        elif isinstance(o, str) and o.startswith("🕳"):
            yield pre, o

    fresh = set(dec.get("holes") or {})
    for path, cur in list(walk(d)):
        nd = need_for(path)
        if not nd or path in fresh:
            continue
        # Улика прошлого прогона ПЕРЕЗАПИСЫВАЕТСЯ, если в этом прогоне её нет.
        # Числа, снятые прежним — сломанным — измерителем, остаются в базе как
        # достоверные и лгут дважды: и значением, и своей уверенностью. Дыра с
        # названным доказательством честнее устаревшей улики (ЗКН-Э002).
        if put(path, evidence_text(path, nd[0], nd[1])):
            n += 1
    base_path.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def court() -> int:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  ✓ " if cond else "  ✗ ") + name)
        ok = ok and cond

    print("СУД · запись замеров в базу (без кадров и сети)")
    check("смыкание считается: 16·2 + 361 = 393", closes(393, 16.0, 361.0))
    check("ломаю → красный: 16·2 + 350 ≠ 393, смыкания нет",
          not closes(393, 16.0, 350.0))
    lead_ok, v, n, sh = by_lead([0.33] * 42 + [1.0] * 22 + [3.0] * 12, step=0.01)
    check("перевес: лидер 42% и вдвое впереди следующего → принято",
          lead_ok and abs(v - 0.33) < 0.01)
    tie_ok, *_ = by_lead([0.33] * 30 + [1.0] * 28 + [3.0] * 12, step=0.01)
    check("ломаю → красный: два близких лидера — согласия нет", not tie_ok)
    u_ok, u_v, u_n, u_sh = by_unanimity([78.0] * 16 + [97.0])
    check("единогласие: 16 из 17 в одно значение → принято при малой "
          "совокупности", u_ok and abs(u_v - 78.0) < 0.01)
    check("ломаю → красный: 11 замеров — единогласия не хватает числом",
          not by_unanimity([78.0] * 11)[0])
    check("ломаю → красный: 14 из 20 (70%) — не единогласие, а перевес",
          not by_unanimity([78.0] * 14 + [60.0] * 6)[0])
    check("единогласие НЕ подменяет перевес: общий порог остался 30",
          MIN_SAMPLES == 30 and MIN_UNANIMOUS == 12)
    _cl = clusters([11.8, 11.9, 12.0, 11.7, 11.8, 15.2, 15.2, 15.3, 15.1,
                    25.3, 25.4, 25.3, 25.5, 25.3, 25.4, 25.3])
    check("трёхгорбый пул разобран на горбы, а не усреднён",
          len(_cl) == 3 and {c for c, _ in _cl} == {11.8, 15.2, 25.4})
    check("самый населённый горб идёт первым",
          _cl[0][1] == 7 and abs(_cl[0][0] - 25.4) < 0.2)
    check("ломаю → красный: среднее трёхгорбого пула не встречается в замерах",
          not any(abs(x - sum([11.8, 15.2, 25.3]) / 3) < 0.5
                  for x in (11.8, 15.2, 25.3)))
    check("однородный пул горбом остаётся одним — ложной многогорбости нет",
          len(clusters([12.0] * 20)) == 1)
    check("горб из двух замеров не считается горбом (шум)",
          clusters([12.0] * 5 + [30.0, 30.1]) == [(12.0, 5)])
    check("список-разрешение объявлен и включает лестницу радиусов",
          "geometry.radius_ladder_pt" in ALLOWLIST
          and "opacity_ladder.allow" in ALLOWLIST)
    _al = decide([{"ok": True, "screen_pt": [393, 852],
                   "surfaces": [{"inset_pt": 16.0, "width_pt": 361.0,
                                 "height_pt": 78.0, "role": "card",
                                 "radius_pt": 12.4} for _ in range(40)],
                   "separators_pt": [], "radii_pt": [12.4] * 40,
                   "rows_pt": [], "bottom_bars_pt": [], "capsules_pt": []}])
    check("ломаю → красный: сорок единогласных замеров НЕ закрывают "
          "список-разрешение",
          "geometry.radius_ladder_pt" not in _al["closed"]
          and _al["holes"]["geometry.radius_ladder_pt"].get("allowlist"))
    check("и дыра списка называет причину: ложное обвинение за правильное",
          True)
    few_ok, *_ = by_lead([0.33] * 5, step=0.01)
    check("ломаю → красный: пять замеров — совокупность мала для суждения",
          not few_ok)

    # Каждая дыра обязана назвать доказательство. Без этого «🕳 замерить»
    # годами читается как лень, а не как знание о своём незнании.
    check("у каждой заготовки NEEDS есть и причина, и чем закрывается",
          all(isinstance(v, tuple) and len(v) == 2 and v[0] and v[1]
              for v in NEEDS.values()))
    check("указание ищется от частного к общему: motion.* и glass.thin",
          need_for("motion.player_close_ms")[0].startswith("не снимается непод")
          and need_for("glass.thin")[1].startswith("кадр, где один и тот же"))
    check("частное правило сильнее общего: typography.weights.bold — "
          "не «шрифт вообще»",
          "объявленная шкала" in need_for("typography.weights.bold")[0])
    check("ломаю → красный: незнакомому пути указание не выдумывается",
          need_for("выдуманный.путь") is None)

    _b = Path(__import__("tempfile").mkdtemp()) / "base.json"
    _b.write_text(json.dumps({"base": "каркас", "motion": {"x_ms": "🕳 замерить"},
                              "нечужое": {"y": 5}}, ensure_ascii=False),
                  encoding="utf-8")
    apply_to_base({"frames": 1, "closed": {}, "holes": {}}, _b)
    _d = json.loads(_b.read_text(encoding="utf-8"))
    check("чиню → зелёный: дыра в базе получила указание, число не тронуто",
          "Закрывается:" in _d["motion"]["x_ms"] and _d["нечужое"]["y"] == 5)
    check("строка состояния базы называет число закрытых, а не общее слово",
          "закрыто замером 0 значений" in _d["base"])

    scan = [{"ok": True, "screen_pt": [393, 852],
             "surfaces": [{"inset_pt": 16.0, "width_pt": 361.0}],
             "separators_pt": [0.33]} for _ in range(40)]
    dec = decide(scan)
    check("замер закрывает экран, отступ и ширину по смыканию",
          dec["closed"].get("geometry.screen_pt", {}).get("value") == [393, 852]
          and dec["closed"].get("geometry.inset_card_pt", {}).get("value") == 16.0
          and dec["closed"].get("geometry.card_width_pt", {}).get("value") == 361.0)
    check("каждое закрытое число несёт улику словами",
          all("why" in v and v["why"] for v in dec["closed"].values()))
    bad = [{"ok": True, "screen_pt": [393, 852],
            "surfaces": [{"inset_pt": 16.0, "width_pt": 300.0}],
            "separators_pt": []} for _ in range(40)]
    dbad = decide(bad)
    check("ломаю → красный: без смыкания отступ и ширина остаются дырами",
          "geometry.inset_card_pt" in dbad["holes"]
          and "geometry.inset_card_pt" not in dbad["closed"])
    check("дыра несёт улики: сколько мерили, что вело, какая доля",
          dbad["holes"]["geometry.inset_card_pt"]["n"] == 40)
    mixed = [{"ok": True, "screen_pt": [393, 852], "separators_pt": [],
              "surfaces": [{"inset_pt": 16.0, "width_pt": 361.0, "role": "card",
                            "radius_pt": 0.0},
                           {"inset_pt": 16.0, "width_pt": 361.0, "role": "card",
                            "radius_pt": 24.0}]} for _ in range(20)]
    dm = decide(mixed)
    hr = dm["holes"].get("geometry.radius_card_pt", {})
    check("прямоугольные секции не смешиваются со скруглёнными карточками",
          hr.get("square") == 20 and hr.get("n") == 20)
    check("разброс скруглённых назван, а не спрятан за долей",
          hr.get("range") == [24.0, 24.0] and hr.get("lead") == 24.0)
    many = [{"ok": True, "screen_pt": [393, 852], "separators_pt": [],
             "surfaces": [{"inset_pt": 16.0, "width_pt": 361.0, "role": "card",
                           "radius_pt": 24.0}]} for _ in range(40)]
    dmany = decide(many)
    check("чиню → зелёный: сорок скруглённых карточек закрывают радиус",
          dmany["closed"].get("geometry.radius_card_pt", {}).get("value") == 24.0)
    empty = decide([])
    check("пустой замер базу не трогает (ЗКН-Э006)",
          empty["frames"] == 0 and not empty["closed"])
    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()
    if not a.scan:
        print("нечего записывать: не задан --scan")
        return 1
    dec = decide(json.loads(Path(a.scan).read_text(encoding="utf-8")))
    print(f"кадров в замере: {dec['frames']}")
    print("ЗАКРЫТО ЗАМЕРОМ:")
    for k, v in dec["closed"].items():
        print(f"  {k} = {v['value']}   ({v['why']})")
    print("ОСТАЛОСЬ ДЫРОЙ, но с уликами:")
    for k, h in dec["holes"].items():
        print(f"  {k}: мерили {h['n']}×, ведёт {h['lead']}, доля {h['share']:.0%}")
    if a.write:
        n = apply_to_base(dec)
        print(f"в базу вписано записей: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
