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


def strip_comments(text: str, suffix: str) -> str:
    text = re.sub(r"/\*.*?\*/", _blank, text, flags=re.S)        # CSS / JS block
    if suffix in (".ts", ".tsx", ".js", ".jsx"):
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


# AE17. ОБЛАСТЬ ТЕМЫ. Объявление считается тематическим, если стоит внутри
# любого механизма смены темы: медиазапрос схемы, атрибут темы, класс темы.
# Список закрытый и объявленный: угадывать «похоже на тему» нельзя.
THEME_SCOPE = re.compile(
    r"prefers-color-scheme|data-theme|\[data-[a-z-]*theme|"
    r"(?:^|[\s,.:#])(?:light|dark)(?:-mode|-theme)?\b(?=[^{]*$)", re.I)


def _in_theme_scope(text: str, pos: int) -> bool:
    """Объявление адресовано КОНКРЕТНОЙ теме, а не обеим сразу."""
    return any(THEME_SCOPE.search(h) for h in _enclosing_headers(text, pos))


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
    stack_head = tuple(s.lower() for s in tokens["typography"].get("font_stack_head", []))
    press_max = float(tokens.get("motion", {}).get("press_response_ms_max", 120))
    tap_min = float(tokens.get("tap_target", {}).get("min_pt", 44)) \
        * float(adapter.get("pt_to_css_px", 1))
    cr_min = float(tokens.get("contrast", {}).get("min_ratio", 4.5))
    # AE18 · разделитель. Число берётся ИЗ БАЗЫ, а не из кода: правило с
    # зашитым числом стареет молча вместе с базой (ЗКН-Э002).
    sep_min = float(tokens.get("separator", {}).get("width_pt", 1))

    # Светлая лестница берётся из палитры, а не из базы замера: она
    # ОПУБЛИКОВАНА Apple, а не снята департаментом, и смешивать два разных
    # по весу свидетельства в одном поле нельзя. Нет палитры — правило по
    # светлой теме молчит, как молчало раньше.
    light_allow = []
    _pal = Path(__file__).resolve().parents[1] / "registry" / "standards" / "palette.json"
    if _pal.exists():
        try:
            _p = json.loads(_pal.read_text(encoding="utf-8"))
            light_allow = ["#FFFFFF"] + [
                v for n in range(6, 0, -1)
                for v in [_p.get("gray", {}).get(f"systemGray{n}", {}).get("light")]
                if v]
        except (ValueError, OSError):
            light_allow = []

    findings, files_n, looked = [], 0, []
    first_long, has_prm = None, False
    # AE17 копит по ВСЕМУ охвату: объявляет ли проект темы вообще и какие
    # поверхности из них выпадают. Один файл этого знать не может.
    has_theme, theme_orphans = False, []
    for g in globs:
        for fp in sorted(glob.glob(str(project_root / g), recursive=True)):
            p = Path(fp)
            if not p.is_file() or p.suffix not in (".css", ".html", ".htm", ".tsx", ".ts", ".jsx", ".js"):
                continue
            files_n += 1
            raw = p.read_text(encoding="utf-8", errors="replace")
            t = strip_comments(raw, p.suffix)
            rel = str(p.relative_to(project_root))
            looked.append(rel)

            if "AE1" in rules:
                for m in BG_PROP.finditer(t):
                    c = hex6(m.group(1))
                    if _in_print_scope(t, m.start()):
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
                        findings.append(("AE1", rel, _line_of(t, m.start()),
                                         f"фон {c} вне лестницы поверхностей ({' → '.join(tokens['surfaces']['ladder'])})"))
            if "AE2" in rules:
                for m in SHADOW_DECL.finditer(t):
                    if not _shadow_is_outer(m.group(2)):
                        continue
                    # Запрет AE2 — про ЧЁРНЫЙ холст (в 217 кадрах теней на #000
                    # нет). Департамент уже проводит эту границу на живом проде
                    # (selftest: «чёрный drop в light — не AE2, в dark — AE2»).
                    # Когда селектор САМ называет светлую тему, холст известен
                    # статически, и файловое правило обязано судить так же.
                    if _in_light_scope(t, m.start()):
                        continue
                    findings.append(("AE2", rel, _line_of(t, m.start()),
                                     "свечение/тень на чёрном холсте запрещены (box/text-shadow, drop-shadow) — глубина = ступень поверхности"))
                for m in DROPSHADOW.finditer(t):
                    if _in_light_scope(t, m.start()):
                        continue
                    findings.append(("AE2", rel, _line_of(t, m.start()),
                                     "свечение/тень на чёрном холсте запрещены (box/text-shadow, drop-shadow) — глубина = ступень поверхности"))
            if "AE3" in rules:
                bigs = [(float(m.group(1)), m.start()) for m in RADIUS.finditer(t) if float(m.group(1)) > rad_lim]
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
                    if rad_ladder and v not in rad_ladder:
                        findings.append(("AE11", rel, _line_of(t, m.start()),
                                         f"border-radius {v:g}px вне измеренной лестницы {sorted(rad_ladder)}"))
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
            "rules": rules, "paths": looked}


def render(res: dict, adapter_name: str) -> str:
    out = [f"# BXE · отчёт линта · адаптер `{adapter_name}` · режим {res['mode']}",
           f"Файлов просмотрено: {res['files']} · правила: {', '.join(res['rules'])} · находок: {len(res['findings'])}", ""]
    if not res["files"]:
        # ЗКН-Э006: пустой обход не есть доказательство чистоты.
        #
        # Родословная (02.08.2026): линт с неверным корнем печатал «Чисто.» и
        # возвращал ноль. CI с опечаткой в пути был бы зелёным вечно — то есть
        # закон против пустого обхода существовал, а главный орган его не
        # исполнял. Ноль находок при нуле файлов означает промах адреса, а не
        # порядок в коде.
        out.append("КРАСНЫЙ · обойдено 0 файлов — промах адреса, а не чистота "
                   "(ЗКН-Э006). Проверьте PROJECT_ROOT и глобы паспорта.")
    elif not res["findings"]:
        out.append("Чисто.")
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--mode", choices=["strict", "report"], default="report")
    ap.add_argument("--out")
    a = ap.parse_args()
    sys.exit(main(Path(__file__).resolve().parents[1], a.adapter, a.mode, a.out))
