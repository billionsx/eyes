#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СЛУЖБА, модуль M5 — страж App Store (ст. 56).

Чек-лист перед сабмитом, построенный из ЖИВОГО текста App Review Guidelines
(никаких пересказов): орган в CI тянет страницу гайдлайнов, извлекает
нумерованные пункты дословными заголовками (адрес page:#N.N.N) →
`registry/appstore/points.json`; офлайн — каркас из снимка дозора.

Плюс автопроверки, которые машина может подтвердить детерминированно по
репозиторию (факт с путём, не мнение):
  · ссылка на политику конфиденциальности (гайдлайн 5.1) — grep по src;
  · ссылка поддержки/контакта (гайдлайн 1.5) — grep по src.
Остальное — «Ручная проверка»: дословные пункты гайдлайнов без интерпретаций.
Выход: registry/appstore/CHECKLIST.md · строка эфира.
"""
import gzip
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawler import UA  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GUIDE_URL = "https://developer.apple.com/app-store/review/guidelines/"
POINT = re.compile(r"\b(\d\.\d(?:\.\d+)?)\s+([A-Z][^\n<>{}]{2,90}?)(?=\s*(?:<|\n|\d\.\d|$))")
KEY_MANUAL = ("1.1", "1.2", "1.5", "2.1", "2.3", "3.1", "3.1.1", "4.0", "4.2", "5.1", "5.1.1", "5.1.2")


def parse_points(html: str) -> list:
    txt = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    txt = re.sub(r"<(h\d|p|li|div|section)\b[^>]*>", "\n", txt, flags=re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    seen, out = set(), []
    for num, title in POINT.findall(txt):
        title = re.sub(r"\s+", " ", title).strip(" .")
        if num not in seen and len(title) >= 3:
            seen.add(num)
            out.append({"n": num, "title": title, "at": f"page:{GUIDE_URL}#{num}"})
    return sorted(out, key=lambda p: [int(x) for x in p["n"].split(".")])


def repo_check(project_root: Path, words) -> dict:
    rx = re.compile("|".join(words), re.I)
    for p in sorted(project_root.glob("apps/web/src/**/*")):
        if p.is_file() and p.suffix in (".tsx", ".ts", ".html", ".css"):
            try:
                for i, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if rx.search(ln):
                        return {"ok": True, "at": f"{p.relative_to(project_root)}:{i}"}
            except Exception:
                continue
    return {"ok": False, "at": ""}


CORPUS = ROOT / "registry" / "corpus" / "appstore"


def corpus_put(url: str, html: str) -> bool:
    """Сохранить сырую страницу гайдлайнов. Урок У1 свода уроков.

    Орган просеивает ЖИВОЙ текст App Review Guidelines. Пока сырьё не
    хранилось, любая правка сита `parse_points` требовала снова идти к Apple —
    та же болезнь, что жатва вылечила 29.07, а атлас 02.08. Урок куплен
    дважды; на третий раз он взят из свода, а не переоткрыт.
    """
    try:
        CORPUS.mkdir(parents=True, exist_ok=True)
        f = CORPUS / (hashlib.sha256(url.encode()).hexdigest()[:12] + ".html.gz")
        # Детерминированно (У6 свода уроков): mtime=0, иначе одинаковое
        # содержимое даёт разные байты и долька конфликтует на пустом месте.
        with open(f, "wb") as raw, gzip.GzipFile(filename="", mode="wb",
                                                 fileobj=raw, mtime=0) as fh:
            fh.write(html.encode("utf-8"))
        return True
    except (OSError, ValueError):
        return False


def remill() -> list:
    """Перемолоть сохранённые гайдлайны текущим ситом. Без сети."""
    out = []
    if not CORPUS.is_dir():
        return out
    for f in sorted(CORPUS.glob("*.html.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            out += parse_points(fh.read())
    return out


def run(project_root: Path, fetch: bool = True) -> dict:
    out = ROOT / "registry" / "appstore"
    out.mkdir(exist_ok=True)
    points = []
    src = "снимок дозора (каркас — подпункты добираются прогоном CI)"
    if fetch:
        try:
            req = urllib.request.Request(GUIDE_URL, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                raw = r.read().decode("utf-8", "replace")
            corpus_put(GUIDE_URL, raw)
            points = parse_points(raw)
            src = f"живая страница гайдлайнов · пунктов {len(points)}"
        except Exception as e:
            src += f" (сеть: {type(e).__name__})"
    if points:
        (out / "points.json").write_text(json.dumps(points, ensure_ascii=False, indent=1), encoding="utf-8")
    elif (out / "points.json").exists():
        points = json.loads((out / "points.json").read_text(encoding="utf-8"))
        src = f"points.json прошлого прогона · пунктов {len(points)}"
    priv = repo_check(project_root, [r"privacy", r"конфиденциальн"])
    supp = repo_check(project_root, [r"mailto:", r"Поддержк", r"Связь:", r"href=\"/contact"])
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = [f"# СТРАЖ APP STORE · чек-лист перед сабмитом — {ts}",
          f"Источник пунктов: {src}. Каждый пункт — дословный заголовок гайдлайна с адресом.", "",
          "## Автопроверено по репозиторию (факт с путём)",
          f"- {'✅' if priv['ok'] else '🔴'} Политика конфиденциальности (гайдлайн 5.1): "
          + (f"найдена — `{priv['at']}`" if priv["ok"] else "НЕ НАЙДЕНА в apps/web/src — заведи страницу/ссылку"),
          f"- {'✅' if supp['ok'] else '🔴'} Поддержка/контакт (гайдлайн 1.5): "
          + (f"найдена — `{supp['at']}`" if supp["ok"] else "НЕ НАЙДЕНА в apps/web/src"), ""]
    if points:
        md.append("## Ключевые пункты — ручная проверка (дословно)")
        for p in points:
            if p["n"] in KEY_MANUAL:
                md.append(f"- [ ] **{p['n']}** {p['title']}  \n  `{p['at']}`")
        md += ["", f"## Полный указатель ({len(points)})"]
        by = {}
        for p in points:
            by.setdefault(p["n"].split(".")[0], []).append(p)
        sect = {"1": "Safety", "2": "Performance", "3": "Business", "4": "Design", "5": "Legal"}
        for s in sorted(by):
            md.append(f"- **{s}. {sect.get(s, '')}** — " + " · ".join(p["n"] for p in by[s]))
    else:
        md += ["## Разделы (каркас снимка)",
               "- [ ] 1. Safety · 2. Performance · 3. Business · 4. Design · 5. Legal",
               "- [ ] Before You Submit — пройден дословно  \n  `page:" + GUIDE_URL + "`"]
    (out / "CHECKLIST.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    with (ROOT / "registry" / "state" / "CHANGELOG.md").open("a", encoding="utf-8") as f:
        f.write(f"### {ts} · страж App Store\n- пунктов {len(points)} · privacy {'ok' if priv['ok'] else 'НЕТ'} · support {'ok' if supp['ok'] else 'НЕТ'}\n\n")
    return {"points": len(points), "privacy": priv["ok"], "support": supp["ok"]}


if __name__ == "__main__":
    import os
    r = run(Path(os.environ.get("PROJECT_ROOT", ".")).resolve(), fetch="--offline" not in sys.argv)
    print(f"страж: пунктов {r['points']} · privacy {'ok' if r['privacy'] else 'НЕТ'} · support {'ok' if r['support'] else 'НЕТ'}")
