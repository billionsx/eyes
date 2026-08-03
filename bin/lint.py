#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ИСПОЛНИТЕЛЬНАЯ ВЛАСТЬ. Переносимый линт измеренных стандартов.

Правила выведены из замеров (registry/standards/tokens.json — каждое число
несёт адрес, ЗКН-Э002), а не из вкуса. Комментарии срезаются ДО проверки:
в комментариях законно живут строки-нарушители (грабли гейтов у клиентов).

Правила:
  AE1 ПОВЕРХНОСТЬ  фон задаётся только измеренными ступенями поверхностей
                   (tokens.surfaces.allow + allow_extra адаптера). Ступени три,
                   а не «примерно тёмные»: #000000 → #1C1C1E → #2C2C2E.
  AE2 ТЕНЬ         box-shadow на чёрном холсте запрещён — в 217 кадрах тени
                   на #000 нет; глубину даёт ступень поверхности, не тень.
  AE3 УГОЛ         скругление > 12 pt требует формы суперэллипса в файле
                   (clip-path:path(...) или corner-shape) — дуга border-radius
                   проиграла замер во всех девяти продуктах (§4.2).
  AE4 ТРЕКИНГ      letter-spacing в px не превышает ±0.4 (жёсткая крышка
                   поправки трекинга); значения в em принадлежат РОЛИ и
                   правилом не трогаются (Э002: трекинг у Apple задан в em).
  AE5 КЕГЛЬ        font-size из шкалы ролей (report-советник по умолчанию:
                   легальны и кегли, выведенные из чернил кадра).
  AE6 ДВОЙНИК      известные тёплые двойники запрещены: #8E8E8E вместо
                   rgba(235,235,245,.60) даёт систематический сдвиг тепла
                   по всему интерфейсу (TOKENS §2).
  AE7 СТЕКЛО       backdrop-filter с blur() обязан нести saturate() в том же
                   значении — стекло Apple это размытие+насыщение, голый blur
                   даёт мутную серость, не материал (products/music.md §стекло).
  AE8 КИНЕТИКА     движение ≥ min_ms_for_curve не ходит на дефолтных
                   ease/linear — длинному движению положена измеренная кривая
                   (383 мс · cubic-bezier(.32,.72,0,1), products/music.md §движение).
  AE9 ПРОЗРАЧНОСТЬ standalone opacity только из лестницы (канон меток iOS
                   .60/.30/.18 + измеренное стекло .05/.06/.09).
  AE10 СТЕК        font-family начинается с системного стека (-apple-system /
                   system-ui / SF Pro) — подмена первой позиции ломает метрики.
  AE11 РАДИУС      border-radius из измеренной лестницы (советник: чужой
                   радиус — чужая геометрия).
  AE12 НАЖАТИЕ     переход в :active не длиннее press_response_ms_max —
                   нажатие отвечает ≤120 мс (products/music.md §движение), дольше =
                   мёртвая рука под пальцем.
  AE13 ДВИЖЕНИЕ-   проект с длинным движением обязан уважать Reduce Motion:
       ДОСТУПНОСТЬ хоть один @media (prefers-reduced-motion) в охвате —
                   канон Apple (HIG Motion/Accessibility): не все могут или
                   хотят переживать движение. Правило проектного уровня.

  AE14 КАСАНИЕ     интерактивный элемент не уже нормы свода 44×44pt по
                   min-width/height — ПЕРВОЕ правило, рождённое конвейером:
                   обход живого свода → добытчик кандидатов → правило
                   (🍎 tokens.tap_target.source, страница живая, не снимок).
  AE19 DYNAMIC TYPE  кегль текста задан МАСШТАБИРУЕМО (rem/em/%/clamp),
                     а не жёстким px: от xSmall к xxxLarge Apple растит
                     кегль на 18 %, а на ступенях доступности — кратно
  AE20 КАПСА       text-transform:uppercase — капсы у Apple нет, заголовок
                   группы Title Case (§3.4); капс это iOS 12
  AE17 ПАРА ТЕМ    поверхность имеет значение для СВЕТЛОЙ и ТЁМНОЙ темы,
                   а не одно жёсткое на обе (только для проектов, где темы
                   уже объявлены)
  AE16 АКТИВНЫЙ ТАБ  активный пункт нижней навигации отличается ТОНОМ,
                     а не заливкой под ним (замер: 37 кадров таб-бара по
                     10 приложениям Apple — заливки нет ни в одном)
  AE18 РАЗДЕЛИТЕЛЬ линия тоньше замеренной 1pt исчезает на 1x (📐 217 кадров)
  AE15 КОНТРАСТ    пара color/background одного блока держит ≥4.5:1 по
                   люминантности WCAG — норма свода dark-mode
                   (🍎 tokens.contrast.source). Пары с var() не судятся:
                   значение не видно статически, молчание честнее догадки.

Отступы правилом НЕ проверяются — ключевой замер: точечной сетки НЕТ,
шаг CSS = ⅓pt при @3x; «линт сетки отступов» противоречил бы измерениям.

Режимы: strict — любое error-нарушение = exit 1; report — только отчёт.
"""
import glob
import json
import re
import sys
from pathlib import Path


def hex6(c: str) -> str:
    """Цвет к канонической шестизначной форме в верхнем регистре.

    #1c1 → #11CC11. Сравнение цветов идёт ТОЛЬКО через эту форму: две записи
    одного цвета обязаны давать один вердикт, иначе правило судит запись,
    а не цвет.
    """
    c = c.strip().upper()
    if len(c) == 4:
        return "#" + "".join(ch * 2 for ch in c[1:])
    return c


def _blank(m) -> str:
    """Комментарий стирается, но его переводы строк остаются на месте.

    Иначе номера строк едут вверх: `_line_of` считает их по обрезанному
    тексту, и каждый адрес после первого многострочного комментария
    указывает не туда. Это рушит ЗКН-Э002 — число обязано нести адрес.
    """
    return " " + "\n" * m.group(0).count("\n")


# ── СЛОВАРЬ ПЕРЕМЕННЫХ ──────────────────────────────────────────────────────

# Имя переменной по спецификации CSS может нести любые буквы, не только
# латиницу: `--отступ` законен. Класс \w в Python юникодный, поэтому имена
# на кириллице и других письменностях больше не выпадают из разбора.
VAR_DEF = re.compile(r"(--[\w-]+)\s*:\s*([^;{}]+)", re.UNICODE)
VAR_USE = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*?)\s*)?\)",
                     re.UNICODE)
MAX_CHAIN = 8


def _collect_vars(project_root, globs):
    """Собирает объявления переменных по всему охвату.

    Возвращает (однозначные, спорные). Переменная со СПОРНЫМИ значениями —
    объявленная по-разному в светлой и тёмной теме — не подставляется вовсе:
    выбрать одну сторону значит судить проект по половине его правды.
    Промолчать честнее, чем угадать, и число таких переменных department
    показывает отдельно.
    """
    seen = {}
    for g in globs:
        for fp in sorted(glob.glob(str(Path(project_root) / g), recursive=True)):
            p = Path(fp)
            if not p.is_file() or p.suffix not in (
                    ".css", ".scss", ".sass", ".html", ".htm",
                    ".tsx", ".ts", ".jsx", ".js", ".vue", ".svelte"):
                continue
            try:
                t = strip_comments(
                    p.read_text(encoding="utf-8", errors="replace"), p.suffix)
            except OSError:
                continue
            for m in VAR_DEF.finditer(t):
                name, val = m.group(1), m.group(2).strip()
                if not val or len(val) > 120:
                    continue
                seen.setdefault(name, set()).add(val)
    defs = {n: next(iter(v)) for n, v in seen.items() if len(v) == 1}
    ambiguous = sorted(n for n, v in seen.items() if len(v) > 1)
    return defs, ambiguous


def _resolve(name, defs, depth=0):
    """Значение переменной с проходом по цепочке ссылок.

    Глубина ограничена: `--a: var(--b)` и `--b: var(--a)` — кольцо, и без
    предела разбор ушёл бы в бесконечность на чужом коде.
    """
    if depth >= MAX_CHAIN or name not in defs:
        return None
    val = defs[name]
    m = VAR_USE.fullmatch(val.strip())
    if m:
        return _resolve(m.group(1), defs, depth + 1) or (m.group(2) or None)
    return None if "var(" in val else val


def _expand_vars(text, defs):
    """Подставляет значения переменных, СОХРАНЯЯ длину текста.

    Длина неприкосновенна: подстановка идёт в тот же отрезок, добивается
    пробелами либо, если значение длиннее ссылки, не делается вовсе.
    Иначе смещаются номера строк и адрес находки указывает не туда —
    ровно та ложь, за которую департамент только что чинил зеркало.
    """
    # Пустой словарь выходом не является: `var(--нет, 20px)` несёт запасное
    # значение в себе, и проект без единого объявления всё равно судим.
    if "var(" not in text:
        return text
    out = []
    last = 0
    for m in VAR_USE.finditer(text):
        val = _resolve(m.group(1), defs)
        if val is None:
            val = (m.group(2) or "").strip() or None
        if val is None or "\n" in val or len(val) > (m.end() - m.start()):
            continue
        out.append(text[last:m.start()])
        out.append(val.ljust(m.end() - m.start()))
        last = m.end()
    if not out:
        return text
    out.append(text[last:])
    return "".join(out)


# ── ПЕРЕМЕННЫЕ С ОГЛЯДКОЙ НА ОБЛАСТЬ ────────────────────────────────────────
# Спорная переменная — не тупик, а главная зона работы. Замер по трём чужим
# проектам: спорных БОЛЬШЕ, чем однозначных (97 против 129 у Excalidraw,
# 46 против 24 у Hoppscotch). Это не беспорядок, это устройство тем: зрелый
# проект объявляет одну переменную дважды — значение для светлого, значение
# для тёмного.
#
# Подставить такую в место применения нельзя: там неизвестно, какая тема
# сработает. Зато у САМОГО ОБЪЯВЛЕНИЯ тема известна точно — она задана
# областью, в которой объявление стоит. И адрес там настоящий, а не
# производный от места применения.
#
# Поэтому департамент судит объявление: тёмное значение — тёмной лестницей,
# светлое — светлой. Обе у него есть: тёмная снята с кадров iOS, светлая
# добыта жатвой из публикации Apple.

VAR_ROLE = re.compile(r"([a-z-]+)\s*:\s*[^;{}]*?var\(\s*(--[\w-]+)", re.I)


def _rgb(c):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _dist(a, b):
    """Расстояние между цветами по худшему каналу."""
    x, y = _rgb(a), _rgb(b)
    return max(abs(x[i] - y[i]) for i in range(3))


def _sat(c):
    """Насыщенность: разброс между каналами. У серого он ноль."""
    r, g, b = _rgb(c)
    return max(r, g, b) - min(r, g, b)


def _is_surface(c, _ladder=None):
    """Претендует ли цвет быть ПОВЕРХНОСТЬЮ.

    Расстояние до лестницы мерой не годится: белый фон в тёмной теме от
    тёмной лестницы далёк, но это очевидное нарушение поверхности, а не
    акцент. Различает не расстояние, а НЕЙТРАЛЬНОСТЬ.
    
    Граница снята с базы С ДВУХ СТОРОН, а не назначена:
      · самая насыщенная ступень тёмной лестницы (замер)      —  2
      · самая насыщенная ступень лестницы Apple (публикация)  —  5
      · наименее насыщенный ИЗМЕРЕННЫЙ акцент (#D8AE3C)      — 156
    Между 5 и 156 лежит пропасть, и порог поставлен у нижнего её края с
    запасом: до 64 — нейтральный оттенок, то есть кто-то выдумал свою
    ступень вместо измеренной. Выше — акцент, а акцент по базе
    департамента принадлежит ПРОДУКТУ (узел `accents`) и нейтральной
    лестницей не судится. Судить фирменный фиолетовый серой лестницей —
    ошибка предмета, а не строгость.
    """
    return _sat(c) <= NEUTRAL_MAX


# Порог нейтральности ВЫВЕДЕН, а не назначен: половина от наименее
# насыщенного ИЗМЕРЕННОГО акцента (#D8AE3C, насыщенность 156). Цвет, вдвое
# менее насыщенный, чем самый бледный акцент Apple, акцентом по свидетельству
# департамента не является — значит претендует быть поверхностью.
# Наблюдаемые поверхности чужих проектов ложатся до 21, акценты — от 125:
# порог стоит в пустоте между ними, а не на границе живых данных.
NEUTRAL_MAX = 78


def _scope_of(text, pos):
    """Тема, в которой стоит объявление: dark · light · contrast · base."""
    for h in _enclosing_headers(text, pos):
        if PRINT_SCOPE.search(h):
            return "print"
        if re.search(r"prefers-contrast\s*:\s*(more|high)", h, re.I):
            return "contrast"
        if LIGHT_SCOPE.search(h):
            return "light"
        if re.search(r"prefers-color-scheme\s*:\s*dark|"
                     r"(?:^|[\s,.:#\[])dark\b", h, re.I):
            return "dark"
    return "base"


def _var_decls(project_root, globs):
    """Объявления переменных с ТЕМОЙ и адресом: name → [(значение, тема,
    файл, строка)]. Роли: name → множество свойств, в которых применяется."""
    decls, roles = {}, {}
    for g in globs:
        for fp in sorted(glob.glob(str(Path(project_root) / g), recursive=True)):
            p = Path(fp)
            if not p.is_file() or p.suffix not in (
                    ".css", ".scss", ".sass", ".html", ".htm",
                    ".tsx", ".ts", ".jsx", ".js", ".vue", ".svelte"):
                continue
            try:
                t = strip_comments(
                    p.read_text(encoding="utf-8", errors="replace"), p.suffix)
            except OSError:
                continue
            rel = str(p.relative_to(Path(project_root)))
            for m in VAR_DEF.finditer(t):
                val = m.group(2).strip()
                if not val or len(val) > 120:
                    continue
                decls.setdefault(m.group(1), []).append(
                    (val, _scope_of(t, m.start()), rel, _line_of(t, m.start())))
            for m in VAR_ROLE.finditer(t):
                roles.setdefault(m.group(2), set()).add(m.group(1).lower())
    return decls, roles


# Роли, чья лестница НЕ зависит от темы. Радиус, прозрачность, кегль и
# трекинг одинаковы в светлом и тёмном интерфейсе, поэтому объявление
# судится независимо от области — и судится ДАЖЕ спорное, у которого
# несколько значений: каждое обязано лежать на лестнице.
#
# Роль → (правило, свойства CSS, единица). Объявлена, не выведена.
VAR_ROLES = (
    ("AE11", ("border-radius", "border-top-left-radius",
              "border-top-right-radius", "border-bottom-left-radius",
              "border-bottom-right-radius"), "px"),
    ("AE9", ("opacity",), ""),
    ("AE5", ("font-size",), "px"),
    ("AE4", ("letter-spacing",), "px"),
)

NUMVAL = re.compile(r"^([-+]?\d*\.?\d+)\s*(px|rem|em|%)?$")


def _judge_var_scales(decls, roles, tokens, rules, resolved=()):
    """Находки по объявлениям переменных ролей с лестницей.

    Зачем отдельно от подстановки. Подстановка молчит на СПОРНОЙ переменной:
    в месте применения неизвестно, какое из значений сработает. А у самого
    объявления значение одно и известно точно — и оно обязано лежать на
    лестнице независимо от того, сколько у переменной соседей.
    """
    out = []
    rad = [float(x) for x in (tokens.get("geometry", {})
                              .get("radius_ladder_pt") or [])]
    op = [float(x) for x in (tokens.get("opacity_ladder", {})
                             .get("allow") or [])]
    sizes = [float(x) for x in (tokens.get("typography", {})
                                .get("role_sizes_pt") or [])]
    cap = tokens.get("typography", {}).get("tracking_cap_px")
    capsule = float(tokens.get("geometry", {})
                    .get("capsule_from_pt") or 9999)

    for rule, props, unit in VAR_ROLES:
        if rule not in rules:
            continue
        for name, items in sorted(decls.items()):
            # ОДНОЗНАЧНУЮ переменную уже подставила подстановка, и правило
            # сработало в месте применения. Судить её ещё и по объявлению
            # значит наказать дважды за один дефект — ровно тот грех, за
            # который департамент разводил AE17 с AE1. Здесь судится только
            # то, до чего подстановка дотянуться не может: спорное.
            if name in resolved:
                continue
            if not (roles.get(name) or set()) & set(props):
                continue
            for val, _scope, rel, line in items:
                m = NUMVAL.match(val.strip())
                if not m:
                    continue
                v = float(m.group(1))
                u = m.group(2) or ""
                if unit == "px" and u not in ("px", ""):
                    continue          # rem/em/% — масштабируемая форма
                if rule == "AE11" and rad and v not in rad and v < capsule:
                    out.append((rule, rel, line,
                                f"переменная радиуса {v:g}px вне измеренной "
                                f"лестницы {sorted(rad)}"))
                elif rule == "AE9" and op and v not in op and 0 <= v <= 1:
                    out.append((rule, rel, line,
                                f"переменная прозрачности {v:g} вне лестницы "
                                f"{op} (метки iOS + измеренное стекло)"))
                elif rule == "AE5" and sizes and v not in sizes and v >= 8:
                    out.append((rule, rel, line,
                                f"переменная кегля {v:g}px вне шкалы ролей "
                                f"{sorted(sizes)}"))
                elif rule == "AE4" and cap is not None and abs(v) > float(cap):
                    out.append((rule, rel, line,
                                f"переменная трекинга {v:g}px — крышка "
                                f"поправки ±{cap}px; роль задаётся в em"))
    return out


def _judge_var_surfaces(decls, roles, dark_allow, light_allow, resolved=()):
    """Находки по объявлениям переменных, применяемых как ФОН.

    Судится каждое объявление своей лестницей. Переменная, которую никогда
    не применяют фоном, не судится вовсе: цвет текста и цвет фона живут на
    разных лестницах, и мерить один другой значит выдумывать нарушения.
    """
    out = []
    for name, items in sorted(decls.items()):
        if name in resolved:
            continue                  # подстановка уже донесла до правила
        props = roles.get(name) or set()
        if not any(p in ("background", "background-color") for p in props):
            continue
        for val, scope, rel, line in items:
            if scope == "print" or not re.fullmatch(HEX, val.strip()):
                continue
            c = hex6(val.strip())
            if scope == "light":
                if (light_allow and c not in light_allow
                        and _is_surface(c, light_allow)):
                    out.append((rel, line, c, "СВЕТЛОЙ", light_allow))
            elif scope in ("dark", "base"):
                if (dark_allow and c not in dark_allow
                        and _is_surface(c, dark_allow)):
                    out.append((rel, line, c, "тёмной", sorted(dark_allow)))
    return out


def strip_comments(text: str, suffix: str) -> str:
    text = re.sub(r"/\*.*?\*/", _blank, text, flags=re.S)        # CSS / JS block
    if suffix in (".ts", ".tsx", ".js", ".jsx", ".scss", ".sass",
                  ".vue", ".svelte"):
        text = re.sub(r"(?<![:\\])//[^\n]*", " ", text)          # // строка (не https://)
    if suffix in (".html", ".htm"):
        text = re.sub(r"<!--.*?-->", _blank, text, flags=re.S)
    return text


# Цвет в CSS законно пишется ШЕСТЬЮ и ТРЕМЯ знаками: #1c1 — это #11CC11,
# и лестница поверхностей обязана судить обе записи одинаково. Ловля только
# шестизначной формы оставляла в гейте дыру, через которую любой цвет
# проходил молча: `#1c1` не в лестнице, а правило не срабатывало.
# Шесть знаков идут в чередовании ПЕРВЫМИ — иначе три знака откусят начало
# шестизначного цвета и сравнение пойдёт с огрызком.
HEX = r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b"

# AE16. Селектор нижней навигации И признак активного состояния в одном
# правиле. Оба условия обязательны: «.tab{}» — это просто таб, «.active{}» —
# это что угодно; вместе — активный пункт навигации, и только он судится.
NAV_SEL = re.compile(r"(?:^|[\s.#\[>+~-])(?:tab-?bar|tabbar|bottom-?nav|"
                     r"navbar-?bottom|nav-?bar|tabs?|nav)(?:$|[\s.#\[:>,{-])", re.I)
ACTIVE_SEL = re.compile(r"(?:[.:\[-]|\b)(?:is-)?(?:active|selected|current|"
                        r"checked|on)\b|aria-current", re.I)
# Заливка. Прозрачное и none заливкой не являются — тон через background
# с прозрачностью Apple тоже не применяет, но запрещать нечего: не заливка.
FILL_DECL = re.compile(r"background(?:-color)?\s*:\s*([^;}]+)", re.I)
NOFILL = re.compile(r"^\s*(?:none|transparent|inherit|initial|unset|revert|"
                    r"rgba\([^)]*,\s*0?\.?0+\s*\))\s*$", re.I)
BG_PROP = re.compile(r"(?:background|background-color)\s*:\s*(" + HEX + ")", re.I)
SHADOW = re.compile(r"\b(?:box-shadow|text-shadow)\s*:\s*(?!\s*none)|drop-shadow\(", re.I)
# AE2 разбирает ЗНАЧЕНИЕ тени по слоям. Запрет касается тени НАРУЖУ — она
# подделывает глубину, которой на #000 в 217 кадрах нет. Слой `inset` рисует
# не тень, а КРОМКУ материала: tokens.json §material определяет стекло как
# «размытие+насыщение фона · верхний блик кромки · нижняя тень кромки ·
# волосок», и в CSS верхний блик и нижняя кромка выражаются единственным
# способом — `box-shadow: inset`. Правило, которое их ловит, ловит собственный
# канон департамента. Поэтому: объявление красное, если хотя бы один его слой
# НЕ inset; объявление целиком из inset-слоёв — кромка, не тень.
SHADOW_DECL = re.compile(r"\b(box-shadow|text-shadow)\s*:\s*([^;{}]*)", re.I)
DROPSHADOW = re.compile(r"drop-shadow\(", re.I)
LAYER_SPLIT = re.compile(r",(?![^()]*\))")


def _shadow_is_outer(value: str) -> bool:
    """Есть ли в объявлении хоть один слой, рисующий тень НАРУЖУ."""
    v = value.strip()
    if not v or v.lower().startswith("none"):
        return False
    for layer in LAYER_SPLIT.split(v):
        layer = layer.strip()
        if layer and not layer.lower().startswith("inset"):
            return True
    return False


RADIUS = re.compile(r"border-radius\s*:\s*([\d.]+)px", re.I)

# ─────────────────── контекст объявления (заголовки блоков) ───────────────────
# Правила ниже смотрят НЕ на свойство, а на блок, в котором оно стоит: одно и то
# же свойство законно в одном контексте и незаконно в другом. Текст сюда приходит
# уже без комментариев (strip_comments сохраняет смещения), поэтому фигурные
# скобки в тексте — настоящие.
LIGHT_SCOPE = re.compile(
    r"""data-theme\s*=\s*['"]?light|prefers-color-scheme\s*:\s*light""", re.I)


def _enclosing_headers(text: str, pos: int) -> list:
    """Заголовки всех блоков, внутрь которых попадает позиция (снаружи внутрь)."""
    headers, stack, start = [], [], 0
    for m in re.finditer(r"[{}]", text):
        if m.start() >= pos:
            break
        if m.group() == "{":
            stack.append(text[start:m.start()])
            start = m.end()
        else:
            if stack:
                stack.pop()
            start = m.end()
    return [h.strip().replace("\n", " ") for h in stack]


def _in_font_face(text: str, pos: int) -> bool:
    """Стоит ли объявление внутри @font-face."""
    return any(h.lower().lstrip().endswith("@font-face") or "@font-face" in h.lower()
               for h in _enclosing_headers(text, pos))


def _in_light_scope(text: str, pos: int) -> bool:
    """Объявление адресовано СВЕТЛОЙ теме."""
    return any(LIGHT_SCOPE.search(h) for h in _enclosing_headers(text, pos))


def _light_exempt(tokens: dict) -> bool:
    """Освобождает ли светлая тема от запрета тени.

    Освобождение появилось не как поблажка, а как ЧЕСТНОСТЬ: запрет AE2 был
    снят с ЧЁРНОГО холста (217 кадров), и распространять его на светлый, не
    измерив светлый, значило бы судить по чужой оси.

    Теперь светлый измерен: 635 чистых кромок холст→карточка, профиль холста
    наружу от кромки на 0..7 pt даёт медиану РОВНО 0.000 — тени нет и там.
    Основание освобождения исчезло, и освобождение снимается — данными, а не
    мнением: появится в своде замер, говорящий обратное, — вернётся само.
    """
    return not (tokens.get("shadows", {}) or {}).get("light_depth")


# AE17. ОБЛАСТЬ ТЕМЫ. Объявление считается тематическим, если стоит внутри
# любого механизма смены темы: медиазапрос схемы, атрибут темы, класс темы.
# Список закрытый и объявленный: угадывать «похоже на тему» нельзя.
THEME_SCOPE = re.compile(
    r"prefers-color-scheme|data-theme|\[data-[a-z-]*theme|"
    r"(?:^|[\s,.:#])(?:light|dark)(?:-mode|-theme)?\b(?=[^{]*$)", re.I)


def _in_theme_scope(text: str, pos: int) -> bool:
    """Объявление адресовано КОНКРЕТНОЙ теме, а не обеим сразу."""
    return any(THEME_SCOPE.search(h) for h in _enclosing_headers(text, pos))


# AE19. Кегль задан жёстким пикселем — интерфейс не переживёт Dynamic Type.
FS_PX = re.compile(r"font-size\s*:\s*(\d*\.?\d+)\s*px", re.I)
# Масштабируемые формы. var() СЮДА НЕ ВХОДИТ намеренно: во что развернётся
# переменная, статически неизвестно, и записывать её в заслугу значило бы
# оправдывать проект за то, чего не видно. Она не считается ни за, ни против.
FS_SCALE = re.compile(r"font-size\s*:\s*[^;}]*?(\d*\.?\d+\s*(?:rem|em|%)|clamp\()",
                      re.I)

PRINT_SCOPE = re.compile(r"@media[^{]*\bprint\b", re.I)


def _in_print_scope(text: str, pos: int) -> bool:
    """Объявление адресовано ПЕЧАТИ.

    Лестница поверхностей описывает ХОЛСТ операционной системы: #000000 →
    #1C1C1E → #2C2C2E. Бумага холстом не является — белый фон на печати не
    нарушение, а единственно верное решение, и требовать от листа чёрной
    ступени абсурдно.

    Граница та же, что департамент уже проводит для светлой темы у AE2:
    правило судит там, где холст известен, и молчит там, где известен другой.
    """
    return any(PRINT_SCOPE.search(h) for h in _enclosing_headers(text, pos))

SUPER = re.compile(r"clip-path\s*:\s*path\(|corner-shape", re.I)
# AE20. Капса. Свод департамента прямо говорит: капсы у Apple НЕТ — заголовок
# группы идёт Title Case (typography.caps_lock, §3.4); капс это iOS 12. Норма
# была, правила под неё не было — и заглавные метки не ловились ничем.
# Ловится ОБЪЯВЛЕНИЕ, а не литерал: `text-transform: uppercase` — решение о
# начертании, машинно однозначное. Литеральные строки в разметке не судятся:
# аббревиатура (ФИО, НДС, URL) заглавная по своей природе, и правило,
# которое их ловит, воспитывает не вкус, а привычку игнорировать отчёт.
UPPERCASE = re.compile(r"text-transform\s*:\s*uppercase", re.I)
LSPX = re.compile(r"letter-spacing\s*:\s*(-?[\d.]+)px", re.I)
FSIZE = re.compile(r"font-size\s*:\s*([\d.]+)px", re.I)
BACKDROP = re.compile(r"backdrop-filter\s*:\s*([^;}\n]+)", re.I)
MOTION = re.compile(r"\b(?:transition|animation)\s*:\s*([^;}\n]+)", re.I)
MS = re.compile(r"([\d.]+)\s*(ms|s)\b")
OPACITY = re.compile(r"(?<![-\w])opacity\s*:\s*(0?\.\d+|[01])(?![\d.])", re.I)
FFAM = re.compile(r"font-family\s*:\s*([^;}\n]+)", re.I)
ACTIVE_BLOCK = re.compile(r":active[^{]*\{([^}]*)\}", re.I | re.S)
# AE18 · РАЗДЕЛИТЕЛЬ. Ищем объявления, задающие толщину линии-разделителя.
# Не всякое «0.5px» — разделитель: сито знает ОДНУ форму записи и не гадает.
HAIRLINE = re.compile(
    r"""(?:border(?:-(?:top|bottom|left|right))?|outline)\s*:\s*"""
    r"""(?P<v>\d*\.?\d+)px|"""
    r"""border-(?:top|bottom|left|right)?-?width\s*:\s*(?P<v2>\d*\.?\d+)px""",
    re.I)

# AE18 · РАЗДЕЛИТЕЛЬ. Сито знает ОДНУ форму записи и не гадает: границу задают
# либо сокращением `border[-сторона]`, либо явной `border-*-width`.
HAIRLINE = re.compile(
    r"(?:^|[;{\s])(?:border(?:-(?:top|bottom|left|right))?|outline)\s*:\s*"
    r"(?P<v>\d*\.?\d+)px"
    r"|(?:^|[;{\s])border-(?:top|bottom|left|right)-width\s*:\s*"
    r"(?P<v2>\d*\.?\d+)px",
    re.I)

BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)
INTERACTIVE = re.compile(r"(button|\bbtn\b|btn-|-btn\b|tappable|clickable|"
                         r"switch|toggle|segmented|\btab\b|-tab\b|chip)", re.I)
EXEMPT_SEL = re.compile(r"(icon|badge|\bdot\b|indicator|divider|separator|"
                        r"thumb|caret|arrow)", re.I)
SIZEDECL = re.compile(r"\b(?:min-)?(?:width|height)\s*:\s*([\d.]+)px", re.I)
FG_DECL = re.compile(r"(?<![-\w])color\s*:\s*(#(?:[0-9a-f]{3}|[0-9a-f]{6}))"
                     r"(?![0-9a-f])", re.I)
BG_DECL = re.compile(r"background(?:-color)?\s*:\s*(#(?:[0-9a-f]{3}|[0-9a-f]{6}))"
                     r"(?![0-9a-f])", re.I)


def _lum(hexc: str) -> float:
    """Относительная люминантность по WCAG — та же формула, что в норме 4.5:1."""
    h = hexc.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(h[k:k + 2], 16)) for k in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    la, lb = _lum(a), _lum(b)
    hi, lo = (la, lb) if la >= lb else (lb, la)
    return (hi + 0.05) / (lo + 0.05)




def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def run(root: Path, adapter: dict, tokens: dict, mode: str, project_root: Path) -> dict:
    scope = adapter.get(mode, {}) or {}
    globs = scope.get("globs", [])
    rules = scope.get("rules", ["AE1", "AE2", "AE3", "AE4", "AE6"])
    allow = {hex6(c) for c in tokens["surfaces"]["allow"]} | {hex6(c) for c in adapter.get("allow_extra", [])}
    forb = {hex6(c): why for c, why in tokens.get("forbidden_colors", {}).items()}
    cap = float(tokens["typography"]["tracking_cap_px"])
    rad_lim = float(tokens["geometry"]["corner_form_required_above_pt"])
    sizes = {float(s) for s in tokens["typography"]["role_sizes_pt"]} | {float(s) for s in adapter.get("sizes_extra", [])}
    op_l = tokens.get("opacity_ladder", {})
    op_allow = [float(v) for v in op_l.get("allow", [])]
    op_tol = float(op_l.get("tolerance", 0.005))
    min_ms = float(tokens.get("motion", {}).get("min_ms_for_curve", 200))
    rad_ladder = {float(v) for v in tokens["geometry"].get("radius_ladder_pt", [])} | {float(v) for v in adapter.get("radius_extra", [])}
    # Капсула — ФОРМА, а не значение лестницы: скругление ≥ порога означает
    # «скруглить полностью». Судить её лестницей значит требовать выбрать
    # угол там, где угла не выбирают (geometry.capsule_refs).
    capsule = float(tokens["geometry"].get("capsule_min_pt", 1e9))
    stack_head = tuple(s.lower() for s in tokens["typography"].get("font_stack_head", []))
    press_max = float(tokens.get("motion", {}).get("press_response_ms_max", 120))
    tap_min = float(tokens.get("tap_target", {}).get("min_pt", 44)) \
        * float(adapter.get("pt_to_css_px", 1))
    cr_min = float(tokens.get("contrast", {}).get("min_ratio", 4.5))
    # AE18 · разделитель. Число берётся ИЗ БАЗЫ, а не из кода: правило с
    # зашитым числом стареет молча вместе с базой (ЗКН-Э002).
    sep_min = float(tokens.get("separator", {}).get("width_pt", 1))

    # ── СВЕТЛАЯ ОСЬ. Два свидетельства разного веса, и они РАНЖИРОВАНЫ.
    #
    # Замер (surfaces.allow_light — 89 светлых кадров, точное 16-битное
    # чтение с покадровой привязкой к белому и переводом P3→sRGB) вытесняет
    # публикацию: цитата описывает намерение, замер — то, что вышло на экран.
    # Палитра Apple (registry/standards/palette.json) остаётся ЗАПАСНЫМ
    # путём — для осей и проектов, где замера ещё нет. Смешивать их в одном
    # поле нельзя: два свидетельства разного веса под одним именем означают,
    # что через месяц никто не скажет, откуда взялось число.
    #
    # Нет ни замера, ни палитры — правило по светлой теме ВОЗДЕРЖИВАЕТСЯ и
    # говорит об этом вслух (ЗКН-Э008), а не молчит и не судит чужой осью.
    light_allow = [hex6(c) for c in (tokens.get("surfaces", {})
                                     .get("allow_light") or [])]
    light_src = "замер"
    if not light_allow:
        _pal = Path(__file__).resolve().parents[1] / "registry" / "standards" / "palette.json"
        if _pal.exists():
            try:
                _p = json.loads(_pal.read_text(encoding="utf-8"))
                light_allow = [hex6("#FFFFFF")] + [
                    hex6(v) for n in range(6, 0, -1)
                    for v in [_p.get("gray", {}).get(f"systemGray{n}", {}).get("light")]
                    if v]
                light_src = "палитра Apple (цитата)"
            except (ValueError, OSError):
                light_allow = []

    findings, files_n, looked, blind = [], 0, [], []
    # Ось проекта. Лестница поверхностей, запрет тени и лестница прозрачности
    # сняты с ТЁМНОЙ системы. Светлый проект этими правилами судить нечем:
    # приговор по чужой оси — это выдумка, а не строгость (ЗКН-Э001). Пока
    # ось не снята, такие правила ВОЗДЕРЖИВАЮТСЯ — и говорят об этом вслух.
    # Как только замер появляется в своде, они просыпаются сами.
    base = str(adapter.get("base", "dark")).lower()
    light_exempt = _light_exempt(tokens)
    ae2_msg = ("свечение/тень запрещены (box/text-shadow, drop-shadow) — "
               "глубина = СТУПЕНЬ ПОВЕРХНОСТИ. Замерено на обоих холстах: "
               "на чёрном (217 кадров) и на светлом (635 кромок, профиль "
               "холста у кромки — медиана 0.000)"
               if not light_exempt else
               "свечение/тень на чёрном холсте запрещены (box/text-shadow, "
               "drop-shadow) — глубина = ступень поверхности")
    abstained = {}
    if base == "light":
        allow = set(light_allow) | {hex6(c) for c in adapter.get("allow_extra", [])}
        for rule, ключ, чем in (
                ("AE1", light_allow, "лестница светлых поверхностей"),
                ("AE2", tokens.get("shadows", {}).get("light_depth"),
                 "норма глубины на светлом холсте"),
                ("AE9", tokens.get("opacity_ladder", {}).get("allow_light"),
                 "лестница прозрачности светлого стекла")):
            if rule in rules and not ключ:
                abstained[rule] = (f"проект объявлен светлым (base: light), "
                                   f"а {чем} департаментом не снята — "
                                   f"судить нечем")
        rules = [r for r in rules if r not in abstained]
    first_long, has_prm = None, False
    # AE17 копит по ВСЕМУ охвату: объявляет ли проект темы вообще и какие
    # поверхности из них выпадают. Один файл этого знать не может.
    has_theme, theme_orphans = False, []
    # AE19 копит по ВСЕМУ охвату: доля жёстких кеглей — свойство проекта,
    # а не строки. Построчный упрёк дал бы сотню находок и утопил остальные.
    fs_px, fs_scale, fs_first = 0, 0, None

    # ── ПРЕДПРОХОД: словарь переменных проекта ──────────────────────────────
    # Зачем. Все value-правила читали ЛИТЕРАЛ: `border-radius: 20px`. Зрелый
    # проект пишет `border-radius: var(--radius-lg)`, и департамент слеп на
    # него целиком. Проверено на чужих проектах: Hoppscotch получил 98.8 не
    # потому что близок к Apple, а потому что у него 25 переменных и четыре
    # литеральных фона. Инструмент мерил «сколько у вас плоского CSS», а не
    # «насколько вы близки к системе».
    #
    # Предпроход собирает объявления по ВСЕМУ охвату, потом подставляет их
    # в текст перед разбором — и восемнадцать правил оживают без единой
    # правки в себе.
    var_defs, var_ambiguous = _collect_vars(project_root, globs)
    # Объявления с темой и ролью — для суда над спорными переменными.
    var_decls, var_roles = _var_decls(project_root, globs)

    for g in globs:
        нашлось = 0
        for fp in sorted(glob.glob(str(project_root / g), recursive=True)):
            p = Path(fp)
            # .scss/.sass/.vue/.svelte добавлены не для полноты списка:
            # сканер их ОБЪЯВЛЯЛ, а линт молча пропускал, и проект на SCSS
            # получал отличный балл при нуле прочитанных файлов. Инструмент,
            # который хвалит за непрочитанное, хуже отсутствующего.
            if not p.is_file() or p.suffix not in (
                    ".css", ".scss", ".sass", ".html", ".htm",
                    ".tsx", ".ts", ".jsx", ".js", ".vue", ".svelte"):
                continue
            files_n += 1
            нашлось += 1
            raw = p.read_text(encoding="utf-8", errors="replace")
            t = strip_comments(raw, p.suffix)
            # Подстановка сохраняет ДЛИНУ текста, иначе номера строк уплывут
            # и адрес находки укажет не туда — ровно тот дефект, что нашёл
            # второй клиент. Проверено судом в обе стороны.
            t = _expand_vars(t, var_defs)
            rel = str(p.relative_to(project_root))
            looked.append(rel)

            if "AE1" in rules:
                for m in BG_PROP.finditer(t):
                    c = hex6(m.group(1))
                    if _in_print_scope(t, m.start()):
                        continue
                    # Граница предмета ОДНА на оба пути. Иначе фирменный
                    # акцент прощается через объявление переменной и
                    # обвиняется через литерал — департамент противоречил бы
                    # сам себе на одном и том же цвете.
                    if not _is_surface(c):
                        continue
                    if _in_light_scope(t, m.start()):
                        # СВЕТЛАЯ ТЕМА. Раньше правило здесь молчало: своей
                        # светлой лестницы у департамента не было, а судить
                        # светлый холст тёмной лестницей — нелепость.
                        # Теперь лестница есть — ОПУБЛИКОВАННАЯ Apple в
                        # альт-тексте образцов страницы цвета. Это не замер,
                        # и говорится это прямо: провенанс в тексте находки,
                        # чтобы вес свидетельства был виден.
                        if light_allow and c not in light_allow:
                            findings.append((
                                "AE1", rel, _line_of(t, m.start()),
                                f"фон {c} вне СВЕТЛОЙ лестницы поверхностей "
                                f"({' → '.join(light_allow)}) — 🍎 опубликовано "
                                f"Apple, /design/human-interface-guidelines/color"))
                        continue
                    if c not in allow:
                        лест = (light_allow if base == "light"
                                else tokens["surfaces"]["ladder"])
                        findings.append(("AE1", rel, _line_of(t, m.start()),
                                         f"фон {c} вне лестницы поверхностей "
                                         f"({' → '.join(лест)}"
                                         + (f", {light_src}" if base == "light" else "")
                                         + ")"))
            if "AE2" in rules:
                for m in SHADOW_DECL.finditer(t):
                    if not _shadow_is_outer(m.group(2)):
                        continue
                    # Запрет AE2 — про ЧЁРНЫЙ холст (в 217 кадрах теней на #000
                    # нет). Департамент уже проводит эту границу на живом проде
                    # (selftest: «чёрный drop в light — не AE2, в dark — AE2»).
                    # Когда селектор САМ называет светлую тему, холст известен
                    # статически, и файловое правило обязано судить так же.
                    if light_exempt and _in_light_scope(t, m.start()):
                        continue
                    findings.append(("AE2", rel, _line_of(t, m.start()), ae2_msg))
                for m in DROPSHADOW.finditer(t):
                    if light_exempt and _in_light_scope(t, m.start()):
                        continue
                    findings.append(("AE2", rel, _line_of(t, m.start()), ae2_msg))
            if "AE3" in rules:
                bigs = [(float(m.group(1)), m.start()) for m in RADIUS.finditer(t)
                        if rad_lim < float(m.group(1)) < capsule]
                if bigs and not SUPER.search(t):
                    v, pos = bigs[0]
                    findings.append(("AE3", rel, _line_of(t, pos),
                                     f"border-radius {v}px > {rad_lim:g}pt без формы суперэллипса (clip-path:path / corner-shape)"))
            if "AE4" in rules:
                for m in LSPX.finditer(t):
                    v = float(m.group(1))
                    if abs(v) > cap + 1e-9:
                        findings.append(("AE4", rel, _line_of(t, m.start()),
                                         f"letter-spacing {v}px — крышка поправки ±{cap}px; роль задаётся в em"))
            if "AE5" in rules:
                for m in FSIZE.finditer(t):
                    v = float(m.group(1))
                    if v not in sizes:
                        findings.append(("AE5", rel, _line_of(t, m.start()),
                                         f"font-size {v}px вне шкалы ролей {sorted(sizes)}"))
            if "AE6" in rules:
                # Двойник ищется по ЛЮБОЙ записи цвета: сокращённая форма —
                # тот же цвет и то же нарушение.
                for m in re.finditer(HEX, t):
                    why = forb.get(hex6(m.group(0)))
                    if why:
                        findings.append(("AE6", rel, _line_of(t, m.start()), why))
            if "AE7" in rules:
                for m in BACKDROP.finditer(t):
                    v = m.group(1)
                    if "blur(" in v.lower() and "saturate(" not in v.lower() and "var(" not in v.lower():
                        findings.append(("AE7", rel, _line_of(t, m.start()),
                                         "backdrop-filter: blur без saturate — стекло это размытие+насыщение, не мутная серость"))
            if "AE8" in rules:
                for m in MOTION.finditer(t):
                    v = m.group(1).lower()
                    if "var(" in v:
                        continue
                    dur = max((float(x) * (1000 if u == "s" else 1) for x, u in MS.findall(v)), default=0)
                    if dur >= min_ms and re.search(r"(?<![-\w])(ease|linear)(?![-\w(])", v):
                        findings.append(("AE8", rel, _line_of(t, m.start()),
                                         f"движение {dur:g}ms на дефолтной кривой — от {min_ms:g}ms положена измеренная (383ms · cubic-bezier(.32,.72,0,1))"))
            if "AE9" in rules:
                for m in OPACITY.finditer(t):
                    v = float(m.group(1))
                    if not any(abs(v - a) <= op_tol for a in op_allow):
                        findings.append(("AE9", rel, _line_of(t, m.start()),
                                         f"opacity {v:g} вне лестницы {op_allow} (метки iOS + измеренное стекло)"))
            if "AE10" in rules:
                for m in FFAM.finditer(t):
                    v = m.group(1).strip().strip("'\"").lower()
                    if v.startswith(("var(", "inherit", "monospace")):
                        continue
                    # Внутри @font-face `font-family` — это ИМЯ подключаемой
                    # гарнитуры, а не стек ролей. Системный стек здесь не просто
                    # не нужен, он синтаксически бессмыслен: описывается файл
                    # шрифта. Правило про первую позицию стека к дескриптору
                    # @font-face не относится.
                    if _in_font_face(t, m.start()):
                        continue
                    if stack_head and not v.startswith(stack_head):
                        findings.append(("AE10", rel, _line_of(t, m.start()),
                                         f"font-family не начинается с системного стека {list(stack_head)} — подмена первой позиции ломает метрики и трекинг"))
            if "AE19" in rules and p.suffix in (".css", ".scss", ".tsx",
                                                ".jsx", ".ts", ".js"):
                for m in FS_PX.finditer(t):
                    if _in_print_scope(t, m.start()):
                        continue
                    if float(m.group(1)) == 0:
                        continue
                    fs_px += 1
                    if fs_first is None:
                        fs_first = (rel, _line_of(t, m.start()))
                fs_scale += len(FS_SCALE.findall(t))
            if "AE17" in rules and p.suffix in (".css", ".scss"):
                if THEME_SCOPE.search(t):
                    has_theme = True
                for m in BG_PROP.finditer(t):
                    # Жёсткий цвет поверхности вне любой темы. var(--…) не
                    # трогаем: переменная и есть механизм пары.
                    if _in_theme_scope(t, m.start()) or _in_print_scope(t, m.start()):
                        continue
                    col = hex6(m.group(1))
                    # Цвет ВНЕ лестницы — предмет AE1, и там он уже назван
                    # вместе с целью. Повторить его здесь значит наказать
                    # дважды за одну строку и раздуть долг — ровно та ошибка,
                    # что была в формуле балла. AE17 берёт только ЗАКОННУЮ
                    # поверхность, у которой нет пары: это и есть новое
                    # знание, которого не даёт ни одно другое правило.
                    if col not in allow:
                        continue
                    theme_orphans.append((rel, _line_of(t, m.start()), col))
            if "AE16" in rules and p.suffix in (".css", ".scss"):
                # Разбор по блокам: заливка судится только там, где селектор
                # объявляет активный пункт навигации.
                for blk in re.finditer(r"([^{}]+)\{([^{}]*)\}", t):
                    sel, body = blk.group(1), blk.group(2)
                    if not (NAV_SEL.search(sel) and ACTIVE_SEL.search(sel)):
                        continue
                    for d in FILL_DECL.finditer(body):
                        val = d.group(1).strip()
                        if NOFILL.match(val):
                            continue
                        findings.append((
                            "AE16", rel,
                            _line_of(t, blk.start(2) + d.start()),
                            f"заливка {val} под активным пунктом навигации — "
                            f"в 37 кадрах таб-бара Apple заливки нет ни одной; "
                            f"активный отличается ТОНОМ"))
                        break
            if "AE11" in rules:
                for m in RADIUS.finditer(t):
                    v = float(m.group(1))
                    if rad_ladder and v not in rad_ladder and v < capsule:
                        findings.append(("AE11", rel, _line_of(t, m.start()),
                                         f"border-radius {v:g}px вне измеренной лестницы {sorted(rad_ladder)}"))
            if "AE20" in rules:
                for m in UPPERCASE.finditer(t):
                    findings.append((
                        "AE20", rel, _line_of(t, m.start()),
                        "text-transform: uppercase — капсы у Apple нет: "
                        "заголовок группы идёт Title Case (§3.4), капс это "
                        "iOS 12 (typography.caps_lock)"))
            if "AE13" in rules:
                if "prefers-reduced-motion" in t.lower():
                    has_prm = True
                if first_long is None:
                    for m in MOTION.finditer(t):
                        v = m.group(1).lower()
                        if "var(" in v:
                            continue
                        dur = max((float(x) * (1000 if u == "s" else 1) for x, u in MS.findall(v)), default=0)
                        if dur >= min_ms:
                            first_long = (rel, _line_of(t, m.start()))
                            break
            if "AE12" in rules:
                for m in ACTIVE_BLOCK.finditer(t):
                    body = m.group(1)
                    if "var(" in body.lower():
                        continue
                    dur = max((float(x) * (1000 if u == "s" else 1) for x, u in MS.findall(body)), default=0)
                    if dur > press_max:
                        findings.append(("AE12", rel, _line_of(t, m.start()),
                                         f":active отвечает {dur:g}ms — нажатие обязано ответить ≤{press_max:g}ms (мёртвая рука)"))

            # AE14/AE15 судят только .css: разбор по блокам selector{body}, а
            # в TSX фигурные скобки принадлежат JSX и разбор блоков дал бы
            # ложные пары. Инлайн-стили TSX — отдельная работа, не эта.
            # Ворота перечисляют ВСЕ правила, судящие по блокам css. Правило,
            # молча зависящее от включённости соседа, не работает у клиента,
            # который сосед не включил, — и молчит вместо красного.
            if p.suffix == ".css" and ({"AE14", "AE15", "AE18"} & set(rules)):
                for bm in BLOCK.finditer(t):
                    sel, body = bm.group(1), bm.group(2)
                    if ("AE14" in rules and INTERACTIVE.search(sel)
                            and not EXEMPT_SEL.search(sel)):
                        for sm in SIZEDECL.finditer(body):
                            v = float(sm.group(1))
                            if v < tap_min - 1e-9:
                                findings.append(("AE14", rel,
                                    _line_of(t, bm.start(2) + sm.start()),
                                    f"цель касания {v:g}px — норма свода минимум "
                                    f"{tap_min:g}px (44×44pt, 🍎 живой HIG)"))
                    if "AE18" in rules:
                        for hm in HAIRLINE.finditer(body):
                            v = float(hm.group("v") or hm.group("v2"))
                            if v < sep_min - 1e-9:
                                findings.append(("AE18", rel,
                                    _line_of(t, bm.start(2) + hm.start()),
                                    f"разделитель {v:g}px тоньше замеренного "
                                    f"{sep_min:g}pt — полпикселя исчезает на "
                                    f"экране 1x и на печати (📐 замер 217 кадров, "
                                    f"registry/standards/tokens.json separator)"))
                    if "AE15" in rules:
                        fg, bg = FG_DECL.search(body), BG_DECL.search(body)
                        if fg and bg:
                            ratio = contrast_ratio(fg.group(1), bg.group(1))
                            if ratio < cr_min - 1e-9:
                                findings.append(("AE15", rel,
                                    _line_of(t, bm.start(2) + fg.start()),
                                    f"контраст {ratio:.2f}:1 ({fg.group(1)} на "
                                    f"{bg.group(1)}) ниже нормы свода {cr_min:g}:1 "
                                    f"(🍎 живой HIG)"))

        if not нашлось:
            blind.append(g)

    if "AE19" in rules and fs_px >= 5 and fs_px > fs_scale and fs_first:
        # Порог объявлен: пять кеглей — это уже шкала, а не единичный
        # случай; большинство жёстких — это выбор проекта, а не недосмотр.
        # Проекту, где масштабируемых больше, правило молчит: он уже решил
        # задачу, а придираться к остаткам значит наказывать за движение
        # в верную сторону.
        findings.append((
            "AE19", fs_first[0], fs_first[1],
            f"кегль задан жёстким px в {fs_px} местах против {fs_scale} "
            f"масштабируемых — интерфейс не переживёт Dynamic Type; "
            f"🍎 Apple растит кегль от xSmall к xxxLarge на 18 % "
            f"(34→40 pt у Large Title), на ступенях доступности кратно "
            f"(/design/human-interface-guidelines/typography)"))

    if "AE1" in rules:
        # Спорная переменная судится ПО ОБЪЯВЛЕНИЮ: адрес настоящий, тема
        # известна из области. Однозначная сюда тоже попадает — и это верно:
        # объявление вне темы обязано лежать на тёмной лестнице, потому что
        # база департамента снята с тёмного холста.
        for rel_, ln_, c_, чья, лестница in _judge_var_surfaces(
                var_decls, var_roles, allow, light_allow, set(var_defs)):
            findings.append((
                "AE1", rel_, ln_,
                f"переменная фона {c_} вне {чья} лестницы поверхностей "
                f"({' → '.join(лестница)})"))

    for rule_, rel_, ln_, why_ in _judge_var_scales(
            var_decls, var_roles, tokens, rules, set(var_defs)):
        findings.append((rule_, rel_, ln_, why_))

    if "AE17" in rules and has_theme and theme_orphans:
        # Правило говорит ТОЛЬКО проектам, которые уже завели темы. Проекту
        # без тем оно молчит: там нет обязательства, которое нарушено, —
        # это выбор охвата, а не дефект. Судить проект за отсутствие того,
        # чего он не обещал, значит завалить его шумом.
        for rel, ln, col in theme_orphans:
            findings.append((
                "AE17", rel, ln,
                f"поверхность {col} задана одним значением на обе темы — "
                f"проект темы объявляет, но эта поверхность из них выпадает; "
                f"🍎 Apple: значения системных цветов меняются от выпуска "
                f"к выпуску, жёсткое одно на обе темы устаревает молча "
                f"(/design/human-interface-guidelines/color)"))

    if "AE13" in rules and first_long and not has_prm:
        findings.append(("AE13", first_long[0], first_long[1],
                         "в охвате есть движение ≥%gms, но нет ни одного @media (prefers-reduced-motion) — Reduce Motion обязателен (HIG Motion)" % min_ms))

    return {"mode": mode, "files": files_n, "findings": findings,
            "rules": rules, "paths": looked,
            # НЕРАЗОБРАННЫЕ переменные. Объявленные по-разному в темах, они
            # не подставляются: выбрать одну сторону значит судить проект по
            # половине его правды. Но и промолчать о них нельзя — иначе балл
            # выглядит лучше, чем есть, а департамент выдаёт непроверенное
            # за чистое (ЗКН-Э001).
            "vars_resolved": len(var_defs),
            "vars_unresolved": var_ambiguous,
            # Глоб, не нашедший НИ ОДНОГО файла, обязан сказать о себе.
            # Половина охвата, ведущая в несуществующий каталог, до сих пор
            # не сообщала о себе ничем — и её пустота читалась как чистота.
            "blind_globs": blind, "abstained": abstained, "base": base}


def render(res: dict, adapter_name: str) -> str:
    out = [f"# BXE · отчёт линта · адаптер `{adapter_name}` · режим {res['mode']}",
           f"Файлов просмотрено: {res['files']} · правила: {', '.join(res['rules'])} · находок: {len(res['findings'])}", ""]

    # Воздержавшиеся правила называются ПЕРВЫМИ. Правило, промолчавшее из-за
    # неснятой оси, и правило, ничего не нашедшее, — разные вещи, и читатель
    # обязан их различать, не заглядывая в исходники.
    for rule, why in sorted((res.get("abstained") or {}).items()):
        out.append(f"⊘ {rule} воздержалось: {why}")
    if res.get("abstained"):
        out.append("")

    if res.get("blind_globs"):
        out.append("⚠ охват смотрит в пустоту — эти глобы не нашли ни одного файла:")
        for g in res["blind_globs"]:
            out.append(f"- `{g}`")
        out.append("")

    if not res["files"]:
        # ЗКН-Э006: пустой обход не есть доказательство чистоты.
        #
        # Родословная (02.08.2026): линт с неверным корнем печатал «Чисто.» и
        # возвращал ноль. CI с опечаткой в пути был бы зелёным вечно — то есть
        # закон против пустого обхода существовал, а главный орган его не
        # исполнял. Ноль находок при нуле файлов означает промах адреса, а не
        # порядок в коде. Глобы, не нашедшие ничего, названы выше поимённо.
        out.append("КРАСНЫЙ · обойдено 0 файлов — промах адреса, а не чистота "
                   "(ЗКН-Э006). Проверьте PROJECT_ROOT и глобы паспорта.")
    elif not res["rules"]:
        # Все правила охвата воздержались (ЗКН-Э008). Находок ноль — но не
        # потому, что чисто, а потому, что судить было нечем.
        out.append("ОТКАЗ: все правила охвата воздержались — вердикта нет.")
    elif not res["findings"]:
        out.append("Чисто по правилам, которые судили."
                   if res.get("abstained") else "Чисто.")
    else:
        by = {}
        for r, f, ln, msg in res["findings"]:
            by.setdefault(r, []).append((f, ln, msg))
        for r in sorted(by):
            out.append(f"## {r} · {len(by[r])}")
            for f, ln, msg in by[r][:120]:
                out.append(f"- `{f}:{ln}` — {msg}")
            if len(by[r]) > 120:
                out.append(f"- … ещё {len(by[r]) - 120}")
            out.append("")
    return "\n".join(out) + "\n"


def main(root: Path, adapter_name: str, mode: str, out_file: str = None, project_root: Path = None) -> int:
    adapter = json.loads((root / "adapters" / f"{adapter_name}.json").read_text(encoding="utf-8"))
    tokens = json.loads((root / "registry" / "standards" / "tokens.json").read_text(encoding="utf-8"))
    project_root = project_root or root.parent
    res = run(root, adapter, tokens, mode, project_root)
    text = render(res, adapter_name)
    if out_file:
        Path(out_file).write_text(text, encoding="utf-8")
    print(text)
    # Пустой обход — красный в ЛЮБОМ режиме (ЗКН-Э006). Ноль находок при нуле
    # файлов есть промах адреса; вернуть на это ноль значит подтвердить чистоту,
    # которой никто не видел.
    if not res["files"]:
        return 1
    return 1 if (mode == "strict" and res["findings"]) else 0


if __name__ == "__main__":
    import argparse
    import os
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--mode", choices=["strict", "report"], default="report")
    ap.add_argument("--out")
    # Корень проекта объявлялся только переменной окружения из watch.py, а
    # CLI молча падал в root.parent — соседний каталог рядом с деревом
    # департамента. Ручной прогон обходил ноль файлов и печатал «Чисто».
    ap.add_argument("--project-root", default=os.environ.get("PROJECT_ROOT"))
    a = ap.parse_args()
    sys.exit(main(Path(__file__).resolve().parents[1], a.adapter, a.mode, a.out,
                  Path(a.project_root).resolve() if a.project_root else None))
