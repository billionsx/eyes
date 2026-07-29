#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · единая точка входа департамента.

  status    — сводка: источники, состояние дозора, iOS 27, стандарты
  crawl     — разведка (живая сеть или --fixtures для офлайна)
  ios27     — дозор iOS 27 по снимкам; --issue-on-detect открывает issue
  lint      — исполнительная власть по адаптеру проекта
  attach    — подключить департамент к новому проекту (создать адаптер)
  selftest  — батарея живых нарушений в обе стороны (ломаю → красный,
              чиню → зелёный). Гейт живёт вместе со своим тестом.

Только stdlib. Департамент обязан запускаться на голом python3 где угодно.
"""
import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BIN = Path(__file__).resolve().parent
ROOT = BIN.parent
sys.path.insert(0, str(BIN))
import crawler  # noqa: E402
import digest as digest_mod  # noqa: E402
import atlas as atlas_mod  # noqa: E402
import figkit as figkit_mod  # noqa: E402
import study as study_mod  # noqa: E402
import weblab as weblab_mod  # noqa: E402
import consult as consult_mod  # noqa: E402
import verify as verify_mod  # noqa: E402
import lint as lint_mod  # noqa: E402

IOS27 = re.compile(r"\b(?:iOS|iPadOS)\s*27\b")

# Мандат основателя дословно (23.07.2026). Суд валит сборку, если домен
# теряет статью конституции: ключ → якорь, обязанный жить в CONSTITUTION.md.
FOUNDER_MANDATE = {
    "кернинг": "Статья 7 · Кернинг", "шрифты": "Статья 8 · Шрифты",
    "цвета": "Статья 9 · Цвета", "отступы": "Статья 10 · Отступы",
    "иконки": "Статья 11 · Иконки", "плашки": "Статья 12 · Плашки",
    "Liquid Glass": "Статья 13 · Liquid Glass", "меню": "Статья 14 · Меню",
    "архитектура приложений": "Статья 15 · Архитектура",
    "blur": "Статья 16 · Blur", "многослойность": "Статья 17 · Многослойность",
    "opacity": "Статья 18 · Opacity", "свечение": "Статья 19 · Свечение",
    "тени": "Статья 20 · Тени", "анимация": "Статья 21 · Анимация",
    "кинетика": "Статья 22 · Кинетика", "жесты": "Статья 23 · Жесты",
    "вибрации": "Статья 24 · Вибрации", "надавливание": "Статья 25 · Надавливание",
    "кроссплатформенность": "Статья 26 · Кроссплатформенность",
    "суб-приложения": "Статья 27 · Суб-приложения",
    "градиенты": "Статья 28 · Градиенты", "геймификация": "Статья 29 · Геймификация",
    "рейтинги/отзывы": "Статья 30 · Рейтинги", "маркетинг": "Статья 31 · Маркетинг",
    "popup": "Статья 32 · Popup", "продукты-эталоны": "Статья 33 · Продукты",
    "UI/UX + HIG": "Статья 34 · UI/UX",
    "автономность": "Статья 46 · Суверенитет",
    "подключение любого проекта паспортом": "Статья 57 · Паспорт проекта",
    "самоулучшение без ИИ": "Статья 48 · Три контура",
    "iOS 27 автообновление": "Статья 40 · Рельсы",
    "полная документация developer.apple.com": "Статья 37.1 · Атлас",
    "кит Figma iOS 27": "Статья 36.1 · Кит",
    "кадротека приложений": "Статья 36.2 · Кадротека",
    "лендинги и магазин Apple": "Статья 36.3 · Веб-атлас",
    "платформы (iOS·iPadOS·macOS·tvOS·visionOS·watchOS·App Store·Web)": "Статья 26.2 · Платформенные кодексы",
    "живой взгляд (не скриншоты)": "Статья 37.3 · Живой взгляд",
    "macOS-плечо и установка приложений": "Статья 49.1 · macOS-плечо",
    "Программа-95": "Статья 52 · Программа-95",
    "реестр поручений основателя": "Статья 53 · Реестр поручений",
    "дашборд в прямом эфире": "Статья 54 · Эфир",
    "большая семёрка консалтинга (аналитика·продукт·бизнес-логика)": "Статья 55 · Большая семёрка",
    "служба по подписке (PR-гейт·монитор·сертификация)": "Статья 56 · Служба",
    "динамика": "Статья 21.1 · Динамика", "эффекты": "Статья 22.1 · Эффекты",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ─────────────────────────────── status ────────────────────────────────
def cmd_status(root: Path) -> int:
    reg = root / "registry"
    srcs = json.loads((reg / "sources.json").read_text(encoding="utf-8"))["sources"]
    st_f = reg / "state" / "watch-state.json"
    st = json.loads(st_f.read_text(encoding="utf-8")) if st_f.exists() else {}
    w = json.loads((reg / "state" / "ios27-watch.json").read_text(encoding="utf-8"))
    tk = json.loads((reg / "standards" / "tokens.json").read_text(encoding="utf-8"))
    snapped = sum(1 for s in st.values() if s.get("sha"))
    print(f"BXE · {_now()}")
    print(f"  источники: {len(srcs)} · снято снимков: {snapped} · база стандартов: {tk['base']}")
    print(f"  iOS 27: {'ОБНАРУЖЕН ' + w.get('first_seen', '') if w.get('detected') else 'дозор, не обнаружен'}")
    last = max((s.get("last_checked", "") for s in st.values()), default="—")
    print(f"  последний обход: {last}")
    return 0


# ─────────────────────────────── ios27 ─────────────────────────────────
def scan_ios27(root: Path) -> list:
    """Улики из снимков и состояния. Детерминированный текстовый дозор."""
    reg = root / "registry"
    ev = []
    for snap in sorted((reg / "snapshots").glob("*.txt")):
        t = snap.read_text(encoding="utf-8", errors="replace")
        for m in list(IOS27.finditer(t))[:3]:
            a, b = max(0, m.start() - 60), min(len(t), m.end() + 60)
            ev.append({"source": snap.stem, "match": m.group(0),
                       "context": re.sub(r"\s+", " ", t[a:b]).strip()})
    return ev


def _skeleton(node, trail=""):
    """Схема ios26.5 → каркас следующей базы: каждое ЧИСЛО становится 🕳
    с памяткой прежнего значения. Строки-пояснения и refs сохраняются как
    контекст. Автоматика разворачивает РЕЛЬСЫ — заполняют их только замеры."""
    if isinstance(node, dict):
        return {k: _skeleton(v, f"{trail}.{k}" if trail else k) for k, v in node.items()}
    if isinstance(node, list):
        if node and all(isinstance(x, (int, float)) for x in node):
            return f"🕳 замерить (ios26: {node})"
        return [_skeleton(x, trail) for x in node]
    if isinstance(node, bool) or node is None:
        return node
    if isinstance(node, (int, float)):
        return f"🕳 замерить (ios26: {node})"
    return node


MANDATE_DOMAINS = [
    "кернинг/трекинг", "шрифты/роли", "цвета/поверхности", "отступы (⅓pt, сетки нет)",
    "иконки/SF Symbols", "плашки/чипы", "Liquid Glass/материал", "меню", "архитектура/суб-приложения",
    "blur/многослойность", "opacity", "свечение/тени", "анимация/кинетика", "жесты",
    "вибрации/haptics", "надавливание/press", "кроссплатформенность", "градиенты",
    "геймификация/рейтинги/отзывы", "маркетинг/popup", "продукты-эталоны (12)",
]


def scaffold_ios27(root: Path, first_seen: str) -> None:
    """Каркас смены базы: tokens.next.json (все числа 🕳) + MIGRATION.md.
    Идемпотентно: существующий каркас не перезаписывается — в нём живут замеры."""
    proto = root / "registry" / "standards" / "ios27"
    proto.mkdir(parents=True, exist_ok=True)
    nxt = proto / "tokens.next.json"
    if not nxt.exists():
        tok_f = root / "registry" / "standards" / "tokens.json"
        if not tok_f.exists():
            tok_f = ROOT / "registry" / "standards" / "tokens.json"  # переносимость: каркас всегда от измеренной базы департамента
        base = json.loads(tok_f.read_text(encoding="utf-8"))
        sk = _skeleton(base)
        sk["base"] = "ios27-dark (КАРКАС: ни одно 🕳 не закрыто — база НЕ действует, Э002)"
        sk["_рельсы"] = ("создано дозором " + first_seen + "; заполняется только конвейером "
                         "intake → инструменты → храповик; перенос чисел из ios26 запрещён")
        nxt.write_text(json.dumps(sk, ensure_ascii=False, indent=1), encoding="utf-8")
    mig = proto / "MIGRATION.md"
    if not mig.exists():
        mig.write_text(
            f"# iOS 27 · МИГРАЦИЯ БАЗЫ · каркас развёрнут {first_seen}\n\n"
            "Правило одно: домен закрыт, когда его числа стоят в `tokens.next.json` "
            "с адресами замеров. Знание дозора (`../../knowledge/`, домен ios27) — сырьё, не источник чисел.\n\n"
            "| Домен мандата | Статус |\n|---|---|\n"
            + "\n".join(f"| {d} | 🕳 |" for d in MANDATE_DOMAINS)
            + "\n\nЗакрытие: 🕳 → 📐 построчно; строка со статусом 🕳 не даёт переключить `base`.\n",
            encoding="utf-8")


def cmd_ios27(root: Path, issue: bool) -> int:
    reg = root / "registry"
    wf = reg / "state" / "ios27-watch.json"
    w = json.loads(wf.read_text(encoding="utf-8"))
    ev = scan_ios27(root)
    if ev and not w.get("detected"):
        w.update({"detected": True, "first_seen": _now(), "evidence": ev[:20]})
        proto = reg / "standards" / "ios27"
        proto.mkdir(parents=True, exist_ok=True)
        (proto / "DETECTED.md").write_text(
            f"# iOS 27 · ОБНАРУЖЕН {w['first_seen']}\n\n"
            "Дозор нашёл iOS 27 в официальных источниках Apple. Протокол смены базы (устав §5):\n\n"
            "1. Разведка уже сняла снимки — улики ниже; хроника в `../..//state/CHANGELOG.md`.\n"
            "2. Приём референсов: экраны iOS 27 кладутся как PDF — конвейер `ios26-intake` того же метода.\n"
            "3. ЗАМЕР, не перенос: ни одно число не попадает в tokens.json без адреса замера (ЗКН-Э002 —\n"
            "   правдоподобное число хуже отсутствующего). До замера база остаётся ios26.5, поле `base`\n"
            "   не переключается декларацией.\n"
            "4. Храповик только растёт: новые замеры добавляются, старые снимаются поправкой с объяснением.\n\n"
            "## Улики\n\n"
            + "\n".join(f"- `{e['source']}` · «…{e['context']}…»" for e in ev[:20]) + "\n",
            encoding="utf-8")
        print(f"iOS 27 ОБНАРУЖЕН · улик: {len(ev)} · протокол: registry/standards/ios27/DETECTED.md")
        scaffold_ios27(root, w["first_seen"])
    elif ev:
        w["evidence"] = ev[:20]
        scaffold_ios27(root, w.get("first_seen", _now()))
        print(f"iOS 27: подтверждён ранее ({w.get('first_seen')}) · улик сейчас: {len(ev)}")
    else:
        print("iOS 27: не обнаружен")
    w["last_scan"] = _now()

    if issue and w.get("detected") and not w.get("issue"):
        tok, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
        if tok and repo:
            body = ("Дозор Billions X Eyes (BXE) обнаружил iOS 27 в официальных источниках.\n\n"
                    + "\n".join(f"- `{e['source']}` — «…{e['context']}…»" for e in w["evidence"][:10])
                    + "\n\nПротокол: `registry/standards/ios27/DETECTED.md` (устав §5).")
            req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/issues",
                data=json.dumps({"title": "Billions X Eyes (BXE) · iOS 27 обнаружен — протокол смены базы",
                                 "body": body, "labels": ["bxad"]}).encode(),
                headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
                         "User-Agent": crawler.UA})
            try:
                with urllib.request.urlopen(req, timeout=25) as r:
                    w["issue"] = json.loads(r.read()).get("number")
                    print(f"issue открыт: #{w['issue']}")
            except Exception as e:
                print(f"issue не открыт: {type(e).__name__} (не критично, протокол уже в репозитории)")
    wf.write_text(json.dumps(w, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


# ─────────────────────────────── ratchet ───────────────────────────────
def apply_ratchet(root: Path, adapter_name: str, res: dict, baseline_file: Path) -> int:
    """Храповик советника: долг по каждому правилу может только уменьшаться.
    Рост = красный даже в report-режиме; улучшение само ужимает базу."""
    if not res.get("findings") and int(res.get("files", 0)) == 0:
        # ЗКН-Э006: пустой обход — не доказательство погашенного долга, а промах
        # адреса (неверный project_root, не забранный код). База неприкосновенна.
        print("  ХРАПОВИК: обойдено 0 файлов — база не тронута (пустой обход ≠ долг погашен)")
        return 1
    counts = {r: 0 for r in res.get("rules", [])}   # ноль тоже база: первое нарушение нового правила = рост
    for r, *_ in res["findings"]:
        counts[r] = counts.get(r, 0) + 1
    base = json.loads(baseline_file.read_text(encoding="utf-8")) if baseline_file.exists() else {}
    mine = base.get(adapter_name, {})
    worse = {r: (mine.get(r), counts.get(r, 0)) for r in set(mine) | set(counts)
             if r in mine and counts.get(r, 0) > mine[r]}
    if worse:
        for r, (b, n) in sorted(worse.items()):
            print(f"  ХРАПОВИК {r}: было {b} → стало {n} (долг растёт — красный)")
        return 1
    tightened = {r: n for r, n in counts.items() if mine.get(r, 10**9) > n}
    new_mine = {r: counts.get(r, 0) for r in sorted(set(mine) | set(counts))}
    if new_mine != mine:
        base[adapter_name] = new_mine
        baseline_file.write_text(json.dumps(base, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
        if tightened:
            print("  храповик ужат: " + " · ".join(f"{r}→{n}" for r, n in sorted(tightened.items())))
    return 0


# ─────────────────────────────── attach ────────────────────────────────
def cmd_attach(root: Path, project: str, report_glob: list, strict_glob: list,
               repo: str = "", prod: str = "", deploy_workflow: str = "") -> int:
    ad = {
        "project": project,
        "created": _now(),
        "enabled": True,
        "repo": repo,
        "branch": "main",
        "prod": prod,
        "live_pages": [prod] if prod else [],
        "deploy_workflow": deploy_workflow,
        "pt_to_css_px": 1,
        "allow_extra": [],
        "sizes_extra": [],
        "report": {"globs": report_glob,
                   "rules": ["AE1", "AE2", "AE3", "AE4", "AE5", "AE6", "AE7", "AE8", "AE9", "AE10", "AE11", "AE12", "AE13"]},
        "strict": {"globs": strict_glob, "rules": ["AE2", "AE3", "AE4", "AE6", "AE7"]},
        "radius_extra": [],
        "_порядок": "новый проект начинает с report; правило переводится в strict, когда его долг = 0",
    }
    out = root / "adapters" / f"{project}.json"
    out.write_text(json.dumps(ad, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"адаптер создан: {out.relative_to(root)} · дальше: eyes.py lint --adapter {project} --mode report")
    return 0


# ────────────────────────────── selftest ───────────────────────────────
def _importable(mod: str) -> bool:
    """Инструмент суда либо есть, либо его нет — без трейсбека посреди суда."""
    try:
        __import__(mod)
        return True
    except Exception:
        return False


def cmd_selftest(root: Path) -> int:
    """Каждый орган проверен на живом нарушении в обе стороны."""
    fx = root / "tests" / "fixtures"
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  ✓ " if cond else "  ✗ ") + name)
        ok = ok and cond

    print("SELFTEST · инструменты суда (объявлены, а не угаданы)")
    _need = {"numpy": "numpy", "PIL": "pillow", "fontTools": "fonttools"}
    _miss = [pkg for mod, pkg in _need.items() if not _importable(mod)]
    check("инструменты на месте: numpy · pillow · fonttools"
          + (f" — НЕТ: pip install {' '.join(_miss)}" if _miss else ""), not _miss)
    if _miss:
        print(f"  суд без инструментов не идёт: pip install {' '.join(_miss)}")
        return 1

    print("SELFTEST · исполнительная власть (lint)")
    tokens = json.loads((root / "registry" / "standards" / "tokens.json").read_text(encoding="utf-8"))
    adapter = {"report": {}, "strict": {"globs": ["bad.css"], "rules": ["AE1", "AE2", "AE3", "AE4", "AE5", "AE6"]},
               "allow_extra": [], "sizes_extra": []}
    res_bad = lint_mod.run(root, adapter, tokens, "strict", fx)
    got = {r for r, *_ in res_bad["findings"]}
    check("ломаю → красный: bad.css даёт AE1..AE6", {"AE1", "AE2", "AE3", "AE4", "AE5", "AE6"} <= got)
    adapter["strict"]["globs"] = ["good.css"]
    res_good = lint_mod.run(root, adapter, tokens, "strict", fx)
    check("чиню → зелёный: good.css чист", not res_good["findings"])
    adapter["strict"]["globs"] = ["commented.css"]
    res_c = lint_mod.run(root, adapter, tokens, "strict", fx)
    check("комментарий срезан до проверки: нарушитель в /* */ не считается", not res_c["findings"])

    print("SELFTEST · разведка (crawler, офлайн)")
    tmp = Path(tempfile.mkdtemp(prefix="eyes-"))
    try:
        reg = tmp / "registry"
        (reg / "state").mkdir(parents=True)
        (reg / "snapshots").mkdir()
        (reg / "sources.json").write_text(json.dumps({"sources": [
            {"id": "fixture-page", "url": "https://example.invalid/hig", "domains": ["материал"]}]}), encoding="utf-8")
        (reg / "state" / "CHANGELOG.md").write_text("# хроника\n", encoding="utf-8")
        fxdir = tmp / "fx"
        fxdir.mkdir()
        shutil.copy(fx / "page_v1.html", fxdir / "fixture-page.html")
        r1 = crawler.crawl(tmp, fixtures=fxdir)
        check("первый обход снимает снимок", r1["changed"] == ["fixture-page"])
        r2 = crawler.crawl(tmp, fixtures=fxdir)
        check("повторный обход без изменений молчит", r2["changed"] == [] and r2["unchanged"] == 1)
        shutil.copy(fx / "page_v2.html", fxdir / "fixture-page.html")
        r3 = crawler.crawl(tmp, fixtures=fxdir)
        log = (reg / "state" / "CHANGELOG.md").read_text(encoding="utf-8")
        check("живое изменение поймано и легло в хронику", r3["changed"] == ["fixture-page"] and "ИЗМЕНЕНИЕ" in log and "появились" in log)

        print("SELFTEST · дозор iOS 27")
        (reg / "state" / "ios27-watch.json").write_text('{"detected": false}', encoding="utf-8")
        check("чистый снимок → не обнаружен", scan_ios27(tmp) == [])
        shutil.copy(fx / "ios27_page.html", fxdir / "fixture-page.html")
        crawler.crawl(tmp, fixtures=fxdir)
        ev = scan_ios27(tmp)
        check("страница с iOS 27 → обнаружен с уликой", bool(ev) and "iOS 27" in ev[0]["match"])
        cmd_ios27(tmp, issue=False)
        w = json.loads((reg / "state" / "ios27-watch.json").read_text(encoding="utf-8"))
        check("протокол DETECTED.md создан, статус зафиксирован",
              w.get("detected") and (reg / "standards" / "ios27" / "DETECTED.md").exists())
        nxt_f = reg / "standards" / "ios27" / "tokens.next.json"
        mig_f = reg / "standards" / "ios27" / "MIGRATION.md"
        nxt = json.loads(nxt_f.read_text(encoding="utf-8"))
        flat = json.dumps(nxt, ensure_ascii=False)
        check("рельсы новой базы: каркас развёрнут, все числа 🕳, чисел ios26 без пометки нет",
              mig_f.exists() and "🕳" in flat
              and not re.search(r'":\s*\d', flat.replace('"level":', ""))
              and "НЕ действует" in str(nxt.get("base", "")))
        nxt_f.write_text(json.dumps({"base": "заполнено замером"}, ensure_ascii=False), encoding="utf-8")
        cmd_ios27(tmp, issue=False)
        check("каркас идемпотентен: замеры в нём не затираются",
              json.loads(nxt_f.read_text(encoding="utf-8"))["base"] == "заполнено замером")
        print("SELFTEST · разведка DocC (JS-скорлупа обходится данными)")
        shutil.copy(fx / "hig-fixture.json", fxdir / "fixture-page.json")
        (fxdir / "fixture-page.html").unlink()
        (reg / "state" / "watch-state.json").write_text("{}", encoding="utf-8")
        crawler.crawl(tmp, fixtures=fxdir)
        snap_t = (reg / "snapshots" / "fixture-page.txt").read_text(encoding="utf-8")
        st = json.loads((reg / "state" / "watch-state.json").read_text(encoding="utf-8"))
        check("DocC-JSON → полный текст и заголовки, маршрут записан",
              "## Best practices" in snap_t and "44x44 pt" in snap_t
              and st["fixture-page"].get("route") == "docc")

        print("SELFTEST · знание (digest)")
        r_d1 = digest_mod.build(tmp)
        kn = (reg / "knowledge" / "fixture-page.md").read_text(encoding="utf-8")
        check("нормативное извлечено, декоративное отброшено",
              "44x44 pt" in kn and "Avoid pairing" in kn and "Reduce Motion" in kn and "Decorative flourishes" not in kn)
        r_d2 = digest_mod.build(tmp)
        check("знание детерминировано: повторный прогон без изменений",
              r_d1["changed"] == ["fixture-page"] and r_d2["changed"] == []
              and (reg / "knowledge" / "INDEX.md").exists())

        print("SELFTEST · пробы iOS 27")
        (reg / "ios27-probes.json").write_text(json.dumps({"probes": [
            {"id": "probe-alive", "url": "https://example.invalid/a", "domains": ["ios27"]},
            {"id": "probe-dead", "url": "https://example.invalid/b", "domains": ["ios27"]}]}), encoding="utf-8")
        shutil.copy(fx / "probe-alive.html", fxdir / "probe-alive.html")
        rp = crawler.probe(tmp, fixtures=fxdir)
        ids = {s["id"] for s in json.loads((reg / "sources.json").read_text(encoding="utf-8"))["sources"]}
        check("живая проба завербована, мёртвая — нет",
              rp["enrolled"] == ["probe-alive"] and "probe-alive" in ids and "probe-dead" not in ids)
        rp2 = crawler.probe(tmp, fixtures=fxdir)
        check("вербовка идемпотентна", rp2["enrolled"] == [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("SELFTEST · исполнительная власть (AE7–AE11)")
    adapter = {"strict": {"globs": ["bad.css"], "rules": ["AE7", "AE8", "AE9", "AE10", "AE11", "AE12", "AE13"]},
               "allow_extra": [], "sizes_extra": [], "radius_extra": []}
    got7 = {r for r, *_ in lint_mod.run(root, adapter, tokens, "strict", fx)["findings"]}
    check("ломаю → красный: bad.css даёт AE7..AE13", {"AE7", "AE8", "AE9", "AE10", "AE11", "AE12", "AE13"} <= got7)
    adapter["strict"]["globs"] = ["good.css"]
    check("чиню → зелёный: good.css чист по AE7..AE13 (Reduce Motion уважен)",
          not lint_mod.run(root, adapter, tokens, "strict", fx)["findings"])
    adapter["strict"]["globs"] = ["commented.css"]
    check("нарушители AE7..AE13 в комментарии не считаются",
          not lint_mod.run(root, adapter, tokens, "strict", fx)["findings"])

    print("SELFTEST · храповик советника")
    tmp2 = Path(tempfile.mkdtemp(prefix="eyes-r-"))
    try:
        bl = tmp2 / "baseline.json"
        res_w = {"rules": ["AE1", "AE9"], "findings": [("AE1", "f", 1, "x")] * 3}
        check("первый замер пишет базу и зелёный (ноль тоже прибит)",
              apply_ratchet(root, "t", res_w, bl) == 0
              and json.loads(bl.read_text())["t"] == {"AE1": 3, "AE9": 0})
        res_zero_worse = {"rules": ["AE1", "AE9"], "findings": [("AE1", "f", 1, "x")] * 3 + [("AE9", "f", 2, "y")]}
        check("нарушение правила с нулевой базой → красный",
              apply_ratchet(root, "t", res_zero_worse, bl) == 1)
        res_worse = {"rules": ["AE1", "AE9"], "findings": [("AE1", "f", 1, "x")] * 4}
        check("долг вырос → красный", apply_ratchet(root, "t", res_worse, bl) == 1)
        res_better = {"rules": ["AE1", "AE9"], "findings": [("AE1", "f", 1, "x")] * 2}
        check("долг упал → зелёный и база ужалась",
              apply_ratchet(root, "t", res_better, bl) == 0 and json.loads(bl.read_text())["t"]["AE1"] == 2)
        # ЗКН-Э006 в обе стороны: пустой обход не ужимает базу и красит прогон
        before = bl.read_text(encoding="utf-8")
        empty = {"rules": ["AE1", "AE9"], "findings": [], "files": 0}
        check("пустой обход → красный, база не тронута",
              apply_ratchet(root, "t", empty, bl) == 1
              and bl.read_text(encoding="utf-8") == before)
        bl2 = tmp2 / "baseline2.json"
        check("обход с файлами и нулём находок → зелёный, база пишется",
              apply_ratchet(root, "u", {"rules": ["AE1"], "findings": [], "files": 7}, bl2) == 0
              and json.loads(bl2.read_text(encoding="utf-8"))["u"]["AE1"] == 0)

        print("SELFTEST · подключение (attach)")
        proj = tmp2 / "proj"
        proj.mkdir()
        (proj / "a.css").write_text(".x{box-shadow:0 0 4px #000}", encoding="utf-8")
        ad_dir = tmp2 / "adapters"
        ad_dir.mkdir()
        real_ad = ROOT / "adapters"
        # attach пишет в root/adapters — используем временный root-скелет
        (tmp2 / "registry" / "standards").mkdir(parents=True)
        shutil.copy(root / "registry" / "standards" / "tokens.json",
                    tmp2 / "registry" / "standards" / "tokens.json")
        cmd_attach(tmp2, "demo", ["*.css"], [])
        ad = json.loads((tmp2 / "adapters" / "demo.json").read_text(encoding="utf-8"))
        res_att = lint_mod.run(tmp2, ad, tokens, "report", proj)
        check("адаптер создан и линт по нему видит долг",
              "AE7" in ad["report"]["rules"] and any(r == "AE2" for r, *_ in res_att["findings"]))
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)

    print("SELFTEST · атлас (цикл документации: обе стороны)")
    import atlas as atlas_mod2
    tmpa = Path(tempfile.mkdtemp(prefix="eyes-a-"))
    try:
        (tmpa / "registry" / "state").mkdir(parents=True)
        (tmpa / "registry" / "state" / "CHANGELOG.md").write_text("", encoding="utf-8")
        fxa = tmpa / "fx"; fxa.mkdir()
        (fxa / "documentation.json").write_text(json.dumps({
            "metadata": {"title": "Root"},
            "references": {"a": {"url": "/documentation/aaa"}, "b": {"url": "/documentation/bbb"}},
            "primaryContentSections": []}), encoding="utf-8")
        (fxa / "documentation__aaa.json").write_text(json.dumps({
            "metadata": {"title": "AAA"}, "references": {},
            "primaryContentSections": [{"content": [{"type": "paragraph", "inlineContent": [
                {"type": "text", "text": "Use a minimum tappable area of 44x44 pt for controls."}]}]}]}), encoding="utf-8")
        (fxa / "documentation__bbb.json").write_text(json.dumps({
            "metadata": {"title": "BBB"}, "references": {},
            "primaryContentSections": [{"content": [{"type": "paragraph", "inlineContent": [
                {"type": "text", "text": "A plain descriptive line without prescriptions."}]}]}]}), encoding="utf-8")
        r1 = atlas_mod2.step(tmpa, budget=1, fixtures=fxa)
        check("бюджет уважается: шаг 1 → пройдена 1, очередь выросла",
              r1["walked"] == 1 and r1["frontier"] == 2)
        r2 = atlas_mod2.step(tmpa, budget=10, fixtures=fxa)
        lib = (tmpa / "registry" / "library" / "aaa.jsonl")
        check("цикл сам раскрывает дерево и добывает закон в библиотеку",
              r2["walked"] == 2 and lib.exists() and "44x44" in lib.read_text(encoding="utf-8")
              and (tmpa / "registry" / "library" / "INDEX.md").exists())
        r3 = atlas_mod2.step(tmpa, budget=10, fixtures=fxa)
        check("фронтир пуст → второй круг переобхода, без ложных изменений",
              r3["walked"] == 3 and r3["changed"] == 0)
        (fxa / "documentation__aaa.json").write_text(json.dumps({
            "metadata": {"title": "AAA"}, "references": {},
            "primaryContentSections": [{"content": [{"type": "paragraph", "inlineContent": [
                {"type": "text", "text": "Use a minimum tappable area of 48x48 pt for controls."}]}]}]}), encoding="utf-8")
        r4 = atlas_mod2.step(tmpa, budget=10, fixtures=fxa)
        chg = (tmpa / "registry" / "state" / "CHANGELOG.md").read_text(encoding="utf-8")
        check("подмена страницы на круге → «закон изменился» в хронике",
              r4["changed"] == 1 and "закон изменился" in chg)
    finally:
        shutil.rmtree(tmpa, ignore_errors=True)

    print("SELFTEST · кит (разбор .sketch без аккаунтов)")
    import io, zipfile
    import figkit as figkit_mod2
    tmpk = Path(tempfile.mkdtemp(prefix="eyes-k-"))
    try:
        (tmpk / "registry" / "state").mkdir(parents=True)
        (tmpk / "registry" / "state" / "CHANGELOG.md").write_text("", encoding="utf-8")
        fxk = tmpk / "fx"; fxk.mkdir()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("document.json", json.dumps({
                "sharedSwatches": {"objects": [{"name": "System Red", "value": {"red": 1, "green": 0.231, "blue": 0.188, "alpha": 1}}]},
                "layerTextStyles": {"objects": [{"name": "Body/Regular", "value": {"textStyle": {"encodedAttributes": {
                    "MSAttributedStringFontAttribute": {"attributes": {"name": "SFPro-Regular", "size": 17}},
                    "kerning": -0.43,
                    "paragraphStyle": {"maximumLineHeight": 22}}}}}]}}))
            z.writestr("pages/p1.json", json.dumps({"name": "Controls", "layers": [
                {"_class": "symbolMaster", "name": "Button/Filled", "layers": [
                    {"_class": "rectangle", "name": "bg", "fixedRadius": 26, "points": []}]}]}))
        (fxk / "mini-kit.sketch").write_bytes(buf.getvalue())
        rk = figkit_mod2.run_sketch_arm(tmpk, fixtures=fxk)
        kj = json.loads((tmpk / "registry" / "standards" / "kit" / "fixture-kit-sketch.json").read_text(encoding="utf-8"))
        check("кит разобран: цвет, текст-стиль 17pt/22/-0.43, радиус 26, символ — с адресами kit:",
              rk["status"] == "извлечено"
              and kj["colors"]["System Red"]["value"] == "#FF3B30"
              and kj["text_styles"]["Body/Regular"]["size_pt"] == 17
              and kj["text_styles"]["Body/Regular"]["kerning"] == -0.43
              and "26.0" in kj["corner_radii"] and kj["symbols"] == ["Button/Filled"]
              and kj["colors"]["System Red"]["at"].startswith("kit:"))
    finally:
        shutil.rmtree(tmpk, ignore_errors=True)

    print("SELFTEST · кадротека и веб-атлас (обе стороны)")
    import screens as screens_mod
    tmpw = Path(tempfile.mkdtemp(prefix="eyes-w-"))
    try:
        (tmpw / "registry" / "state").mkdir(parents=True)
        (tmpw / "registry" / "state" / "CHANGELOG.md").write_text("", encoding="utf-8")
        # кадротека: 2×2-кадры — лестница против чужого цвета
        from PIL import Image as _Im
        fr = tmpw / "frames" / "TestApp"; fr.mkdir(parents=True)
        im = _Im.new("RGB", (4, 4), (0, 0, 0))
        for x in range(2):
            im.putpixel((x, 0), (0x1C, 0x1C, 0x1E))
        im.putpixel((3, 3), (0x8E, 0x8E, 0x8E))
        im.save(fr / "a.PNG")
        rs = screens_mod.run(tmpw, tmpw / "frames")
        pj = json.loads((tmpw / "registry" / "screens" / "passports" / "TestApp.json").read_text(encoding="utf-8"))
        fr0 = pj["frames"][0]
        check("кадр разобран: лестница посчитана, двойник пойман, адрес screen:",
              rs["frames"] == 1 and abs(fr0["ladder_share"]["#1C1C1E"] - 2/16) < 1e-6
              and fr0["forbidden_hits"].get("#8E8E8E") == 1
              and fr0["at"].startswith("screen:TestApp/"))
        # веб-атлас: страница+css → паспорт структуры и закон типографики
        (tmpw / "registry" / "web-sources.json").write_text(json.dumps(
            {"pages": ["https://www.apple.com/fixture/"]}), encoding="utf-8")
        fxw = tmpw / "fxw"; fxw.mkdir()
        (fxw / "www-apple-com-fixture.html").write_text(
            '<link rel="stylesheet" href="/v/fixture/main.css">'
            '<section class="section-hero x"></section><section class="section-gallery"></section>'
            '<a class="button">Buy</a><h1>t</h1><img><video></video>', encoding="utf-8")
        (fxw / (__import__("crawler")._slug("/v/fixture/main.css") + ".css")).write_text(
            ".typography-hero-headline{font-size:80px;line-height:1.05;letter-spacing:-0.015em;font-weight:600}",
            encoding="utf-8")
        rw = weblab_mod.run(tmpw, fixtures=fxw)
        wp = json.loads((tmpw / "registry" / "weblab" / "www-apple-com-fixture.json").read_text(encoding="utf-8"))
        lib = (tmpw / "registry" / "library" / "web-landings.jsonl").read_text(encoding="utf-8")
        check("лендинг разобран: секции по порядку, CTA/медиа, закон typography с адресом css:",
              wp["sections"] == ["section-hero", "section-gallery"] and wp["cta"] == 1
              and rw["typo_laws_new"] == 1 and '"font-size": "80px"' in lib and '"at": "css:main.css:' in lib)
        rw2 = weblab_mod.run(tmpw, fixtures=fxw)
        check("законы веб-атласа идемпотентны по адресу", rw2["typo_laws_new"] == 0)
    finally:
        shutil.rmtree(tmpw, ignore_errors=True)

    print("SELFTEST · живой взгляд (мок: обе стороны)")
    import liveview as lv
    tok = json.loads((root / "registry" / "standards" / "tokens.json").read_text(encoding="utf-8"))
    bad_els = [
        {"sel": "div.card", "backgroundColor": "rgb(20, 20, 24)", "boxShadow": "none", "textShadow": "none",
         "backdropFilter": "blur(20px)", "fontFamily": "Papyrus, fantasy", "transition": "0.3s|ease"},
        {"sel": "span.dup", "backgroundColor": "rgb(142, 142, 142)",
         "boxShadow": "rgba(0, 0, 0, 0.14) 0px 10px 30px 0px",
         "textShadow": "none", "backdropFilter": "none", "fontFamily": "-apple-system"},
    ]
    got_lv = {r for r, *_ in lv.check_dump(bad_els, tok)}
    check("живые нарушения пойманы: AE1·AE2·AE6·AE7·AE10",
          {"AE1", "AE2", "AE6", "AE7", "AE10"} <= got_lv)
    good_els = [{"sel": "div.ok", "backgroundColor": "rgb(28, 28, 30)", "boxShadow": "none", "textShadow": "none",
                 "backdropFilter": "blur(20px) saturate(180%)", "fontFamily": "-apple-system, system-ui"},
                {"sel": "div.lens", "backgroundColor": "rgba(0, 0, 0, 0)",
                 "boxShadow": "rgba(255, 255, 255, 0.95) 0px 1.5px 1px 0px inset",
                 "backdropFilter": "blur(1px) saturate(1.9)", "fontFamily": "-apple-system"},
                {"sel": "svg.icon", "backgroundColor": "rgba(0, 0, 0, 0)", "boxShadow": "none",
                 "textShadow": "none", "backdropFilter": "none", "fontFamily": "Arial"}]
    check("чистый живой DOM → находок нет (белый inset-блик и svg-шрифт законны)",
          lv.check_dump(good_els, tok) == [])
    check("канон холста: чёрный drop в light — не AE2, в dark — AE2",
          not any(r == "AE2" for r, *_ in lv.check_dump([bad_els[1]], tok, theme="light"))
          and any(r == "AE2" for r, *_ in lv.check_dump([bad_els[1]], tok, theme="dark")))

    print("SELFTEST · рука шрифтов (метрики первоисточника)")
    import figkit as fk2
    from fontTools.fontBuilder import FontBuilder
    import io as _io
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder([".notdef", "H"]); fb.setupCharacterMap({72: "H"})
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    pen = TTGlyphPen(None); pen.moveTo((0,0)); pen.lineTo((0,714)); pen.lineTo((50,714)); pen.lineTo((50,0)); pen.closePath()
    fb.setupGlyf({".notdef": TTGlyphPen(None).glyph(), "H": pen.glyph()})
    fb.setupHorizontalMetrics({".notdef": (500,0), "H": (100,0)})
    fb.setupHorizontalHeader(ascent=950, descent=-250)
    fb.setupNameTable({"familyName": "BXETest", "styleName": "Regular"})
    fb.setupOS2(sCapHeight=714, sxHeight=500)
    fb.setupPost()
    buf = _io.BytesIO(); fb.save(buf)
    m = fk2.parse_font_bytes(buf.getvalue(), "font:test.dmg:BXETest.ttf")
    check("метрики сняты точно: em 1000 · крышка 714 → доля 0.714 (наш канон)",
          m["unitsPerEm"] == 1000 and m["capHeight"] == 714 and m["capHeight_fraction"] == 0.714
          and m["at"].startswith("font:"))

    print("SELFTEST · поручения и эфир (ст. 53–54: обе стороны)")
    import dashboard as dash_mod
    tj = json.loads((root / "registry" / "tasks.json").read_text(encoding="utf-8"))
    ALL = [t for g, its in tj.items() if not g.startswith("_") for t in its]
    ids = [t["id"] for t in ALL]
    ST = {"done", "active", "queued", "blocked", "partial"}
    check("реестр поручений целостен: id уникальны · статусы из множества · у каждого орган",
          len(ids) == len(set(ids)) and all(t["status"] in ST and t.get("organ") for t in ALL) and len(ALL) >= 20)
    dd = dash_mod.collect()
    st_atlas = json.loads((root / "registry" / "atlas" / "state.json").read_text(encoding="utf-8"))
    check("эфир живыми числами: атлас в дашборде == реестру, задачи посчитаны",
          dd["atlas"]["visited"] == st_atlas["visited"] and dd["tasks"]["bxad"]["done"] >= 8
          and (root / "dashboard" / "DASHBOARD.md").exists() and (root / "dashboard" / "index.html").exists())
    baddup = json.loads(json.dumps(tj)); baddup["bxad"].append(dict(baddup["bxad"][0]))
    ids2 = [t["id"] for g, its in baddup.items() if not g.startswith("_") for t in its]
    check("подделка (дубль id поручения) ловится", len(ids2) != len(set(ids2)))

    print("SELFTEST · большая семёрка (фикстуры: обе стороны)")
    tmpc = Path(tempfile.mkdtemp(prefix="eyes-c-"))
    try:
        (tmpc / "registry" / "state").mkdir(parents=True)
        (tmpc / "registry" / "state" / "CHANGELOG.md").write_text("", encoding="utf-8")
        (tmpc / "registry" / "big7-sources.json").write_text(json.dumps(
            {"firms": {"bain": ["https://fixture.big7/insights"]}, "budget_per_day": 5}), encoding="utf-8")
        fxc = tmpc / "fxc"; fxc.mkdir()
        (fxc / "https-fixture-big7-insights"[:80].replace("/", "-").replace(":", "-").replace(".", "-").lstrip("-")).with_suffix(".html")
        import re as _re
        name = _re.sub(r"[^a-z0-9]+", "-", "https://fixture.big7/insights".lower()).strip("-")[:80] + ".html"
        (fxc / name).write_text("<p>Companies must adopt zero-based budgeting to fund growth. "
                                "We apply the pyramid principle and net promoter score in reviews.</p>"
                                "<p>The weather is nice today in the office lobby garden area, isn't it, dear colleagues of ours.</p>", encoding="utf-8")
        rc1 = consult_mod.run(tmpc, fixtures=fxc)
        lib7 = (tmpc / "registry" / "library" / "big7.jsonl").read_text(encoding="utf-8")
        big = json.loads((tmpc / "registry" / "bizlab" / "state.json").read_text(encoding="utf-8"))
        check("семёрка: императив пойман положением с адресом page:, рамки ZBB/Минто/NPS в карте",
              rc1["laws_new"] == 1 and '"at": "page:https://fixture.big7/insights"' in lib7
              and {"ZBB", "Пирамида Минто", "NPS"} <= set(big["frames"]))
        rc2 = consult_mod.run(tmpc, fixtures=fxc)
        check("семёрка идемпотентна: повтор не плодит положений", rc2["laws_new"] == 0)
    finally:
        shutil.rmtree(tmpc, ignore_errors=True)

    print("SELFTEST · кит (очередь Sketch-китов)")
    import figkit as fk
    names = ["tvOS-18-Design-Templates-Sketch.dmg", "visionOS-2-Design-Templates-Sketch.dmg",
             "tvOS-18-Production-Templates-Photoshop.dmg", "Bezel-iPhone-17.dmg",
             "tvOS-18-Production-Templates-Sketch.dmg"]
    check("очередь: следующий невзятый Sketch-кит, Photoshop/безель мимо, по одному",
          fk.pick_targets(names, {"tvOS-18-Design-Templates-Sketch.dmg"}) == ["tvOS-18-Production-Templates-Sketch.dmg"]
          and fk.pick_targets(names, set(names)) == [])

    print("SELFTEST · служба M1 (парсер диффа)")
    import review as review_mod
    patch = "@@ -1,2 +1,4 @@\n context\n+.bad { color: #8E8E8E; }\n+.ok { color: var(--x); }\n-old line\n context2\n@@ -10 +12,2 @@\n+.later { box-shadow: 0 10px 30px rgba(0,0,0,.5); }"
    added = review_mod.parse_added(patch)
    check("дифф разобран: номера НОВЫХ строк точны, удалённые не мешают",
          added == {2: ".bad { color: #8E8E8E; }", 3: ".ok { color: var(--x); }",
                    12: ".later { box-shadow: 0 10px 30px rgba(0,0,0,.5); }"})
    check("пустой патч → пусто", review_mod.parse_added("") == {})

    print("SELFTEST · служба M1-Б (надзор по коммитам)")
    import watch as watch_mod
    check("надзор: суд органа зелёный (отбор, порядок, честность области)",
          watch_mod.selftest() == 0)
    _diff = {"a.css": {5: "x"}}
    _f = [("AE1", "a.css", 5, "в диффе"), ("AE2", "a.css", 6, "мимо диффа")]
    check("ломаю → красный: тронутая строка названа; чиню → зелёный: нетронутая молчит",
          [h["rule"] for h in watch_mod.pick_hits(_diff, _f)] == ["AE1"])

    print("SELFTEST · служба M2 (дифф базовой линии)")
    import monitor as mon
    oldf = [["example-com:AE10", "button", "Arial"], ["example-com:AE2", "div.gtab-bg", "чёрный drop"]]
    newf = [["example-com:AE2", "div.gtab-bg", "чёрный drop"], ["example-com:AE1", "div.x", "фон вне лестницы"]]
    dd2 = mon.diff_findings(oldf, newf)
    check("монитор: регресс пойман, починка подтверждена, неизменное молчит",
          [f[0] for f in dd2["new"]] == ["example-com:AE1"] and [f[0] for f in dd2["gone"]] == ["example-com:AE10"])
    check("монитор: идентичные снятия → тишина",
          mon.diff_findings(newf, newf) == {"new": [], "gone": []})

    print("SELFTEST · служба M3 (формула объявлена и детерминирована)")
    import certify as cert
    c0 = {"strict": 2, "report": 400, "live": 9, "verify_diverg": 1}
    check("скор по формуле: 100−4−5−13.5−5 = 72.5 · C",
          cert.score_of(c0) == 72.5 and cert.grade(72.5) == "C")
    check("чистый проект → 100 · A+", cert.score_of({"strict": 0, "report": 0, "live": 0, "verify_diverg": 0}) == 100.0
          and cert.grade(100.0) == "A+")

    print("SELFTEST · служба M6 (бриф недели)")
    import brief as brief_mod
    tmpb = Path(tempfile.mkdtemp(prefix="eyes-b-"))
    try:
        (tmpb / "registry" / "library").mkdir(parents=True)
        (tmpb / "registry" / "bizlab").mkdir(parents=True)
        (tmpb / "registry" / "state").mkdir(parents=True)
        (tmpb / "registry" / "state" / "CHANGELOG.md").write_text("", encoding="utf-8")
        (tmpb / "registry" / "library" / "big7.jsonl").write_text(json.dumps(
            {"firm": "bain", "text": "Companies must adopt zero-based budgeting.",
             "at": "page:https://fixture/1"}, ensure_ascii=False) + "\n", encoding="utf-8")
        (tmpb / "registry" / "bizlab" / "state.json").write_text(json.dumps(
            {"firms": {}, "frames": {"ZBB": 21, "NPS": 3}}), encoding="utf-8")
        (tmpb / "registry" / "bizlab" / "frames-week.json").write_text(json.dumps({"ZBB": 19}), encoding="utf-8")
        import importlib
        brief_mod.ROOT = tmpb
        rb = brief_mod.run()
        latest = (tmpb / "briefs" / "latest.md").read_text(encoding="utf-8")
        check("бриф: положение дословно с адресом, дифф рамки +2, канонический вопрос ZBB",
              "zero-based budgeting" in latest and "page:https://fixture/1" in latest
              and "ZBB: +2 (всего 21)" in latest and "статьи расходов" in latest and rb["grew"] >= 1)
        brief_mod.ROOT = ROOT
    finally:
        brief_mod.ROOT = ROOT
        shutil.rmtree(tmpb, ignore_errors=True)

    print("SELFTEST · служба M5 (страж App Store)")
    import appstore as guard
    fx_html = "<h2>1.1 Objectionable Content</h2><p>Apps should not include...</p><li>5.1.1 Data Collection and Storage</li><p>2.3 Accurate Metadata</p>"
    pts = guard.parse_points(fx_html)
    check("гайдлайны: пункты извлечены дословно с номерами и адресами #N.N",
          [p["n"] for p in pts] == ["1.1", "2.3", "5.1.1"]
          and pts[0]["title"] == "Objectionable Content"
          and pts[2]["at"].endswith("#5.1.1"))
    tmpg = Path(tempfile.mkdtemp(prefix="eyes-g-"))
    try:
        (tmpg / "apps" / "web" / "src").mkdir(parents=True)
        (tmpg / "apps" / "web" / "src" / "App.tsx").write_text('<a href="/privacy">Privacy</a>', encoding="utf-8")
        chk_p = guard.repo_check(tmpg, ["privacy"])
        chk_m = guard.repo_check(tmpg, ["nonexistent-word-xyz"])
        check("автопроверка: privacy найден с путём App.tsx:1, отсутствие — честное НЕТ",
              chk_p["ok"] and chk_p["at"].endswith("App.tsx:1") and not chk_m["ok"])
    finally:
        shutil.rmtree(tmpg, ignore_errors=True)

    print("SELFTEST · конституция (ст. 45: полнота мандата машиной)")
    const_t = (root / "CONSTITUTION.md").read_text(encoding="utf-8")
    missing = [d for d, anchor in FOUNDER_MANDATE.items() if anchor not in const_t]
    check(f"каждый из {len(FOUNDER_MANDATE)} доменов мандата несёт статью", not missing)
    if missing:
        for d in missing:
            print(f"    ПОТЕРЯН: {d}")
    check("проверка живая: изъятие статьи было бы поймано",
          bool([d for d, a in FOUNDER_MANDATE.items()
                if a not in const_t.replace("Статья 24 · Вибрации", "")]) )
    check("числа кодекса совпадают с реестром: кнопка/чип/крышка/стекло/нажатие",
          all(s in const_t for s in ("32.0", "35.0", "±0.4", ".05", ".06", ".09",
                                     "383", "120", "2.5–2.6", "#1C1C1E", "#2C2C2E")))

    print("SELFTEST · изученность (study: обе стороны)")
    import study as study_mod2
    rs = study_mod2.run(root)
    check("все статьи кодекса изучены (замер/знание/🕳), не изучено 0",
          not rs["bad"] and rs["articles"] >= 30 and rs["knowledge"] > 1000)
    tmps = Path(tempfile.mkdtemp(prefix="eyes-s-"))
    try:
        (tmps / "registry" / "state").mkdir(parents=True)
        (tmps / "registry" / "knowledge").mkdir()
        shutil.copy(root / "registry" / "sources.json", tmps / "registry" / "sources.json")
        bare = (root / "CONSTITUTION.md").read_text(encoding="utf-8").replace(
            "Дозор: `hig-split-views`, `hig-designing-for-ipados` (архитектура\nразделённых пространств).", "")
        bare = bare.replace("прецедент ЗКН-Э003", "прецедент")
        (tmps / "CONSTITUTION.md").write_text(bare, encoding="utf-8")
        check("статья без замера/знания/🕳 → НЕ ИЗУЧЕНО пойман",
              any("Суб-приложения" in b for b in study_mod2.run(tmps)["bad"]))
    finally:
        shutil.rmtree(tmps, ignore_errors=True)

    print("SELFTEST · сверка (verify: обе стороны)")
    import verify as verify_mod
    rv = verify_mod.run(root)
    check("живая сверка сходится: расхождений 0", rv["bad"] == 0 and rv["confirmed"] >= 3)
    tmpv = Path(tempfile.mkdtemp(prefix="eyes-v-"))
    try:
        (tmpv / "registry" / "standards").mkdir(parents=True)
        (tmpv / "registry" / "state").mkdir()
        (tmpv / "registry" / "knowledge").mkdir()
        shutil.copy(root / "CONSTITUTION.md", tmpv / "CONSTITUTION.md")
        tk2 = json.loads((root / "registry" / "standards" / "tokens.json").read_text(encoding="utf-8"))
        tk2["geometry"]["button_height_pt"] = 33.0  # подделка: конституция говорит 32.0
        (tmpv / "registry" / "standards" / "tokens.json").write_text(
            json.dumps(tk2, ensure_ascii=False), encoding="utf-8")
        (tmpv / "registry" / "state" / "watch-state.json").write_text("{}", encoding="utf-8")
        (tmpv / "registry" / "knowledge" / "hig-buttons.md").write_text(
            "Нормативных положений: 1\n- Use at least 44x44 pt.\n", encoding="utf-8")
        rv2 = verify_mod.run(tmpv)
        check("подделка числа базы → РАСХОЖДЕНИЕ пойман (и в кодексе, и против 44×44)",
              rv2["bad"] >= 2)
    finally:
        shutil.rmtree(tmpv, ignore_errors=True)

    print("SELFTEST · оглавление DocC (topicSections → references)")
    import extractor as ex_mod
    idx_fx = json.dumps({"metadata": {"title": "HIG"},
                         "references": {"doc://a": {"title": "Buttons"}, "doc://b": {"title": "Sliders"}},
                         "topicSections": [{"title": "Components", "identifiers": ["doc://a", "doc://b"]}]})
    exd = ex_mod.extract_docc(idx_fx)
    check("индекс раскрыт: секция стала заголовком, страницы — строками",
          "Components" in exd["headings"] and "Buttons" in exd["text"] and "Sliders" in exd["text"])

    print("SELFTEST · реестр выданных сертификатов (подлинность в обе стороны)")
    import certify as cert_mod
    cd = tmp2 / "certs" / "demo"
    cd.mkdir(parents=True, exist_ok=True)
    (cd / "2026-07.html").write_text("<html>сертификат</html>", encoding="utf-8")
    cert_mod.register(cd, "demo", "2026-07", 91.5, "A", "2026-07-28 00:00 UTC")
    check("выданное сходится с реестром → чисто", cert_mod.verify_register(cd) == [])
    (cd / "2026-07.html").write_text("<html>подменено</html>", encoding="utf-8")
    check("подмена выданного документа поймана", len(cert_mod.verify_register(cd)) == 1)
    cert_mod.register(cd, "demo", "2026-07", 91.5, "A", "2026-07-28 00:00 UTC")
    check("перевыдача с новым отпечатком → снова чисто", cert_mod.verify_register(cd) == [])
    (cd / "2026-08.html").write_text("<html>мимо реестра</html>", encoding="utf-8")
    check("выдача мимо реестра поймана", len(cert_mod.verify_register(cd)) == 1)
    (cd / "2026-08.html").unlink()

    print("SELFTEST · эфир на домене (ст. 54: свежесть проверяется, а не обещается)")
    import livecheck as lc_mod
    lim = 15.0
    check("совпадение отпечатков → зелёный",
          lc_mod.verdict(lc_mod.lag_minutes("2026-07-28 06:32 UTC", "2026-07-28 06:32 UTC"), lim)[0] == 0)
    check("отставание домена за пределом → красный",
          lc_mod.verdict(lc_mod.lag_minutes("2026-07-28 06:32 UTC", "2026-07-28 05:10 UTC"), lim)[0] == 1)
    check("домен впереди репозитория → красный (расхождение, не свежесть)",
          lc_mod.verdict(lc_mod.lag_minutes("2026-07-28 06:00 UTC", "2026-07-28 06:20 UTC"), lim)[0] == 1)
    check("адрес эфира живёт в реестре, не в коде",
          "url" in json.loads((root / "registry" / "site.json").read_text(encoding="utf-8")))

    if not isinstance(ok, bool):  # мета-страж: вердикт суда перезаписан тенью — это провал сам по себе
        print("SELFTEST: КРАСНЫЙ — вердикт суда был перезаписан (тень переменной ok)")
        return 1
    print("SELFTEST:", "ЗЕЛЁНЫЙ" if ok else "КРАСНЫЙ")
    return 0 if ok else 1


# ─────────────────────────────── main ──────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(prog="bxad")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    c = sub.add_parser("crawl")
    c.add_argument("--fixtures")
    c.add_argument("--limit", type=int, default=0)
    i = sub.add_parser("ios27")
    i.add_argument("--issue-on-detect", action="store_true")
    ln = sub.add_parser("lint")
    ln.add_argument("--adapter", required=True)
    ln.add_argument("--mode", choices=["strict", "report"], default="report")
    ln.add_argument("--out")
    ln.add_argument("--ratchet", help="файл базы долга: рост = красный, улучшение ужимает базу")
    ln.add_argument("--project-root", default="", help="корень кода проекта (или переменная PROJECT_ROOT)")
    sub.add_parser("digest")
    sub.add_parser("verify")
    sub.add_parser("study")
    sub.add_parser("weblab")
    sub.add_parser("consult")
    at = sub.add_parser("atlas")
    at.add_argument("--budget", type=int, default=700)
    kt = sub.add_parser("kit")
    kt.add_argument("--force", action="store_true")
    pr = sub.add_parser("probe")
    pr.add_argument("--fixtures")
    at = sub.add_parser("attach")
    at.add_argument("--project", required=True)
    at.add_argument("--report-glob", action="append", default=[])
    at.add_argument("--strict-glob", action="append", default=[])
    at.add_argument("--globs", default="", help="CSV-глобы (короткая запись --report-glob)")
    at.add_argument("--repo", default="", help="owner/name репозитория проекта")
    at.add_argument("--prod", default="", help="корень прода проекта")
    at.add_argument("--deploy-workflow", default="", help="имя воркфлоу деплоя проекта")
    sub.add_parser("projects")
    sub.add_parser("selftest")
    a = ap.parse_args()

    if a.cmd == "status":
        return cmd_status(ROOT)
    if a.cmd == "crawl":
        r = crawler.crawl(ROOT, fixtures=Path(a.fixtures) if a.fixtures else None, limit=a.limit)
        print(f"обход: {r['total']} источников · изменилось {len(r['changed'])} · без изменений {r['unchanged']} · ошибок {len(r['errors'])}")
        for sid in r["changed"]:
            print(f"  Δ {sid}")
        for sid, e in r["errors"]:
            print(f"  ! {sid}: {e}")
        return 0
    if a.cmd == "ios27":
        return cmd_ios27(ROOT, a.issue_on_detect)
    if a.cmd == "lint":
        pr = a.project_root or os.environ.get("PROJECT_ROOT", "")
        proot = Path(pr).resolve() if pr else ROOT.parent
        rc = lint_mod.main(ROOT, a.adapter, a.mode, a.out, proot)
        if a.ratchet:
            adapter = json.loads((ROOT / "adapters" / f"{a.adapter}.json").read_text(encoding="utf-8"))
            tokens = json.loads((ROOT / "registry" / "standards" / "tokens.json").read_text(encoding="utf-8"))
            res = lint_mod.run(ROOT, adapter, tokens, a.mode, proot)
            rc = max(rc, apply_ratchet(ROOT, a.adapter, res, Path(a.ratchet)))
        return rc
    if a.cmd == "digest":
        r = digest_mod.build(ROOT)
        print(f"знание: источников {r['sources']} · обновлено выжимок {len(r['changed'])}")
        return 0
    if a.cmd == "verify":
        r = verify_mod.run(ROOT)
        print(f"сверка: строк {r['rows']} · подтверждено знанием {r['confirmed']} · расхождений {r['bad']}")
        return 1 if r["bad"] else 0
    if a.cmd == "study":
        r = study_mod.run(ROOT)
        print(f"изученность: статей {r['articles']} · замером {r['measured']} · знанием {r['known']} "
              f"(положений {r['knowledge']}) · 🕳 {r['holes']} · не изучено {len(r['bad'])}")
        return 1 if r["bad"] else 0
    if a.cmd == "weblab":
        r = weblab_mod.run(ROOT)
        print(f"веб-атлас: страниц {r['pages']} · видов секций {r['sections_kinds']} · новых типографических законов {r['typo_laws_new']}")
        return 0
    if a.cmd == "consult":
        r = consult_mod.run(ROOT)
        print(f"семёрка: страниц {r['pages']} · новых положений {r['laws_new']} · рамок {r['frames']}")
        return 0
    if a.cmd == "atlas":
        r = atlas_mod.step(ROOT, budget=a.budget)
        print(f"атлас: пройдено {r['walked']} · очередь {r['frontier']} · всего {r['visited_total']} · "
              f"добыто {r['mined']} · изменилось {r['changed']} · библиотека {r['library']['total']} законов / {r['library']['frameworks']} фреймворков")
        return 0
    if a.cmd == "kit":
        r = figkit_mod.run_sketch_arm(ROOT, force=a.force)
        print("кит:", r["status"])
        for k in r.get("kits", []):
            print(f"  {k['kit']}: цветов {k['colors']} · текст-стилей {k['text_styles']} · радиусов {k['radii']} · символов {k['symbols']}")
        f = figkit_mod.run_figma_arm(ROOT)
        print("figma-рука:", f["status"])
        return 0
    if a.cmd == "probe":
        r = crawler.probe(ROOT, fixtures=Path(a.fixtures) if a.fixtures else None)
        print(f"пробы iOS 27: проверено {r['checked']} · завербовано {len(r['enrolled'])}"
              + (": " + ", ".join(r["enrolled"]) if r["enrolled"] else ""))
        return 0
    if a.cmd == "attach":
        gl = list(a.report_glob) + [g.strip() for g in a.globs.split(",") if g.strip()]
        return cmd_attach(ROOT, a.project, gl or ["src/**/*.css"], a.strict_glob or [],
                          repo=a.repo, prod=a.prod, deploy_workflow=a.deploy_workflow)
    if a.cmd == "projects":
        import projects as projects_mod
        ads, en = projects_mod.all_adapters(ROOT), projects_mod.enabled(ROOT)
        print(f"паспортов {len(ads)} · обслуживается {len(en)} · по умолчанию {projects_mod.default_name(ROOT)}")
        for k, v in ads.items():
            mark = "·" if k in en else "○"
            print(f"  {mark} {k}: repo={v.get('repo') or '—'} prod={v.get('prod') or '—'} "
                  f"globs={len((v.get('report') or {}).get('globs', []))} "
                  f"strict={len((v.get('strict') or {}).get('rules', []))}")
        print("страниц живого взгляда:", len(projects_mod.live_pages(ROOT)))
        return 0
    if a.cmd == "selftest":
        return cmd_selftest(ROOT)
    return 2


if __name__ == "__main__":
    sys.exit(main())
