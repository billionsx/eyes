#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СЛУЖБА, модуль M3 — пиксель-сертификация (ст. 56).

Периодический сертификат соответствия проекта измеренным законам. Ни одного
числа из головы: входы — те же органы, что судят сам департамент:
  · линт файлов (strict + report) по адаптеру проекта;
  · живой монитор прода (registry/live/baseline.json);
  · сверка конституция↔реестр↔знание↔шрифт (VERIFICATION);
  · суд департамента (количество зелёных проверок).

Формула скоринга ОБЪЯВЛЕНА в самом сертификате (прозрачность, ст. 1):
  score = max(0, 100 − 2.0·strict − 1.5·live − 5.0·сверка − 0.05·report)

Потолок на долг советника снят 29.07.2026. С потолком 50 проект с 327
открытыми находками терял те же 5 баллов, что и проект с 50, и получал A.
Документ, который называет A состояние с 327 нарушениями, не измеряет —
он успокаивает. Вес снижен до 0.05, чтобы шкала осталась достижимой:
долг 0 → 100, долг 130 → 93.5 (A), долг 327 → 83.7 (C).
  (report — советники, не нарушения: вес мал и ограничен потолком)
Грейд: A+ ≥ 98 · A ≥ 93 · B ≥ 85 · C ≥ 70 · D < 70.

Выход: certificates/<проект>/<ГГГГ-ММ>.html (+ .pdf при --pdf через
Chromium) · latest.html · badge.json (shields.io endpoint) · строка эфира.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402
import projects  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
W = {"strict": 2.0, "report": 0.05, "live": 1.5, "verify": 5.0}


def grade(score: float) -> str:
    return "A+" if score >= 98 else "A" if score >= 93 else "B" if score >= 85 else "C" if score >= 70 else "D"


def collect(project_root: Path) -> dict:
    adapter = projects.pick(ROOT)
    tokens = json.loads((ROOT / "registry" / "standards" / "tokens.json").read_text(encoding="utf-8"))
    s = lint.run(ROOT, adapter, tokens, "strict", project_root)
    r = lint.run(ROOT, adapter, tokens, "report", project_root)
    base = json.loads((ROOT / "registry" / "live" / "baseline.json").read_text(encoding="utf-8")) \
        if (ROOT / "registry" / "live" / "baseline.json").exists() else {"findings": []}
    ver = (ROOT / "registry" / "state" / "VERIFICATION.md").read_text(encoding="utf-8") \
        if (ROOT / "registry" / "state" / "VERIFICATION.md").exists() else ""
    diverg = ver.count("РАСХОЖДЕНИЕ")
    return {"project": adapter.get("project", "default"),
            "strict": len(s["findings"]), "report": len(r["findings"]),
            "files": len(set(s.get("paths", [])) | set(r.get("paths", []))),
            "files_strict": s["files"],
            "rules": sorted(set(s["rules"]) | set(r["rules"])),
            "live": len(base["findings"]), "live_sha": base.get("sha", ""),
            "verify_diverg": diverg,
            "verify_rows": ver.count("| сходится") + diverg,
            "top": [(f[0], f[1], f[2]) for f in (s["findings"] + r["findings"])[:12]],
            "live_top": [(f[0].split(":")[1], f[1]) for f in base["findings"][:8]]}


class EmptyScan(Exception):
    """Обойдено 0 файлов — сертификат не выдаётся.

    ЗКН-Э006 закрывал этот случай для храповика: пустой обход не
    доказательство погашенного долга, а промах адреса. Для документа он
    опаснее: сертификат на пустом обходе — не «нет данных», а «данные есть
    и они отличные». Молчание не выдаётся за чистоту (ЗКН-Э001).
    """


def score_of(c: dict) -> float:
    return round(max(0.0, 100.0 - W["strict"] * c["strict"]
                     - W["report"] * c["report"]
                     - W["live"] * c["live"] - W["verify"] * c["verify_diverg"]), 1)


def render_html(c: dict, score: float, ts: str) -> str:
    g = grade(score)
    rows_f = "".join(f"<tr><td>{r}</td><td>{p}</td><td>{l}</td></tr>" for r, p, l in c["top"]) or \
             "<tr><td colspan=3>находок нет</td></tr>"
    rows_l = "".join(f"<tr><td>{r}</td><td>{s2}</td></tr>" for r, s2 in c["live_top"]) or \
             "<tr><td colspan=2>прод чист по базовой линии</td></tr>"
    return f"""<!doctype html><html lang="ru"><meta charset="utf-8"><title>BXE сертификат</title>
<style>@page{{margin:14mm}}body{{font:14px/1.55 -apple-system,system-ui;color:#111;margin:40px auto;max-width:820px}}
h1{{font-size:26px;margin:0}} .g{{font-size:64px;font-weight:800}} .s{{color:#555}}
table{{width:100%;border-collapse:collapse;margin:10px 0 22px}} td,th{{border-top:1px solid #ddd;padding:6px 8px;text-align:left;font-size:12.5px}}
.k{{display:flex;gap:28px;margin:18px 0}} .k div b{{font-size:22px;display:block}}</style>
<h1>BXE · Сертификат соответствия измеренным законам</h1>
<p class="s">Проект: <b>{c['project']}</b> · период {ts[:7]} · выдан {ts} · правила: {', '.join(c['rules'])}</p>
<div class="k"><div><b class="g">{g}</b>грейд</div><div><b>{score}</b>скор</div>
<div><b>{c['files']}</b>файлов проверено</div><div><b>{c['report']}</b>находок советника открыто</div><div><b>{c['verify_rows']}</b>строк сверки · расхождений {c['verify_diverg']}</div></div>
<p class="s">Формула (объявлена, ст. 1): score = 100 − 2.0·strict({c['strict']}) − 1.5·live({c['live']}) − 5.0·сверка({c['verify_diverg']}) − 0.05·report({c['report']}). Каждое правило выведено из замера/первоисточника с адресом (📐/🍎), суд департамента зелёный.</p>
<h3>Файловые находки (top)</h3><table><tr><th>Правило</th><th>Файл</th><th>Строка</th></tr>{rows_f}</table>
<h3>Живой прод (базовая линия{(' · деплой ' + c['live_sha'][:9]) if c['live_sha'] else ''})</h3>
<table><tr><th>Правило</th><th>Селектор</th></tr>{rows_l}</table>
<p class="s">BXE — Billions X Eyes · конституция и реестры: github.com/billionsx/eyes</p></html>"""


def verify_register(out: Path) -> list:
    """ПОДЛИННОСТЬ ВЫДАННОГО (ст. 44). Реестр и файлы сверяются в обе стороны:
    строка без файла — потерянный сертификат; файл без строки — выдача мимо
    реестра; несовпавший sha256 — подмена выданного документа."""
    import hashlib, re
    reg = out / "REGISTER.md"
    problems = []
    rows = {}
    if reg.exists():
        for line in reg.read_text(encoding="utf-8").split("\n"):
            m = re.match(r"\|\s*(\d{4}-\d{2})\s*\|.*?\|\s*`([0-9a-f]{16})…`\s*\|", line)
            if m:
                rows[m.group(1)] = m.group(2)
    files = {f.stem for f in out.glob("*.html") if f.stem != "latest"}
    for month, short in rows.items():
        f = out / f"{month}.html"
        if not f.exists():
            problems.append(f"{month}: строка в реестре есть, файла нет")
            continue
        real = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
        if real != short:
            problems.append(f"{month}: отпечаток не сходится (реестр {short}, файл {real})")
    for month in sorted(files - set(rows)):
        problems.append(f"{month}: файл выдан мимо реестра")
    return problems


def register(out: Path, project: str, month: str, score: float,
             gr: str, ts: str) -> None:
    """РЕЕСТР ВЫДАННЫХ СЕРТИФИКАТОВ (ст. 56 · M3).

    Так ведут дело органы сертификации: выданный документ НЕИЗМЕНЕН, а реестр
    несёт его отпечаток. Копия у клиента не нужна и вредна — она отстанет от
    следующей выдачи; клиент носит бейдж и адрес проверки, подлинность
    сверяется отпечатком из этого реестра.

    Строка реестра: месяц · скор · грейд · sha256 файла · размер · дата выдачи.
    Прошлые строки не переписываются — только дополняются (выдача необратима).
    """
    import hashlib
    f = out / f"{month}.html"
    digest = hashlib.sha256(f.read_bytes()).hexdigest()
    reg = out / "REGISTER.md"
    head = (f"# РЕЕСТР ВЫДАННЫХ СЕРТИФИКАТОВ · {project}\n\n"
            "Орган выдачи: департамент Billions X Eyes. Выданный сертификат\n"
            "неизменен; подлинность проверяется отпечатком sha256 этой строки\n"
            "против файла в этом каталоге. Копий у клиента нет намеренно —\n"
            "копия отстаёт от следующей выдачи (ЗКН-Э005: одно понятие — один\n"
            "источник). Клиент носит бейдж `badge.json` и адрес проверки.\n\n"
            "| месяц | скор | грейд | файл | размер | sha256 | выдан |\n"
            "|---|---|---|---|---|---|---|\n")
    rows = {}
    if reg.exists():
        for line in reg.read_text(encoding="utf-8").split("\n"):
            if line.startswith("| 20"):
                rows[line.split("|")[1].strip()] = line
    rows[month] = (f"| {month} | {score} | {gr} | `{month}.html` | {f.stat().st_size} | "
                   f"`{digest[:16]}…` | {ts} |")
    reg.write_text(head + "\n".join(rows[k] for k in sorted(rows)) + "\n", encoding="utf-8")
    print(f"реестр: {project} · {month} · {score} · {gr} · sha256 {digest[:16]}…")


def run(project_root: Path, pdf: bool = False) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    c = collect(project_root)
    if not c["files"]:
        raise EmptyScan(
            f"обойдено 0 файлов в {project_root} — сертификат не выдан. "
            "Пустой обход означает промах адреса (не забран код, неверный "
            "PROJECT_ROOT или пустые глобы паспорта), а не отличный проект.")
    score = score_of(c)
    out = ROOT / "certificates" / c["project"]
    out.mkdir(parents=True, exist_ok=True)
    html = render_html(c, score, ts)
    month = ts[:7]
    (out / f"{month}.html").write_text(html, encoding="utf-8")
    (out / "latest.html").write_text(html, encoding="utf-8")
    color = "brightgreen" if score >= 93 else "green" if score >= 85 else "yellow" if score >= 70 else "red"
    (out / "badge.json").write_text(json.dumps(
        {"schemaVersion": 1, "label": "BXE", "message": f"{score} · {grade(score)}", "color": color}), encoding="utf-8")
    register(out, c["project"], month, score, grade(score), ts)
    if pdf:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                b = pw.chromium.launch()
                pg = b.new_page()
                pg.set_content(html, wait_until="load")
                pg.pdf(path=str(out / f"{month}.pdf"), format="A4", print_background=True)
                b.close()
        except Exception as e:
            print(f"pdf: {type(e).__name__} (html/badge выданы)")
    with (ROOT / "registry" / "state" / "CHANGELOG.md").open("a", encoding="utf-8") as f:
        f.write(f"### {ts} · сертификация\n- {c['project']}: скор {score} · грейд {grade(score)} "
                f"(strict {c['strict']} · report {c['report']} · live {c['live']} · сверка {c['verify_diverg']})\n\n")
    return {"project": c["project"], "score": score, "grade": grade(score), **{k: c[k] for k in ("strict", "report", "live", "verify_diverg")}}


if __name__ == "__main__":
    r = run(Path(os.environ.get("PROJECT_ROOT", ".")).resolve(), pdf="--pdf" in sys.argv)
    print(f"сертификат {r['project']}: {r['score']} · {r['grade']} (strict {r['strict']} · report {r['report']} · live {r['live']} · сверка {r['verify_diverg']})")
