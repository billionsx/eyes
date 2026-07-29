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

Отступы правилом НЕ проверяются — ключевой замер: точечной сетки НЕТ,
шаг CSS = ⅓pt при @3x; «линт сетки отступов» противоречил бы измерениям.

Режимы: strict — любое error-нарушение = exit 1; report — только отчёт.
"""
import glob
import json
import re
import sys
from pathlib import Path


def strip_comments(text: str, suffix: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)          # CSS / JS block
    if suffix in (".ts", ".tsx", ".js", ".jsx"):
        text = re.sub(r"(?<![:\\])//[^\n]*", " ", text)          # // строка (не https://)
    if suffix in (".html", ".htm"):
        text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    return text


HEX = r"#[0-9A-Fa-f]{6}\b"
BG_PROP = re.compile(r"(?:background|background-color)\s*:\s*(" + HEX + ")", re.I)
SHADOW = re.compile(r"\b(?:box-shadow|text-shadow)\s*:\s*(?!\s*none)|drop-shadow\(", re.I)
RADIUS = re.compile(r"border-radius\s*:\s*([\d.]+)px", re.I)
SUPER = re.compile(r"clip-path\s*:\s*path\(|corner-shape", re.I)
LSPX = re.compile(r"letter-spacing\s*:\s*(-?[\d.]+)px", re.I)
FSIZE = re.compile(r"font-size\s*:\s*([\d.]+)px", re.I)
BACKDROP = re.compile(r"backdrop-filter\s*:\s*([^;}\n]+)", re.I)
MOTION = re.compile(r"\b(?:transition|animation)\s*:\s*([^;}\n]+)", re.I)
MS = re.compile(r"([\d.]+)\s*(ms|s)\b")
OPACITY = re.compile(r"(?<![-\w])opacity\s*:\s*(0?\.\d+|[01])(?![\d.])", re.I)
FFAM = re.compile(r"font-family\s*:\s*([^;}\n]+)", re.I)
ACTIVE_BLOCK = re.compile(r":active[^{]*\{([^}]*)\}", re.I | re.S)


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def run(root: Path, adapter: dict, tokens: dict, mode: str, project_root: Path) -> dict:
    scope = adapter.get(mode, {}) or {}
    globs = scope.get("globs", [])
    rules = scope.get("rules", ["AE1", "AE2", "AE3", "AE4", "AE6"])
    allow = {c.upper() for c in tokens["surfaces"]["allow"]} | {c.upper() for c in adapter.get("allow_extra", [])}
    forb = {c.upper(): why for c, why in tokens.get("forbidden_colors", {}).items()}
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

    findings, files_n, looked = [], 0, []
    first_long, has_prm = None, False
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
                    c = m.group(1).upper()
                    if c not in allow:
                        findings.append(("AE1", rel, _line_of(t, m.start()),
                                         f"фон {c} вне лестницы поверхностей ({' → '.join(tokens['surfaces']['ladder'])})"))
            if "AE2" in rules:
                for m in SHADOW.finditer(t):
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
                for c, why in forb.items():
                    for m in re.finditer(re.escape(c), t, re.I):
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
                    if stack_head and not v.startswith(stack_head):
                        findings.append(("AE10", rel, _line_of(t, m.start()),
                                         f"font-family не начинается с системного стека {list(stack_head)} — подмена первой позиции ломает метрики и трекинг"))
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

    if "AE13" in rules and first_long and not has_prm:
        findings.append(("AE13", first_long[0], first_long[1],
                         "в охвате есть движение ≥%gms, но нет ни одного @media (prefers-reduced-motion) — Reduce Motion обязателен (HIG Motion)" % min_ms))

    return {"mode": mode, "files": files_n, "findings": findings,
            "rules": rules, "paths": looked}


def render(res: dict, adapter_name: str) -> str:
    out = [f"# BXE · отчёт линта · адаптер `{adapter_name}` · режим {res['mode']}",
           f"Файлов просмотрено: {res['files']} · правила: {', '.join(res['rules'])} · находок: {len(res['findings'])}", ""]
    if not res["findings"]:
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
    return 1 if (mode == "strict" and res["findings"]) else 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--mode", choices=["strict", "report"], default="report")
    ap.add_argument("--out")
    a = ap.parse_args()
    sys.exit(main(Path(__file__).resolve().parents[1], a.adapter, a.mode, a.out))
