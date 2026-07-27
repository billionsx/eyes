#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ЖИВОЙ ВЗГЛЯД (ст. 37.3). Видеть приложение в реальном режиме — не кадром.

Режим --live (носитель: CI): headless-Chromium (Playwright) открывает каждую
страницу registry/live-sources.json, ждёт networkidle и снимает НАСТОЯЩИЙ DOM:
для выборки видимых элементов — селектор-путь, backgroundColor, boxShadow /
textShadow, backdropFilter, fontFamily, fontSize, letterSpacing, borderRadius,
transition. Дамп: registry/live/<slug>.json (факты, не картинка).

Сверка check_dump — те же законы, что у линта, но по ЖИВЫМ вычисленным
значениям: AE1 фон вне лестницы · AE2 тень/свечение на чёрном · AE6 тёплый
двойник · AE7 blur без saturate · AE10 чужой шрифт первой позицией.
Отчёт: registry/live/REPORT.md (советник; храповик — после стабилизации).
Мок-режим (--mock dump.json) судится офлайн: механизм доказан без браузера.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

JS_SNAPSHOT = """
() => {
  const out = [], seen = new Set();
  const els = Array.from(document.querySelectorAll('body *')).slice(0, 4000);
  for (const el of els) {
    const r = el.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    const cs = getComputedStyle(el);
    const rec = {
      sel: el.tagName.toLowerCase() + (el.className && typeof el.className === 'string'
            ? '.' + el.className.trim().split(/\\s+/).slice(0,2).join('.') : ''),
      backgroundColor: cs.backgroundColor, boxShadow: cs.boxShadow,
      textShadow: cs.textShadow, backdropFilter: cs.backdropFilter || cs.webkitBackdropFilter,
      fontFamily: cs.fontFamily, fontSize: cs.fontSize,
      letterSpacing: cs.letterSpacing, borderRadius: cs.borderRadius,
      transition: cs.transitionDuration + '|' + cs.transitionTimingFunction
    };
    const key = JSON.stringify(rec);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(rec);
    if (out.length >= %LIMIT%) break;
  }
  return out;
}
"""


def _rgb_to_hex(v: str):
    m = re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)", v or "")
    if not m:
        return None, None
    a = float(m.group(4)) if m.group(4) is not None else 1.0
    return "#%02X%02X%02X" % (int(m.group(1)), int(m.group(2)), int(m.group(3))), a


NONTEXT = {"svg", "path", "circle", "rect", "line", "polyline", "polygon", "ellipse", "g", "use", "defs", "img", "video", "canvas"}


def _dark_drop_shadow(v: str) -> bool:
    """Чёрная выпадающая тень (запрещена на чёрном холсте); белые inset-блики стекла законны."""
    if not v or v == "none":
        return False
    for part in re.split(r",(?![^()]*\))", v):
        if "inset" in part:
            continue
        m = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", part)
        if m and max(int(m.group(1)), int(m.group(2)), int(m.group(3))) < 0x60:
            return True
    return False


def check_dump(elements: list, tokens: dict, theme: str = "dark") -> list:
    finds = []
    ladder = {c.upper() for c in tokens["surfaces"]["allow"]} | {"#1C1C1C", "#2C2C2C", "#181818", "#111111"}
    stack = tuple(s.lower() for s in tokens["typography"]["font_stack_head"])
    for el in elements:
        sel = el.get("sel", "?")
        hx, a = _rgb_to_hex(el.get("backgroundColor", ""))
        if hx and a == 1.0 and hx not in ladder:
            if hx == "#8E8E8E":
                finds.append(("AE6", sel, f"живой тёплый двойник {hx}"))
            elif max(int(hx[i:i+2], 16) for i in (1, 3, 5)) < 0x60:
                finds.append(("AE1", sel, f"живой тёмный фон {hx} вне лестницы"))
        for prop in ("boxShadow", "textShadow"):
            v = el.get(prop) or "none"
            if theme == "dark" and _dark_drop_shadow(v):  # ст.10 — канон ТЁМНОГО холста; в light тени законны
                finds.append(("AE2", sel, f"чёрная выпадающая тень на чёрном холсте: {v[:80]}"))
        bf = (el.get("backdropFilter") or "").lower()
        if "blur(" in bf and "saturate(" not in bf:
            finds.append(("AE7", sel, "живое стекло: blur без saturate"))
        tag = sel.split(".")[0].split(":")[0]
        ff = (el.get("fontFamily") or "").lower().strip().strip('"\'')
        if tag not in NONTEXT and ff and not ff.startswith(stack):
            finds.append(("AE10", sel, f"живой шрифт первой позицией: {ff.split(',')[0][:40]}"))
    return finds


def _report(root: Path, results: dict):
    md = ["# ЖИВОЙ ВЗГЛЯД · отчёт (советник)",
          f"Снято: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · настоящий DOM+computed, не кадры.", ""]
    for slug, r in results.items():
        md.append(f"## {r['url']}")
        md.append(f"элементов снято: {r['elements']} · находок: {len(r['findings'])}")
        if r.get("note"):
            md.append(f"сбой: {r['note']}")
        md.append(f"диагностика: {json.dumps(r.get('diag'), ensure_ascii=False)}")
        by = {}
        for rule, sel, why in r["findings"]:
            by.setdefault(rule, []).append((sel, why))
        for rule in sorted(by):
            md.append(f"- **{rule}** · {len(by[rule])}: " + "; ".join(f"`{s2}` ({w[:60]})" for s2, w in by[rule][:4]))
        md.append("")
    (root / "registry" / "live" / "REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def run_live(root: Path) -> dict:
    from playwright.sync_api import sync_playwright
    import sys as _s
    _s.path.insert(0, str(Path(__file__).resolve().parent))
    import projects  # noqa: E402
    cfg = json.loads((root / "registry" / "live-sources.json").read_text(encoding="utf-8"))
    cfg["pages"] = projects.live_pages(root) or cfg.get("pages", [])
    tokens = json.loads((root / "registry" / "standards" / "tokens.json").read_text(encoding="utf-8"))
    out = root / "registry" / "live"
    out.mkdir(exist_ok=True)
    js = JS_SNAPSHOT.replace("%LIMIT%", str(cfg.get("sample_limit", 400)))
    results = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 393, "height": 852}, device_scale_factor=3,
                        color_scheme="dark",  # канон ст.10 — тёмный холст; headless по умолчанию light
                        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) "
                                   "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1")
        for url in cfg["pages"]:
            slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"https?://", "", url).strip("/").lower()) or "root"
            try:
                pg.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:  # SPA: ждём реального монтирования дерева
                    pg.wait_for_function("document.querySelectorAll('body *').length > 50", timeout=20000)
                except Exception:
                    pg.wait_for_timeout(4000)
                els = pg.evaluate(js)
            except Exception as e:
                results[slug] = {"url": url, "elements": 0, "findings": [], "note": f"{type(e).__name__}: {str(e)[:160]}"}
                continue
            diag = pg.evaluate("() => ({url: location.href, title: document.title,"
                                   " theme: document.documentElement.getAttribute('data-theme') || 'dark',"
                                   " ready: document.readyState, htmlLen: document.documentElement.outerHTML.length,"
                                   " bodyChildren: document.body ? document.body.childElementCount : -1})")
            finds = check_dump(els, tokens, theme=diag.get("theme", "dark"))
            (out / f"{slug}.json").write_text(json.dumps(
                {"url": url, "elements": els, "findings": finds, "diag": diag}, ensure_ascii=False), encoding="utf-8")
            results[slug] = {"url": url, "elements": len(els), "findings": finds, "diag": diag}
        b.close()
    _report(root, results)
    with (root / "registry" / "state" / "CHANGELOG.md").open("a", encoding="utf-8") as f:
        f.write("### живой взгляд\n" + "".join(
            f"- {r['url']}: элементов {r['elements']} · находок {len(r['findings'])}\n" for r in results.values()) + "\n")
    return results


if __name__ == "__main__":
    if "--mock" in sys.argv:
        dump = json.loads(Path(sys.argv[sys.argv.index("--mock") + 1]).read_text(encoding="utf-8"))
        tokens = json.loads((ROOT / "registry" / "standards" / "tokens.json").read_text(encoding="utf-8"))
        for f in check_dump(dump.get("elements", dump), tokens):
            print(*f)
    elif "--live" in sys.argv:
        r = run_live(ROOT)
        print("живой взгляд:", " · ".join(f"{k}: элементов {v['elements']}, находок {len(v['findings'])}" for k, v in r.items()))
    else:
        print("режимы: --live (CI, Playwright) · --mock dump.json (суд)")
