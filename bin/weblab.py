#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ВЕБ-АТЛАС (лендинги Apple). Логика, архитектура и закономерности
презентаций apple.com — детерминированно, без ИИ.

По каждому адресу registry/web-sources.json:
  ПАСПОРТ СТРУКТУРЫ — секции страницы (порядок и имена секций из классов
    section-* / unit-wrapper), счёт медиа (img/video), CTA (ссылки-кнопки),
    ribbon/навигация, заголовочная иерархия. Это архитектура лендинга.
  ЗАКОНЫ ТИПОГРАФИКИ — из подключённых CSS выжимаются правила классов
    typography-*: font-size / line-height / letter-spacing / font-weight —
    прямые числа кита веб-презентаций Apple, адрес css:<файл>:<класс>.
  ЗНАНИЕ — текст страницы через общий конвейер (снимок + нормативная выжимка).
Паспорта: registry/weblab/<slug>.json · законы: library/web-landings.jsonl ·
свод закономерностей: state/WEBLAB.md (частота секций по всем страницам —
это и есть «кит лендингов»: какие блоки и в каком порядке строит Apple).
"""
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawler import UA, _robots_ok, _slug  # noqa: E402

DELAY = 1.2
SEC = re.compile(r'<section[^>]*class="([^"]+)"', re.I)
DATA_MOD = re.compile(r'data-(?:module-template|analytics-section-engagement)="([^"]+)"', re.I)
CSSL = re.compile(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', re.I)
IMG = re.compile(r"<img\b", re.I)
VID = re.compile(r"<video\b", re.I)
CTA = re.compile(r'class="[^"]*\bbutton\b[^"]*"', re.I)
H = re.compile(r"<h([1-6])\b", re.I)
TYPO = re.compile(r"\.([a-z0-9-]*(?:typography|headline|eyebrow|subhead|copy)[a-z0-9-]*)\s*\{([^}]*)\}", re.I)
PROP = re.compile(r"(font-size|line-height|letter-spacing|font-weight)\s*:\s*([^;]+)", re.I)


def _get(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def parse_page(html: str):
    secs = []
    for m in SEC.finditer(html):
        cls = [c for c in m.group(1).split() if c.startswith("section-")]
        if cls:
            secs.append(cls[0])
    mods = DATA_MOD.findall(html)
    return {"sections": secs[:60], "modules": mods[:60],
            "imgs": len(IMG.findall(html)), "videos": len(VID.findall(html)),
            "cta": len(CTA.findall(html)),
            "h_levels": dict(Counter(H.findall(html))),
            "css": [u for u in CSSL.findall(html) if ".css" in u][:6]}


def mine_typography(css: str, css_name: str):
    laws = []
    for m in TYPO.finditer(css):
        cls, body = m.group(1), m.group(2)
        props = {k.lower(): v.strip() for k, v in PROP.findall(body)}
        if "font-size" in props:
            laws.append({"class": cls, **props, "at": f"css:{css_name}:{cls}"})
    return laws


def run(root: Path, limit=200, fixtures: Path = None) -> dict:
    reg = root / "registry"
    srcs = json.loads((reg / "web-sources.json").read_text(encoding="utf-8"))["pages"]
    out = reg / "weblab"
    out.mkdir(exist_ok=True)
    stf = out / "state.json"
    st = json.loads(stf.read_text(encoding="utf-8")) if stf.exists() else {}
    lib = reg / "library" / "web-landings.jsonl"
    lib.parent.mkdir(exist_ok=True)
    sec_freq, mod_freq = Counter(), Counter()
    done = laws_n = 0
    typo_seen = set()
    if lib.exists():
        for ln in lib.read_text(encoding="utf-8").splitlines():
            try:
                typo_seen.add(json.loads(ln)["at"])
            except Exception:
                pass
    for url in srcs[:limit]:
        slug = _slug(re.sub(r"https?://", "", url).strip("/") or "root")
        if fixtures is not None:
            fx = fixtures / f"{slug}.html"
            if not fx.exists():
                continue
            html = fx.read_text(encoding="utf-8")
        else:
            if not _robots_ok(url):
                st[slug] = {"url": url, "note": "robots-disallow"}
                continue
            try:
                html = _get(url)
            except Exception as e:
                st[slug] = {"url": url, "note": f"{type(e).__name__}"}
                continue
            time.sleep(DELAY)
        pp = parse_page(html)
        done += 1
        for s in pp["sections"]:
            sec_freq[s] += 1
        for m2 in pp["modules"]:
            mod_freq[m2] += 1
        css_laws = []
        for cu in pp["css"][:3]:
            css_url = cu if cu.startswith("http") else ("https://www.apple.com" + cu)
            if fixtures is not None:
                cf = fixtures / (_slug(cu) + ".css")
                css = cf.read_text(encoding="utf-8") if cf.exists() else ""
            else:
                try:
                    css = _get(css_url)
                except Exception:
                    css = ""
                time.sleep(DELAY / 2)
            css_laws += mine_typography(css, cu.rsplit("/", 1)[-1])
        fresh = [l for l in css_laws if l["at"] not in typo_seen]
        if fresh:
            with lib.open("a", encoding="utf-8") as fh:
                for l in fresh:
                    fh.write(json.dumps({"page": url, **l}, ensure_ascii=False) + "\n")
                    typo_seen.add(l["at"])
            laws_n += len(fresh)
        (out / f"{slug}.json").write_text(json.dumps(
            {"url": url, **pp, "typography_laws": len(css_laws)}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        st[slug] = {"url": url, "sections": len(pp["sections"]), "cta": pp["cta"]}
    stf.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# ВЕБ-АТЛАС · кит лендингов Apple (закономерности по всем страницам)",
          "Частота секций и модулей — это архитектурный словарь презентаций Apple.",
          "", "## Секции (топ-30)", "| Секция | Страниц |", "|---|---|"]
    for s, n in sec_freq.most_common(30):
        md.append(f"| {s} | {n} |")
    md += ["", "## Модули (топ-30)", "| Модуль | Страниц |", "|---|---|"]
    for s, n in mod_freq.most_common(30):
        md.append(f"| {s} | {n} |")
    md += ["", f"Страниц разобрано: {done} · типографических законов добыто: {laws_n} (всего в web-landings)"]
    (reg / "state" / "WEBLAB.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    if fixtures is None and done:
        with (reg / "state" / "CHANGELOG.md").open("a", encoding="utf-8") as f:
            f.write(f"### · веб-атлас лендингов\n- страниц {done} · секций-видов {len(sec_freq)} · "
                    f"модулей-видов {len(mod_freq)} · новых типографических законов {laws_n}\n\n")
    return {"pages": done, "sections_kinds": len(sec_freq), "typo_laws_new": laws_n}


if __name__ == "__main__":
    r = run(Path(__file__).resolve().parents[1])
    print(f"веб-атлас: страниц {r['pages']} · видов секций {r['sections_kinds']} · новых типографических законов {r['typo_laws_new']}")
