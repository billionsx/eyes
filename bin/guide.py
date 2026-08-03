#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · НАСТАВЛЕНИЕ. Что делать с находкой.

Зачем орган. Департамент умел говорить «неверно» и молчал о том, что верно.
Инструмент, называющий нарушение без цели, поднимает тревогу, но не уровень:
разработчик узнаёт, что ошибся, и не узнаёт, куда идти. Наставление достаёт
из измеренной базы ЦЕЛЬ — то самое число, ради которого правило и заведено, —
и подаёт её вместе с адресом замера.

Таблица объявлена, а не выведена. Каждая строка связывает правило с узлом
базы: цель берётся из ЗАМЕРА и меняется вместе с ним. Захардкодить число в
наставлении значило бы завести второй источник истины, который начнёт
расходиться с базой молча.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

# правило → (о чём · что сделать · путь(и) в измеренной базе за целью)
GUIDE = {
    "AE1": ("Фон вне лестницы поверхностей.",
            "Взять ступень из измеренной лестницы. Глубину даёт СТУПЕНЬ, "
            "а не осветление произвольным серым.",
            ["surfaces.allow"]),
    "AE2": ("Тень на чёрном холсте.",
            "Убрать box-shadow/drop-shadow. Разделить слои следующей "
            "ступенью поверхности.",
            ["surfaces.allow"]),
    "AE3": ("Скругление больше порога без формы суперэллипса.",
            "Либо уменьшить радиус до порога, либо задать форму: "
            "clip-path:path(...) или corner-shape.",
            ["geometry.corner_form_required_above_pt", "geometry.superellipse_n"]),
    "AE4": ("Трекинг в пикселях выше крышки.",
            "Убрать letter-spacing в px либо свести под крышку. Трекинг "
            "принадлежит РОЛИ и задаётся в em.",
            ["typography.tracking_cap_px"]),
    "AE5": ("Кегль вне шкалы ролей.",
            "Взять ближайший кегль из шкалы ролей.",
            ["typography.role_sizes_pt"]),
    "AE6": ("Тёплый двойник системного цвета.",
            "Заменить на системный цвет метки с прозрачностью — двойник даёт "
            "систематический сдвиг тепла по всему интерфейсу.",
            ["opacity_ladder.allow"]),
    "AE7": ("Размытие без насыщения.",
            "Добавить saturate() в том же значении: стекло Apple — это "
            "размытие И насыщение, голый blur даёт мутную серость.",
            ["glass"]),
    "AE8": ("Длинное движение на дефолтной кривой.",
            "Поставить измеренную кривую вместо ease/linear.",
            ["motion.min_ms_for_curve", "motion.curve"]),
    "AE9": ("Прозрачность вне лестницы.",
            "Взять ступень из лестницы прозрачности.",
            ["opacity_ladder.allow"]),
    "AE10": ("Шрифтовой стек начинается не с системного.",
             "Поставить системный стек первым: подмена первой позиции ломает "
             "метрики.",
             ["typography.font_stack_head"]),
    "AE11": ("Радиус вне измеренной лестницы.",
             "Взять ближайший радиус из лестницы.",
             ["geometry.radius_ladder_pt"]),
    "AE12": ("Отклик на нажатие дольше предела.",
             "Сократить переход в :active до предела — нажатие обязано "
             "отвечать мгновенно.",
             ["motion.press_response_ms_max"]),
    "AE13": ("Есть длинное движение, нет уважения к Reduce Motion.",
             "Добавить @media (prefers-reduced-motion: reduce) и погасить "
             "в нём анимации.",
             ["motion.min_ms_for_curve"]),
    "AE14": ("Цель касания меньше минимума.",
             "Довести интерактивный элемент до минимума — увеличением "
             "самого элемента или прозрачной областью нажатия.",
             ["tap_target.min_pt", "tap_target.secondary_min_pt"]),
    "AE15": ("Контраст пары цветов ниже порога.",
             "Поднять контраст текста к фону до порога.",
             ["contrast.min_ratio"]),
    "AE16": ("Заливка под активным пунктом нижней навигации.",
             "Убрать background у активного пункта. Активный таб отличается "
             "ТОНОМ — цветом глифа и подписи; неактивный остаётся нейтральным "
             "серым. Заливка-капсула под активным — приём Material, не iOS.",
             ["tabbar", "geometry.tabbar_height_pt"]),
}


def _dig(tree, path):
    cur = tree
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def guide(rule, tokens=None):
    """Наставление по правилу: смысл, действие, ЦЕЛЬ из замера, адрес."""
    if tokens is None:
        tokens = json.loads(
            (ROOT / "registry" / "standards" / "tokens.json")
            .read_text(encoding="utf-8"))
    g = GUIDE.get(rule)
    if not g:
        return {"rule": rule, "error": "нет такого правила"}
    what, todo, paths = g
    target = {}
    for p in paths:
        v = _dig(tokens, p)
        if v is not None:
            target[p] = v
    out = {"rule": rule, "problem": what, "action": todo, "target": target}
    # Двойное свидетельство, если оно по этому правилу есть.
    try:
        import attest as att
        import law as lw
        rows = att.attest(tokens, lw.load(), paths[0].split(".")[0])
        proven = [r for r in rows if r["verdict"] == "ПОДТВЕРЖДЕНО"]
        if proven:
            out["apple_says"] = {"law": proven[0]["law"], "address": proven[0]["id"]}
    except Exception:
        pass
    return out


def court():
    ok = True

    def chk(n, c):
        nonlocal ok
        ok = ok and bool(c)
        print(f"  {'✓' if c else '✗'} {n}")

    print("СУД · наставление")
    tok = json.loads((ROOT / "registry" / "standards" / "tokens.json")
                     .read_text(encoding="utf-8"))

    chk("наставление есть на КАЖДОЕ правило департамента",
        set(GUIDE) == {f"AE{i}" for i in range(1, 17)})

    g = guide("AE14", tok)
    chk("цель берётся из ЗАМЕРА, а не из текста наставления",
        g["target"]["tap_target.min_pt"] == tok["tap_target"]["min_pt"])
    chk("наставление называет и проблему, и действие",
        g["problem"] and g["action"])

    empty = guide("AE14", {"tap_target": {}})
    chk("подмена базы меняет цель — второго источника истины нет",
        empty["target"] == {})

    chk("несуществующее правило — внятный отказ",
        "error" in guide("AE99", tok))

    for r in GUIDE:
        if not guide(r, tok)["target"]:
            chk(f"у {r} цель не достаётся из базы", False)
            break
    else:
        chk("у каждого правила цель достаётся из живой базы", True)

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(court() if "--court" in sys.argv else
             (print(json.dumps(guide(sys.argv[1] if len(sys.argv) > 1 else "AE1"),
                               ensure_ascii=False, indent=2)) or 0))
