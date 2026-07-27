#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ЭФИР-ДАШБОРД (ст. 54). Отчётность в прямом эфире: каждый прогон
пересобирает dashboard/DASHBOARD.md (рендерится GitHub'ом по постоянной
ссылке) и dashboard/index.html + data.json (для домена после переноса).
Только живые числа из реестров — ни одного слова из головы.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "registry"


def _j(p, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def collect() -> dict:
    d = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
    st = _j(R / "atlas" / "state.json", {})
    d["atlas"] = {"visited": st.get("visited", 0), "frontier": len(st.get("frontier", [])),
                  "cycles": st.get("cycles", 0), "last": st.get("last_step", "—")}
    m = re.search(r"Итого законов: (\d+) · фреймворков: (\d+)",
                  (R / "library" / "INDEX.md").read_text(encoding="utf-8") if (R / "library" / "INDEX.md").exists() else "")
    d["library"] = {"laws": int(m.group(1)) if m else 0, "frameworks": int(m.group(2)) if m else 0}
    wl = R / "library" / "web-landings.jsonl"
    d["web_laws"] = sum(1 for _ in wl.open(encoding="utf-8")) if wl.exists() else 0
    kn = 0
    for f in (R / "knowledge").glob("*.md"):
        mm = re.search(r"Нормативных положений: (\d+)", f.read_text(encoding="utf-8"))
        kn += int(mm.group(1)) if mm else 0
    d["knowledge"] = kn
    d["sources"] = len(_j(R / "sources.json", {}).get("sources", []))
    d["web_pages"] = len(_j(R / "web-sources.json", {}).get("pages", []))
    ks = _j(R / "standards" / "kit" / "state.json", {})
    d["kit"] = {"kits": len(ks.get("kits", [])), "fonts": len(ks.get("fonts", []) or []),
                "links_seen": len(ks.get("links_seen", []) or []), "errors": len(ks.get("errors", []) or [])}
    sy = _j(R / "standards" / "symbols" / "sf-symbols-names.json", {})
    d["symbols"] = sy.get("count", 0)
    sc = R / "state" / "SCREENS.md"
    ms = re.search(r"Итого кадров: (\d+) · приложений: (\d+)", sc.read_text(encoding="utf-8")) if sc.exists() else None
    d["screens"] = {"frames": int(ms.group(1)) if ms else 0, "apps": int(ms.group(2)) if ms else 0}
    ap = _j(R / "appstore" / "points.json", [])
    ck = (R / "appstore" / "CHECKLIST.md")
    d["appstore"] = {"points": len(ap), "have": ck.exists()}
    br = (ROOT / "briefs" / "latest.md")
    d["brief"] = br.read_text(encoding="utf-8").splitlines()[0].replace("# ", "") if br.exists() else ""
    certs = {}
    for f in sorted((ROOT / "certificates").glob("*/badge.json")):
        m = _j(f, {}).get("message", "")
        if m:
            certs[f.parent.name] = m
    d["certificates"] = certs
    d["certificate"] = " · ".join(f"{k}: {v}" for k, v in certs.items())
    ms = _j(R / "live" / "monitor-state.json", {})
    d["monitor"] = ms
    lv = R / "live" / "REPORT.md"
    d["live"] = {"pages": lv.read_text(encoding="utf-8").count("## ") if lv.exists() else 0}
    base = _j(R / "state" / "ae-baseline.json", {})
    d["ratchet"] = {k: sum(v.values()) for k, v in base.items()} if base else {}
    b7 = _j(R / "bizlab" / "state.json", {})
    d["big7"] = {"pages": sum(len(f.get("visited", [])) for f in b7.get("firms", {}).values()),
                 "laws": sum(f.get("laws", 0) for f in b7.get("firms", {}).values()),
                 "frames": len(b7.get("frames", {}))}
    tk = _j(R / "standards" / "tokens.json", {})
    d["base"] = tk.get("base", "?")
    tasks = _j(R / "tasks.json", {})
    d["tasks"] = {grp: {s: sum(1 for t in items if t["status"] == s)
                        for s in ("done", "active", "queued", "blocked", "partial")}
                  for grp, items in tasks.items() if not grp.startswith("_")}
    d["tasks_list"] = tasks
    c = (ROOT / "CONSTITUTION.md").read_text(encoding="utf-8")
    d["articles"] = len(re.findall(r"\*\*Статья \d+(?:\.\d+)?", c))
    return d


GRP = {"bxad": "Департамент BXE", "service": "Служба (трек M)",
       "iskcon_product": "Проект ISKCON"}


def render(d: dict):
    groups = [g for g in d["tasks_list"] if not g.startswith("_")]
    out = ROOT / "dashboard"
    out.mkdir(exist_ok=True)
    (out / "data.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    t = d["tasks"]

    def trow(grp):
        s = t.get(grp, {})
        return f"done {s.get('done',0)} · active {s.get('active',0)} · queued {s.get('queued',0)} · partial {s.get('partial',0)} · blocked {s.get('blocked',0)}"

    md = [f"# BXE · ЭФИР — {d['ts']}",
          "Живые числа реестров департамента Billions X Eyes; лист пересобирается каждым прогоном.", "",
          "| Орган | Состояние |", "|---|---|",
          f"| Конституция | статей **{d['articles']}** · база `{d['base']}` |",
          f"| Атлас документации | пройдено **{d['atlas']['visited']}** · фронтир {d['atlas']['frontier']} · кругов {d['atlas']['cycles']} · шаг {d['atlas']['last']} |",
          f"| Библиотека законов | **{d['library']['laws']}** законов · {d['library']['frameworks']} фреймворков · +{d['web_laws']} веб-лендинги |",
          f"| Знание (курируемое) | **{d['knowledge']}** положений · {d['sources']} источников |",
          f"| Веб-атлас | {d['web_pages']} страниц поручения |",
          f"| Кит | извлечено {d['kit']['kits']} · шрифтовых dmg {d['kit']['fonts']} · ссылок в поле зрения {d['kit']['links_seen']} · ошибок {d['kit']['errors']} |",
          f"| SF Symbols | **{d['symbols']}** символов (macOS-плечо) |",
          f"| Кадротека | {d['screens']['frames']} кадров · {d['screens']['apps']} приложений |",
          f"| Живой взгляд | страниц в эфире: {d['live']['pages']} |",
          f"| Страж App Store (M5) | {'пунктов ' + str(d['appstore']['points']) + ' · чек-лист готов' if d['appstore']['have'] else 'первый прогон впереди'} |",
          f"| Big7-бриф (M6) | {d['brief'] or 'первый — в понедельник'} |",
          f"| Сертификат (M3) | {d['certificate'] or 'не выдан'} |",
          f"| Монитор прода | {('деплой ' + d['monitor'].get('sha','')[:9] + ' · сейчас ' + str(d['monitor'].get('now')) + ' · новых ' + str(d['monitor'].get('new')) + ' · закрыто ' + str(d['monitor'].get('gone'))) if d.get('monitor') else 'первого снятия не было'} |",
          f"| Большая семёрка | страниц {d['big7']['pages']} · положений {d['big7']['laws']} · рамок в карте {d['big7']['frames']} |",
          f"| Храповик | долг по проектам: " + (" · ".join(f"{k}:{v}" for k, v in d['ratchet'].items()) or "—") + " |",
          "", "## Поручения основателя",
          *[f"- {GRP.get(g, g)}: {trow(g)}" for g in groups], "",
          "| ID | Поручение | Статус | Орган |", "|---|---|---|---|"]
    for grp in groups:
        for x in d["tasks_list"].get(grp, []):
            md.append(f"| {x['id']} | {x['task']} | **{x['status']}** | {x['organ']} |")
    (out / "DASHBOARD.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    rows = "".join(f"<tr><td>{x['id']}</td><td>{x['task']}</td><td class='s-{x['status']}'>{x['status']}</td></tr>"
                   for grp in groups for x in d["tasks_list"].get(grp, []))
    projects_row = " · ".join(f"{k} <span class=\'l\'>{v}</span>"
                              for k, v in (d.get("certificates") or {}).items()) or "—"
    debt = " · ".join(f"{k}: {v}" for k, v in (d.get("ratchet") or {}).items()) or "—"
    mon = d.get("monitor") or {}
    mon_s = (f"новых {mon.get('new', 0)} · закрыто {mon.get('gone', 0)} · находок сейчас {mon.get('now', 0)}"
             if mon else "первого снятия не было")
    html = f"""<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="600">
<title>Billions X Eyes · эфир</title>
<meta name="description" content="Департамент стандартов Apple: живые числа реестров, законы, храповик долга подключённых проектов.">
<style>
:root{{color-scheme:dark}}
*{{box-sizing:border-box}}
body{{background:#000;color:#fff;font:16px/1.5 -apple-system,BlinkMacSystemFont,system-ui,sans-serif;
margin:0;padding:28px 20px 60px;max-width:1100px;margin-inline:auto;-webkit-font-smoothing:antialiased}}
header{{margin-bottom:24px}}
h1{{font-size:30px;line-height:1.15;font-weight:700;letter-spacing:-.4px;margin:0 0 6px}}
.sub{{color:rgba(255,255,255,.6);font-size:15px}}
.g{{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px}}
.c{{background:#1C1C1E;border-radius:18px;padding:16px 18px}}
.n{{font-size:28px;font-weight:700;letter-spacing:-.5px}}
.l{{color:rgba(255,255,255,.6);font-size:13px}}
.wide{{grid-column:1/-1;background:#1C1C1E;border-radius:18px;padding:16px 18px;font-size:14px}}
h2{{font-size:19px;font-weight:600;margin:28px 0 10px}}
table{{width:100%;border-collapse:collapse}}
td{{padding:8px;border-top:1px solid #2C2C2E;font-size:13.5px;vertical-align:top}}
.s-done{{color:#30D158}}.s-active{{color:#0A84FF}}.s-queued{{color:rgba(255,255,255,.55)}}
.s-partial{{color:#FFD60A}}.s-blocked{{color:#FF453A}}
a{{color:#0A84FF;text-decoration:none}}
footer{{margin-top:32px;color:rgba(255,255,255,.45);font-size:13px}}
</style>
<header>
<h1>Billions X Eyes</h1>
<div class="sub">Департамент стандартов Apple · автономный · эфир пересобран {d['ts']}</div>
</header>
<div class="g">
<div class="c"><div class="n">{d['library']['laws']}</div><div class="l">законов в библиотеке · {d['library']['frameworks']} фреймворков · +{d['web_laws']} веб</div></div>
<div class="c"><div class="n">{d['atlas']['visited']}</div><div class="l">страниц документации пройдено · фронтир {d['atlas']['frontier']}</div></div>
<div class="c"><div class="n">{d['knowledge']}</div><div class="l">положений знания · {d['sources']} источников дозора</div></div>
<div class="c"><div class="n">{d['articles']}</div><div class="l">статей конституции · база {d['base']}</div></div>
<div class="c"><div class="n">{d['symbols']}</div><div class="l">SF Symbols (macOS-плечо)</div></div>
<div class="c"><div class="n">{d['screens']['frames']}</div><div class="l">кадров кадротеки · {d['screens']['apps']} приложений Apple</div></div>
<div class="c"><div class="n">{d['appstore']['points']}</div><div class="l">пунктов App Review Guidelines в страже</div></div>
<div class="c"><div class="n">{d['big7']['laws']}</div><div class="l">положений большой семёрки · {d['big7']['pages']} страниц</div></div>
<div class="wide">Сертификаты проектов: {projects_row}<br>Храповик долга: {debt}<br>Монитор прода: {mon_s}<br>Бриф недели: {d['brief'] or '—'}</div>
</div>
<h2>Поручения</h2>
<table>{rows}</table>
<footer>Числа — только из реестров департамента, ни одного из головы (БТ001).
Исходники и хроника: <a href="https://github.com/billionsx/eyes">github.com/billionsx/eyes</a> ·
лист в Markdown: <a href="https://github.com/billionsx/eyes/blob/main/dashboard/DASHBOARD.md">DASHBOARD.md</a></footer>
</html>"""
    (out / "index.html").write_text(html, encoding="utf-8")

    # Статика домена: пишется каждым прогоном, чтобы не могла разойтись.
    # index.html пересобирается постоянно — кэш браузера держим коротким,
    # data.json отдаём как источник чисел для внешних читателей.
    (out / "_headers").write_text(
        "/*\n"
        "  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: strict-origin-when-cross-origin\n"
        "  Cache-Control: public, max-age=300, must-revalidate\n"
        "/data.json\n"
        "  Access-Control-Allow-Origin: *\n"
        "  Cache-Control: public, max-age=300\n", encoding="utf-8")
    (out / "robots.txt").write_text(
        "# Billions X Eyes · эфир департамента\n"
        "User-agent: *\n"
        "Allow: /\n", encoding="utf-8")


if __name__ == "__main__":
    d = collect()
    render(d)
    print(f"эфир: атлас {d['atlas']['visited']} · законов {d['library']['laws']} · задач BXE done {d['tasks']['bxad']['done']}")
