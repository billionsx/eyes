#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · БОЛЬШАЯ СЕМЁРКА (ст. 55). Ежедневное системное познание логики
консалтинга: Big-4 (Deloitte · PwC · EY · KPMG) + Big-3 (McKinsey · BCG ·
Bain). Домены знаний: аналитика · продукт · бизнес-логика.

Механика — близнец атласа, свой фронтир на фирму (registry/bizlab/state.json):
 · шаг дня по бюджету, robots-ok, только домены семёрки;
 · с каждой страницы: ПОЛОЖЕНИЯ — императивы бизнес-логики по маркерам
   (should · must · need to · imperative · it is essential · leaders/companies
   that … outperform) → library/big7.jsonl с адресом page:<url>;
 · КАРТА ФРЕЙМВОРКОВ — детект канонических рамок словарём (MECE, пирамида
   Минто, 7-S, growth-share matrix, three horizons, jobs to be done, NPS,
   RAPID, zero-based budgeting, experience curve, value chain, five forces,
   balanced scorecard, blue ocean, OKR, north star metric, flywheel, TAM/SAM/
   SOM, unit economics, design thinking) — кто из фирм каким языком говорит;
 · свод state/BIG7.md: страницы/положения по фирмам + частоты рамок.
Числа не выдумываются: только текст самих фирм с адресами.
"""
import json
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawler import UA, _robots_ok  # noqa: E402
import html as _html  # noqa: E402


def strip_html(raw: str) -> str:
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", _html.unescape(raw)).strip()

DELAY = 1.0
RENDER_FIRMS = {"mckinsey", "bain"}
BLOCK_PATH = re.compile(r"/(account|login|profile|search|careers?|contact|privacy|legal|cookies|subscribe|preference|rss)\b|\?", re.I)  # их хабы собираются скриптом — берём браузером
LINK = re.compile(r'href="([^"#]+)"', re.I)
IMP = re.compile(r"\b(should|must|need(?:s)? to|it is essential|imperative|"
                 r"companies that [^.]{10,80} outperform|leaders (?:should|must|need))\b", re.I)
FRAMEWORKS = {
    "MECE": r"\bMECE\b", "Пирамида Минто": r"pyramid principle",
    "7-S": r"\b7-?S framework|McKinsey 7-?S", "Матрица рост-доля": r"growth[- ]share matrix",
    "Три горизонта": r"three horizons", "Jobs to be Done": r"jobs?[- ]to[- ]be[- ]done|\bJTBD\b",
    "NPS": r"net promoter", "RAPID": r"\bRAPID\b", "ZBB": r"zero[- ]based budget",
    "Кривая опыта": r"experience curve", "Цепочка ценности": r"value chain",
    "Пять сил": r"five forces", "Balanced Scorecard": r"balanced scorecard",
    "Blue Ocean": r"blue ocean", "OKR": r"\bOKRs?\b", "North Star": r"north star metric",
    "Flywheel": r"\bflywheel\b", "TAM/SAM/SOM": r"\bTAM\b.{0,40}\bSAM\b|\bSAM\b.{0,40}\bSOM\b",
    "Юнит-экономика": r"unit economics", "Design Thinking": r"design thinking",
}
FRX = {k: re.compile(v, re.I) for k, v in FRAMEWORKS.items()}
SENT_MAX = 3


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def mine(text: str, url: str):
    laws, frames = [], []
    for k, rx in FRX.items():
        if rx.search(text):
            frames.append(k)
    sents = re.split(r"(?<=[.!?])\s+", text)
    got = 0
    for s in sents:
        s = s.strip()
        if 40 <= len(s) <= 320 and IMP.search(s):
            laws.append({"text": s, "at": f"page:{url}"})
            got += 1
            if got >= SENT_MAX:
                break
    return laws, frames


def _renderer():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None, None, None
    pw = sync_playwright().start()
    b = pw.chromium.launch()
    pg = b.new_page(user_agent=UA)
    return pw, b, pg


def run(root: Path, budget: int = None, fixtures: Path = None) -> dict:
    reg = root / "registry"
    cfg = json.loads((reg / "big7-sources.json").read_text(encoding="utf-8"))
    budget = budget or cfg.get("budget_per_day", 70)
    bl = reg / "bizlab"
    bl.mkdir(exist_ok=True)
    stf = bl / "state.json"
    st = json.loads(stf.read_text(encoding="utf-8")) if stf.exists() else \
        {"firms": {f: {"frontier": list(seeds), "visited": [], "laws": 0}
                   for f, seeds in cfg["firms"].items()}, "frames": {}}
    lib = reg / "library" / "big7.jsonl"
    lib.parent.mkdir(exist_ok=True)
    seen_at = set()
    if lib.exists():
        for ln in lib.read_text(encoding="utf-8").splitlines():
            try:
                seen_at.add(json.loads(ln)["text"][:100])
            except Exception:
                pass
    frames_c = Counter(st.get("frames", {}))
    firms = list(st["firms"].keys())
    for f2 in firms:  # хабы дышат ежедневно: сиды всегда в голове фронтира
        seeds = list(cfg["firms"].get(f2, []))
        st["firms"][f2]["frontier"] = seeds + [u for u in st["firms"][f2]["frontier"] if u not in seeds]
        st["firms"][f2]["_seeds"] = seeds
    per = max(1, budget // max(1, len(firms)))
    per_render = min(per, 8)  # браузерные фирмы: жёсткий кап времени шага
    new_laws = pages = 0
    pw = br = pg = None
    st.setdefault("errors", {})
    for firm in firms:
        fs = st["firms"][firm]
        vis = set(fs["visited"])
        steps = 0
        cap = per_render if firm in RENDER_FIRMS else per
        last_html, last_txt = "", ""
        while fs["frontier"] and steps < cap:
            url = fs["frontier"].pop(0)
            if BLOCK_PATH.search(url):
                vis.add(url)
                continue
            if url in vis and url not in fs.get("_seeds", []):
                continue
            vis.add(url)
            if fixtures is not None:
                fx = fixtures / (re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[:80] + ".html")
                if not fx.exists():
                    continue
                html = fx.read_text(encoding="utf-8")
            else:
                if not _robots_ok(url):
                    continue
                if firm in RENDER_FIRMS:
                    if pg is None:
                        try:
                            pw, br, pg = _renderer()
                        except Exception as e:
                            st["errors"][firm] = f"renderer: {type(e).__name__}: {str(e)[:120]}"
                            break
                    if pg is None:
                        st["errors"][firm] = "renderer: playwright недоступен"
                        break
                    try:
                        pg.goto(url, wait_until="domcontentloaded", timeout=15000)
                        pg.wait_for_timeout(2200)
                        html = pg.content()
                    except Exception as e:
                        st["errors"][firm] = f"{type(e).__name__}: {str(e)[:120]}"
                        continue
                else:
                    try:
                        html = _get(url)
                    except Exception:
                        continue
                time.sleep(DELAY)
            steps += 1
            pages += 1
            text = strip_html(html)
            if firm in RENDER_FIRMS:
                last_html, last_txt = html, text
            laws, frames = mine(text, url)
            for fr in frames:
                frames_c[fr] += 1
            fresh = [l for l in laws if l["text"][:100] not in seen_at]
            if fresh:
                with lib.open("a", encoding="utf-8") as fh:
                    for l in fresh:
                        fh.write(json.dumps({"firm": firm, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **l}, ensure_ascii=False) + "\n")
                        seen_at.add(l["text"][:100])
                fs["laws"] += len(fresh)
                new_laws += len(fresh)
            host = urllib.parse.urlparse(url).netloc
            for h in LINK.findall(html):
                u = urllib.parse.urljoin(url, h.split("?")[0])
                pu = urllib.parse.urlparse(u)
                if pu.netloc == host and pu.scheme.startswith("http") and u not in vis \
                        and len(fs["frontier"]) < 4000 and not re.search(r"\.(pdf|jpg|png|zip|mp4)$", u, re.I) and not BLOCK_PATH.search(u):
                    fs["frontier"].append(u)
        if firm in RENDER_FIRMS:
            st["errors"][firm] = (f"сводка: шагов {steps} · фронтир после {len(fs['frontier'])} · "
                                  f"последняя страница {len(last_html)}б: «{last_txt[:90]}»") if steps else "сводка: шагов 0 (фронтир пуст до входа)"
        fs.pop("_seeds", None)
        fs["visited"] = sorted(vis)
        st["frames"] = dict(frames_c)
        stf.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")  # инкрементально: работа фирмы не теряется
    if br is not None:
        br.close(); pw.stop()
    st["frames"] = dict(frames_c)
    stf.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    md = ["# БОЛЬШАЯ СЕМЁРКА · познание логики консалтинга (ст. 55)",
          "Положения — только словами самих фирм, адрес page:<url>.", "",
          "| Фирма | Пройдено | Положений |", "|---|---|---|"]
    for firm in firms:
        fs = st["firms"][firm]
        md.append(f"| {firm} | {len(fs['visited'])} | {fs['laws']} |")
    md += ["", "## Карта фреймворков (частота упоминаний)", "| Рамка | Страниц |", "|---|---|"]
    for k, n in frames_c.most_common(25):
        md.append(f"| {k} | {n} |")
    (reg / "state" / "BIG7.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    if fixtures is None and pages:
        with (reg / "state" / "CHANGELOG.md").open("a", encoding="utf-8") as f:
            f.write(f"### · большая семёрка\n- страниц {pages} · новых положений {new_laws} · рамок в карте {len(frames_c)}\n\n")
    return {"pages": pages, "laws_new": new_laws, "frames": len(frames_c)}


if __name__ == "__main__":
    r = run(Path(__file__).resolve().parents[1])
    print(f"семёрка: страниц {r['pages']} · новых положений {r['laws_new']} · рамок {r['frames']}")
