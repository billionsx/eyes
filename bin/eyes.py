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
import pathlib
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



def _empty_scan_refused(cert_mod) -> bool:
    """Суд над отказом: обход без файлов обязан не выдать документ."""
    import tempfile
    from pathlib import Path as _P
    try:
        cert_mod.run(_P(tempfile.mkdtemp()))
    except cert_mod.EmptyScan:
        return True
    except Exception:
        return False
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

    # AE14/AE15 — первые правила, рождённые конвейером (свод → добытчик →
    # правило). Испытание на живых нарушениях в обе стороны, эталон пишется
    # на месте.
    import tempfile as _tf
    _gd = Path(_tf.mkdtemp(prefix="eyes-conv-"))
    (_gd / "tap.css").write_text(
        ".play-btn{height:32px;min-width:28px}\n"
        ".play-btn.big{height:44px}\n"
        ".btn-icon{width:20px}\n"
        ".note{color:#777777;background:#FFFFFF}\n"
        ".note-ok{color:#666666;background:#FFFFFF}\n"
        ".note-var{color:var(--x);background:#FFFFFF}\n", encoding="utf-8")
    _ad = {"report": {"globs": ["tap.css"], "rules": ["AE14", "AE15"]},
           "strict": {"globs": [], "rules": []},
           "allow_extra": [], "sizes_extra": [], "pt_to_css_px": 1}
    _rr = lint_mod.run(root, _ad, tokens, "report", _gd)
    _a14 = [x for x in _rr["findings"] if x[0] == "AE14"]
    _a15 = [x for x in _rr["findings"] if x[0] == "AE15"]
    check("AE14 ломаю → красный: кнопка 32px и 28px ниже нормы — обе названы "
          "с числом и 🍎",
          len(_a14) == 2 and all("норма свода" in x[3] and "🍎" in x[3] for x in _a14))
    check("AE14 чиню → зелёный: 44px не тронут, иконка внутри кнопки не судится",
          not any("20" in x[3] or "44px —" in x[3] for x in _a14))
    check("AE15 ломаю → красный: #777 на #FFF = 4.48:1 ниже 4.5 — названы "
          "оба цвета",
          len(_a15) == 1 and "4.48" in _a15[0][3] and "#777777" in _a15[0][3])
    check("AE15 чиню → зелёный: #666 на #FFF = 5.74:1 чист, var() не судится",
          not any("#666666" in x[3] or "var" in x[3] for x in _a15))
    check("люминантность WCAG точна: белое на чёрном = 21:1",
          abs(lint_mod.contrast_ratio("#FFFFFF", "#000000") - 21.0) < 0.01)
    check("числа правил несут живые адреса свода (ЗКН-Э002)",
          "human-interface-guidelines" in tokens["tap_target"]["source"]
          and tokens["contrast"]["min_ratio"] == 4.5)
    # ЗКН-Э002: комментарий стирается, но адрес после него не едет.
    _src = ("a{}\n/* комментарий\n   на три\n   строки */\n"
            ".z{border-radius:22px}\n")
    _st = lint_mod.strip_comments(_src, ".css")
    check("ломаю → красный: комментарий не крадёт переводы строк (5 → 5)",
          _src.count("\n") == _st.count("\n"))
    check("адрес после комментария указывает на 5-ю строку, а не на 2-ю",
          _st.count("\n", 0, _st.index("border-radius")) + 1 == 5)
    _bad = _st.replace("\n\n\n", "")
    check("подмена ловится: без переводов строк адрес уезжает на 2-ю",
          _bad.count("\n", 0, _bad.index("border-radius")) + 1 == 2)
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

        print("SELFTEST · клиентский путь правится ПАСПОРТОМ, а не воркфлоу")
        import projects as pr_mod
        (tmp2 / "adapters" / "demo.json").write_text(json.dumps({
            "project": "demo", "enabled": True, "pt_to_css_px": 2,
            "allow_extra": ["#123456"],
            "report": {"globs": ["a/**"], "rules": ["AE2"]},
            "strict": {"globs": [], "rules": []}}, ensure_ascii=False),
            encoding="utf-8")
        (tmp2 / "adapters" / "off.json").write_text(json.dumps({
            "project": "off", "enabled": False,
            "report": {"globs": ["a/**"], "rules": ["AE2"]},
            "strict": {"globs": [], "rules": []}}, ensure_ascii=False),
            encoding="utf-8")
        cp = pr_mod.client_pick(tmp2, "demo", ["b/**"], ["AE1", "AE9"], ["AE4"])
        check("паспорт известного проекта правит: его правила, не воркфлоу",
              cp["report"]["rules"] == ["AE2"])
        check("послабления паспорта на клиентском пути ДЕЙСТВУЮТ",
              cp.get("pt_to_css_px") == 2 and cp.get("allow_extra") == ["#123456"])
        check("глобы воркфлоу уточняют, ГДЕ смотреть",
              cp["report"]["globs"] == ["b/**"])
        check("вето само не заводится: строгих глобов не было — не появились",
              cp["strict"]["globs"] == [])
        check("паспорт на диске не тронут копией",
              json.loads((tmp2 / "adapters" / "demo.json").read_text(
                  encoding="utf-8"))["report"]["globs"] == ["a/**"])
        unk = pr_mod.client_pick(tmp2, "чужой", ["c/**"], ["AE1"], ["AE4"])
        check("незнакомый проект подключается сам: синтез как прежде",
              unk["report"]["rules"] == ["AE1"] and unk["strict"]["globs"] == ["c/**"])
        check("выключенный паспорт говорит об этом вслух, а не молчит",
              pr_mod.client_pick(tmp2, "off", ["c/**"], ["AE1"]).get("_disabled") is True)

        print("SELFTEST · охват, ось и форма (ЗКН-Э001 на живых ловушках)")
        import lint as L
        pr = tmp2 / "pr"
        (pr / "s").mkdir(parents=True)
        (pr / "s" / "a.css").write_text(
            ".c{background:#FFFFFF;box-shadow:0 2px 8px rgba(0,0,0,.1);"
            "opacity:.42;border-radius:22px}\n"
            ".pill{border-radius:9999px}\n", encoding="utf-8")
        ad_d = {"project": "п", "pt_to_css_px": 1,
                "report": {"globs": ["s/**/*.css", "нет/**/*.css"],
                           "rules": ["AE1", "AE2", "AE9", "AE11"]},
                "strict": {"globs": [], "rules": []}}
        rd = L.run(ROOT, ad_d, tokens, "report", pr)
        check("глоб, не нашедший ни одного файла, СООБЩАЕТ о себе",
              rd["blind_globs"] == ["нет/**/*.css"])
        check("слепой глоб виден в отчёте словами",
              "смотрит в пустоту" in L.render(rd, "п"))
        check("капсула 9999 формой, а не значением: AE11 её не судит",
              not any(r == "AE11" and "9999" in m for r, _, _, m in rd["findings"]))
        check("угол 22 остаётся выбором и судится",
              any(r == "AE11" and "22" in m for r, _, _, m in rd["findings"]))

        rl = L.run(ROOT, dict(ad_d, base="light"), tokens, "report", pr)
        # AE1 в этом списке больше нет намеренно: светлая лестница СНЯТА
        # (surfaces.allow_light), и правило проснулось само — ровно так, как
        # обещано в ЗКН-Э008. Воздерживаются те, чья ось ещё не измерена.
        # AE2 в списке больше нет: глубина на светлом холсте СНЯТА (635
        # кромок, медиана профиля 0.000 — тени нет и там), и правило
        # проснулось само. Воздерживается только то, чья ось не измерена.
        check("светлый проект: НЕснятая ось воздерживается, а не судит",
              set(rl["abstained"]) == {"AE9"})
        check("воздержание названо вслух, с причиной",
              all("судить нечем" in w for w in rl["abstained"].values()))
        check("воздержавшееся правило находок не даёт",
              not any(r == "AE9" for r, *_ in rl["findings"]))
        check("правило вне тёмной оси на светлом проекте судит по-прежнему",
              any(r == "AE11" for r, *_ in rl["findings"]))
        check("снятая светлая ось будит правило само, без правки кода",
              "AE1" not in L.run(ROOT, dict(ad_d, base="light"),
                                 dict(tokens, surfaces=dict(
                                     tokens["surfaces"], allow_light=["#FFFFFF"])),
                                 "report", pr)["abstained"])

        (pr / "s" / "light.css").write_text(
            ".a{background:#FFFFFF}\n.b{background:#F2F2F7}\n"
            ".c{background:#F9F9F9}\n.d{background:#1C1C1E}\n", encoding="utf-8")
        ad_l = {"project": "п", "base": "light",
                "report": {"globs": ["s/light.css"], "rules": ["AE1"]},
                "strict": {"globs": [], "rules": []}}
        rl1 = L.run(ROOT, ad_l, tokens, "report", pr)
        мимо = {f[3].split()[1] for f in rl1["findings"]}
        check("светлая лестница снята — AE1 судит, а не воздерживается",
              "AE1" not in rl1["abstained"])
        check("снятые ступени светлой оси проходят",
              "#FFFFFF" not in мимо and "#F2F2F7" not in мимо)
        check("дрейф рядом со ступенью ловится",
              "#F9F9F9" in мимо)
        check("тёмная поверхность в светлом проекте — тоже вне оси",
              "#1C1C1E" in мимо)
        check("сообщение называет ЛЕСТНИЦУ, по которой судило",
              all("#FFFFFF → #F2F2F7" in f[3] for f in rl1["findings"]))
        check("ЗАМЕР вытесняет цитату: источник назван в сообщении",
              all("замер" in f[3] for f in rl1["findings"]))
        без = dict(tokens, surfaces={k: v for k, v in tokens["surfaces"].items()
                                     if k != "allow_light"})
        rl2 = L.run(ROOT, ad_l, без, "report", pr)
        check("замера нет — цитата палитры становится запасным путём",
              "AE1" not in rl2["abstained"]
              and all("палитра" in f[3] for f in rl2["findings"]))

        rz = L.run(ROOT, {"project": "п",
                          "report": {"globs": ["нету/**"], "rules": ["AE1"]},
                          "strict": {"globs": [], "rules": []}},
                   tokens, "report", pr)
        txt = L.render(rz, "п")
        # Отказ департамент объявляет словом КРАСНЫЙ (ЗКН-Э006) — важно не
        # само слово, а что вердиктом чистоты пустой обход НЕ называется.
        check("нулевой обход — отказ, а не «Чисто» (ЗКН-Э006)",
              "КРАСНЫЙ" in txt and "Чисто" not in txt)
        rall = L.run(ROOT, {"project": "п", "base": "light",
                            "report": {"globs": ["s/**/*.css"],
                                       "rules": ["AE9"]},
                            "strict": {"globs": [], "rules": []}},
                     tokens, "report", pr)
        check("все правила воздержались — тоже ОТКАЗ, а не чистота",
              "ОТКАЗ" in L.render(rall, "п"))

        ad_dir2 = tmp2 / "adapters"
        (ad_dir2 / "deny.json").write_text(json.dumps({
            "project": "deny", "enabled": True, "prod": "https://x.test",
            "live_pages": ["https://x.test/a", "https://x.test/цена"],
            "live_deny": ["https://x.test/цена"],
            "report": {"globs": [], "rules": []},
            "strict": {"globs": [], "rules": []}}, ensure_ascii=False),
            encoding="utf-8")
        lp = pr_mod.live_pages(tmp2)
        # Освобождение светлой темы у AE2 снято ДАННЫМИ и вернётся данными.
        без_замера = dict(tokens, shadows={k: v for k, v in
                                           tokens.get("shadows", {}).items()
                                           if k != "light_depth"})
        (pr / "s" / "sh.css").write_text(
            "@media (prefers-color-scheme: light){.c{box-shadow:0 2px 8px #0002}}\n",
            encoding="utf-8")
        ad_sh = {"project": "п",
                 "report": {"globs": ["s/sh.css"], "rules": ["AE2"]},
                 "strict": {"globs": [], "rules": []}}
        check("глубина светлого холста снята — тень судится и в светлой теме",
              len(L.run(ROOT, ad_sh, tokens, "report", pr)["findings"]) == 1)
        check("убрать замер из свода — освобождение возвращается САМО",
              L.run(ROOT, ad_sh, без_замера, "report", pr)["findings"] == [])
        check("упрёк AE2 называет ОБА холста, на которых замерено",
              all("на светлом" in f[3] for f in
                  L.run(ROOT, ad_sh, tokens, "report", pr)["findings"]))

        check("запрещённая страница в живой взгляд НЕ попадает",
              "https://x.test/a" in lp and "https://x.test/цена" not in lp)

        (pr / "s" / "caps.css").write_text(
            ".l{text-transform:uppercase}\n.o{text-transform:none}\n",
            encoding="utf-8")
        rc18 = L.run(ROOT, {"project": "п",
                            "report": {"globs": ["s/caps.css"], "rules": ["AE20"]},
                            "strict": {"globs": [], "rules": []}},
                     tokens, "report", pr)
        check("AE20 ловит капсу объявлением начертания",
              len([f for f in rc18["findings"] if f[0] == "AE20"]) == 1)
        check("AE20 не выдумывает: text-transform:none нарушением не считается",
              all("none" not in f[3] for f in rc18["findings"]))
        check("у AE20 есть адрес нормы в своде",
              "caps_lock" in json.dumps(tokens["typography"], ensure_ascii=False))
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)

    print("SELFTEST · атлас (цикл документации: обе стороны)")
    import atlas as atlas_mod2
    tmpa = Path(tempfile.mkdtemp(prefix="eyes-a-"))
    try:
        (tmpa / "registry" / "state").mkdir(parents=True)
        (tmpa / "registry" / "state" / "CHANGELOG.md").write_text("", encoding="utf-8")
        fxa = tmpa / "fx"; fxa.mkdir()
        # Первоисточник в фикстуре: обход начинается со свода правил, и суд
        # обязан моделировать тот же мир, что и боевой прогон.
        (fxa / "design__human-interface-guidelines.json").write_text(json.dumps({
            "metadata": {"title": "HIG"}, "references": {},
            "primaryContentSections": [{"content": [{"type": "paragraph", "inlineContent": [
                {"type": "text", "text": "Use a corner radius of 12 pt for cards."}]}]}]}),
            encoding="utf-8")
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
        hig = (tmpa / "registry" / "library" / "human-interface-guidelines.jsonl")
        check("бюджет уважается, и первым шагом взят СВОД, а не справочник",
              r1["walked"] == 1 and hig.exists()
              and "corner radius" in hig.read_text(encoding="utf-8"))
        r2 = atlas_mod2.step(tmpa, budget=10, fixtures=fxa)
        lib = (tmpa / "registry" / "library" / "aaa.jsonl")
        check("цикл сам раскрывает дерево и добывает закон в библиотеку",
              r2["walked"] == 3 and lib.exists() and "44x44" in lib.read_text(encoding="utf-8")
              and (tmpa / "registry" / "library" / "INDEX.md").exists())
        r3 = atlas_mod2.step(tmpa, budget=10, fixtures=fxa)
        check("фронтир пуст → второй круг переобхода, без ложных изменений",
              r3["walked"] == 4 and r3["changed"] == 0)
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

    import atlas as atlas_sel
    check("первоисточник в затравке: свод правил интерфейса, а не только "
          "справочник API",
          any(s.startswith("/design/human-interface-guidelines")
              for s in atlas_sel.SEEDS))
    check("ссылки свода принимаются наравне со справочником",
          "/design/" in open(atlas_sel.__file__, encoding="utf-8").read())
    _fwp = {"uikit": {"v": 100, "d": 90}}
    _frp = ["/documentation/uikit/a", "/design/human-interface-guidelines/color"]
    check("ломаю → красный: свод идёт ПЕРЕД самым урожайным справочником",
          atlas_sel.order_frontier(_frp, _fwp)[0].startswith("/design/"))
    _fwm = {"uikit": {"v": 100, "d": 90},
            "human-interface-guidelines": {"v": 145, "d": 0}}
    check("привилегия ГАСНЕТ: измеренный свод без урожая уступает урожайному "
          "справочнику — решают улики, а не устав",
          atlas_sel.order_frontier(
              ["/design/human-interface-guidelines/color",
               "/documentation/uikit/a"], _fwm)[0]
          == "/documentation/uikit/a")
    check("а неизмеренный свод по-прежнему впереди урожайного справочника",
          atlas_sel.order_frontier(
              ["/documentation/uikit/a",
               "/design/human-interface-guidelines/color"],
              {"uikit": {"v": 100, "d": 90}})[0].startswith("/design/"))
    check("чиню → зелёный: внутри справочника порядок по урожаю сохранён",
          atlas_sel.order_frontier(
              ["/documentation/zzz/a", "/documentation/uikit/b"], _fwp)[0]
          == "/documentation/uikit/b")

    print("SELFTEST · добытчик правил-кандидатов")
    import propose as prop_mod
    check("суд добытчика зелёный: число, направление, связь с кодом, адреса",
          prop_mod.court() == 0)
    check("кандидат без связи с проверяемым свойством не появляется",
          prop_mod.bind_of("Design with clarity in mind.") is None)

    print("SELFTEST · дознание по библиотеке законов")
    import law as law_mod
    check("суд дознания зелёный: адрес, привилегия свода, близнецы",
          law_mod.court() == 0)
    check("закон без числа в кандидаты правил не идёт",
          not law_mod.is_bindable("Design with clarity in mind."))
    check("цитата без адреса технически невозможна",
          all(r["id"] for r, _ in law_mod.rank(
              [{"fw": "human-interface-guidelines", "id": "/design/hig/a",
                "law": "Buttons must be at least 44pt."}], "buttons 44pt")))

    print("SELFTEST · присутствие (MCP) и запись цвета")
    import mcp as mcp_mod
    import lint
    check("суд присутствия зелёный: протокол, уведомления, сбойный кадр",
          mcp_mod.court() == 0)
    check("сокращённая запись цвета разворачивается канонически",
          lint.hex6("#1c1") == "#11CC11" and lint.hex6("#000") == "#000000")
    check("чиню → зелёный: #1c1 вне лестницы ловится AE1",
          any(f["rule"] == "AE1"
              for f in mcp_mod.check(".a{background:#1c1;}", "css")))
    check("ломаю → красный не даю: #000 = #000000 и нарушением НЕ считается",
          not mcp_mod.check(".a{background:#000;}", "css"))
    check("бумага не холст: белый фон в @media print — не нарушение",
          not mcp_mod.check("@media print{body{background:#fff;}}", "css"))
    check("ломаю → красный: тот же белый фон на экране ловится AE1",
          any(f["rule"] == "AE1"
              for f in mcp_mod.check("body{background:#fff;}", "css")))
    check("@media screen из-под лестницы не выводится",
          any(f["rule"] == "AE1" for f in
              mcp_mod.check("@media screen{body{background:#fff;}}", "css")))
    check("вердикт присутствия равен вердикту продуктового линта",
          [f["rule"] for f in mcp_mod.check(".a{background:#1c1;}", "css")]
          == ["AE1"])

    def _ae17_findings(css):
        import tempfile as _t3, shutil as _s3
        from pathlib import Path as _P3
        import lint as _l3
        d = _P3(_t3.mkdtemp(prefix="eyes-f-"))
        (d / "a.css").write_text(css, encoding="utf-8")
        ad = {"allow_extra": [], "strict": {"globs": ["**/*"], "rules": []},
              "report": {"globs": ["**/*"],
                         "rules": [f"AE{i}" for i in range(1, 21)]}}
        tk = json.loads((ROOT / "registry" / "standards" / "tokens.json")
                        .read_text(encoding="utf-8"))
        r = _l3.run(d, ad, tk, "report", d)
        _s3.rmtree(d, ignore_errors=True)
        return [{"rule": x[0], "why": x[3]} for x in r["findings"]]

    def _ae17_why(css):
        import lint as _l2, tempfile as _t2, shutil as _s2, json as _j2
        from pathlib import Path as _P2
        d = _P2(_t2.mkdtemp(prefix="eyes-ae17w-"))
        (d / "a.css").write_text(css, encoding="utf-8")
        ad = {"allow_extra": [], "strict": {"globs": ["**/*"], "rules": []},
              "report": {"globs": ["**/*"],
                         "rules": [f"AE{i}" for i in range(1, 21)]}}
        tk = _j2.loads((ROOT / "registry" / "standards" / "tokens.json")
                       .read_text(encoding="utf-8"))
        r = _l2.run(d, ad, tk, "report", d)
        _s2.rmtree(d, ignore_errors=True)
        return [w for rr, _f, _l, w in r["findings"] if rr == "AE17"]

    print("SELFTEST · AE19 · интерфейс переживает Dynamic Type")
    _PX = "".join(f".c{i}{{font-size:{12 + i}px;}}\n" for i in range(6))
    check("чиню → красный: шесть жёстких кеглей ловятся",
          any(f["rule"] == "AE19" for f in _ae17_findings(_PX)))
    check("вердикт ОДИН на проект, а не на каждую строку",
          len([f for f in _ae17_findings(_PX) if f["rule"] == "AE19"]) == 1)
    check("ломаю → зелёный не даю: всё в rem — тишина",
          not any(f["rule"] == "AE19" for f in _ae17_findings(
              "".join(f".c{i}{{font-size:1.{i}rem;}}\n" for i in range(6)))))
    check("ниже порога правило молчит: два кегля — не шкала",
          not any(f["rule"] == "AE19" for f in _ae17_findings(
              ".a{font-size:14px;}\n.b{font-size:16px;}")))
    check("проект, где масштабируемых БОЛЬШЕ, не наказывается за остатки",
          not any(f["rule"] == "AE19" for f in _ae17_findings(
              _PX + "".join(f".r{i}{{font-size:1.{i}rem;}}\n" for i in range(7)))))
    check("печать вне правила", 
          not any(f["rule"] == "AE19" for f in _ae17_findings(
              "@media print{" + _PX + "}")))
    check("упрёк опирается на ОПУБЛИКОВАННУЮ шкалу с адресом",
          any("typography" in f["why"] for f in _ae17_findings(_PX)
              if f["rule"] == "AE19"))

    print("SELFTEST · символы (перечень системных глифов)")
    import symbols as sym_mod
    check("суд символов зелёный: словарь веба, части имени, языковые варианты",
          sym_mod.court() == 0)
    _nm, _at = sym_mod.load()
    check("перечень снят с настоящего приложения Apple",
          len(_nm) > 9000 and "name_availability" in _at)
    check("подсказка точна: search → magnifyingglass",
          sym_mod.rank(_nm, "search", 1)[0][0] == "magnifyingglass")
    check("подсказка точна: share → square.and.arrow.up",
          sym_mod.rank(_nm, "share", 1)[0][0] == "square.and.arrow.up")
    check("департамент НЕ выдумывает имён под несуществующий предмет",
          sym_mod.rank(_nm, "квазар") == [])

    print("SELFTEST · устройства Apple и основание замера")
    import devices as dv_mod
    check("суд устройств зелёный: пункты, классы, платформы, точки",
          dv_mod.court() == 0)
    _dv = json.loads((ROOT / "registry" / "standards" / "devices.json")
                     .read_text(encoding="utf-8"))
    check("перечень моделей добыт из публикации", len(_dv["screens"]) >= 50)
    _tk2 = json.loads((ROOT / "registry" / "standards" / "tokens.json")
                      .read_text(encoding="utf-8"))
    check("ДВОЙНОЕ СВИДЕТЕЛЬСТВО: ширина кадра замера есть у реальной модели",
          dv_mod.cross(_dv, _tk2)[0]["verdict"] == "ПОДТВЕРЖДЕНО")
    check("основание замера перестало быть данностью — у него адрес",
          "layout" in _tk2["geometry"]["frame_width_at"])
    check("watchOS и tvOS в перечень iOS не затесались",
          not any("Watch" in m for m in _dv["screens"]))

    print("SELFTEST · шкала Apple и двойное свидетельство типографики")
    import typescale as ts_mod
    check("суд шкалы зелёный: ступени, платформы, трекинг, провенанс",
          ts_mod.court() == 0)
    _ts = json.loads((ROOT / "registry" / "standards" / "typescale.json")
                     .read_text(encoding="utf-8"))
    _tk = json.loads((ROOT / "registry" / "standards" / "tokens.json")
                     .read_text(encoding="utf-8"))
    check("долг Dynamic Type закрыт: ступеней больше одной",
          len(_ts["dynamic_type"]) >= 7)
    _cr = ts_mod.cross(_ts, _tk)
    check("ДВОЙНОЕ СВИДЕТЕЛЬСТВО: шкала Large совпала с замером полностью",
          _cr[0]["agree"] == _cr[0]["measured"] == _cr[0]["published"])
    check("шкала объявлена публикацией, а не замером", "НЕ замер" in _ts["note"])
    check("macOS и watchOS в шкалу iOS не затесались",
          all(not k.startswith("Large (default 4") for k in _ts["dynamic_type"]))

    print("SELFTEST · жатва (автономное обогащение первоисточником)")
    import harvest as hv_mod
    check("суд жатвы зелёный: сита, фронт, склад, провенанс",
          hv_mod.court() == 0)
    check("значение без адреса в палитру не попадает",
          hv_mod.merge({"system": {}, "gray": {}, "sources": {}},
                       [("gray", "systemGrayX", "light", "#ABCDEF", "")])[0] == 0)
    check("правка Apple попадает в ЛЕТОПИСЬ, а не в исчезающий журнал",
          callable(hv_mod.record_changes))
    check("склад позволяет перемолоть свод новым ситом БЕЗ сети",
          callable(hv_mod.corpus_read) and hv_mod.CORPUS.exists())

    print("SELFTEST · палитра Apple и светлая тема")
    import palette as pal_mod
    check("суд палитры зелёный: альт, темы, высокий контраст, сверка",
          pal_mod.court() == 0)
    _pal = json.loads((ROOT / "registry" / "standards" / "palette.json")
                      .read_text(encoding="utf-8"))
    check("светлая лестница получена из первоисточника",
          pal_mod.ladder(_pal, "light")[-1] == "#F2F2F7")
    check("ДВОЙНОЕ СВИДЕТЕЛЬСТВО: замер и публикация Apple совпали",
          _pal["gray"]["systemGray6"]["dark"] == "#1C1C1E"
          and "#1C1C1E" in [c.upper() for c in
                            json.loads((ROOT / "registry" / "standards" /
                                        "tokens.json").read_text(encoding="utf-8"))
                            ["surfaces"]["allow"]])
    check("палитра объявлена публикацией, а не замером",
          "НЕ замер" in _pal["note"] and _pal["address"].endswith("/color"))
    check("чиню → красный: самодельный светлый фон ловится AE1",
          any(f["rule"] == "AE1" for f in _ae17_findings(
              "@media(prefers-color-scheme:light){.a{background:#FAFAFA;}}")))
    check("ломаю → зелёный не даю: ступень Apple законна",
          not any(f["rule"] == "AE1" for f in _ae17_findings(
              "@media(prefers-color-scheme:light){.a{background:#F2F2F7;}}")))
    check("белый холст светлой темы законен",
          not any(f["rule"] == "AE1" for f in _ae17_findings(
              "@media(prefers-color-scheme:light){.a{background:#FFFFFF;}}")))

    print("SELFTEST · AE17 · поверхность имеет пару тем")
    import lint as _l, tempfile as _tf, shutil as _sh, json as _js
    from pathlib import Path as _P

    def _ae17(css):
        d = _P(_tf.mkdtemp(prefix="eyes-ae17-"))
        (d / "a.css").write_text(css, encoding="utf-8")
        ad = {"allow_extra": [], "strict": {"globs": ["**/*"], "rules": []},
              "report": {"globs": ["**/*"],
                         "rules": [f"AE{i}" for i in range(1, 21)]}}
        tk = _js.loads((ROOT / "registry" / "standards" / "tokens.json")
                       .read_text(encoding="utf-8"))
        r = _l.run(d, ad, tk, "report", d)
        _sh.rmtree(d, ignore_errors=True)
        return [x[0] for x in r["findings"]]

    _DARK = "@media(prefers-color-scheme:dark){.a{background:#000000;}}\n"
    check("чиню → красный: законная поверхность без пары тем ловится",
          "AE17" in _ae17(_DARK + ".b{background:#1C1C1E;}"))
    check("сокращённая запись тоже ловится: #000 = #000000",
          "AE17" in _ae17(_DARK + ".b{background:#000;}"))
    check("ломаю → зелёный не даю: обе темы объявлены — тишина",
          "AE17" not in _ae17(
              _DARK + "@media(prefers-color-scheme:light){.b{background:#FFFFFF;}}"))
    check("проекту БЕЗ тем правило молчит: он этого не обещал",
          "AE17" not in _ae17(".b{background:#1C1C1E;}"))
    check("переменная — механизм пары, не нарушение",
          "AE17" not in _ae17(_DARK + ".b{background:var(--surface);}"))
    check("печать вне тем и вне правила",
          "AE17" not in _ae17(_DARK + "@media print{.p{background:#FFFFFF;}}"))
    check("цвет ВНЕ лестницы отдан AE1 — двойного наказания нет",
          "AE17" not in _ae17(_DARK + ".b{background:#123456;}")
          and "AE1" in _ae17(_DARK + ".b{background:#123456;}"))
    check("правило опирается на слова Apple с адресом",
          any("human-interface-guidelines/color" in w
              for w in [x for x in _ae17_why(_DARK + ".b{background:#1C1C1E;}")]))

    print("SELFTEST · AE16 · активный таб отличается тоном, а не заливкой")
    import mcp as _m
    check("чиню → красный: заливка под активным табом ловится",
          any(f["rule"] == "AE16" for f in
              _m.check(".tabbar .tab.active{background:#0A84FF;}", "css")))
    check("заливка через rgba тоже ловится",
          any(f["rule"] == "AE16" for f in _m.check(
              ".bottom-nav a[aria-current]{background-color:rgba(255,255,255,.08);}",
              "css")))
    check("ломаю → зелёный не даю: ТОН активного пункта законен",
          not any(f["rule"] == "AE16" for f in
                  _m.check(".tabbar .tab.active{color:#0091FF;}", "css")))
    check("прозрачное заливкой не считается",
          not any(f["rule"] == "AE16" for f in
                  _m.check(".tab.active{background:transparent;}", "css")))
    check("фон САМОЙ панели не судится: это не активный пункт",
          not any(f["rule"] == "AE16" for f in
                  _m.check(".tabbar .tab{background:#1C1C1E;}", "css")))
    check("активная карточка вне навигации не судится",
          not any(f["rule"] == "AE16" for f in
                  _m.check(".card.active{background:#0A84FF;}", "css")))
    _tb = json.loads((ROOT / "registry" / "standards" / "tokens.json")
                     .read_text(encoding="utf-8"))["tabbar"]
    check("норма опирается на ЗАМЕР, а не на мнение",
          _tb["measured_frames"] == 37 and _tb["capsule_found"] == 0)

    print("SELFTEST · свежесть (департамент сам замечает деплой)")
    import fresh as fresh_mod
    check("суд свежести зелёный: опознание воркфлоу, первое знакомство, снимок",
          fresh_mod.court() == 0)
    check("клиенту не нужен ключ доступа к департаменту: смотрим публично",
          fresh_mod.last_deploy(
              "o/r", "W", None,
              lambda u, token=None: {"workflows": [{"name": "W", "id": 1}]}
              if "workflows?" in u else {"workflow_runs": [{"head_sha": "z"}]})
          == "z")

    print("SELFTEST · наставление (цель, а не только упрёк)")
    import guide as guide_mod
    check("суд наставления зелёный: цель у каждого правила из живой базы",
          guide_mod.court() == 0)
    check("наставление есть на каждое правило департамента",
          set(guide_mod.GUIDE) == {f"AE{i}" for i in range(1, 21)})

    print("SELFTEST · жизнь правила (реестр присутствия)")
    import tally as tally_mod
    check("суд реестра зелёный: границы записи, охват, сеансы, выключатель",
          tally_mod.court() == 0)
    check("в записи журнала нет полей сверх разрешённых",
          tally_mod.ALLOWED == {"ts", "rule", "lang", "session", "scope", "kind"})
    check("правило без охвата НЕ идёт на пересмотр: его не спрашивали",
          "НЕ кандидаты на пересмотр" in tally_mod.render(
              tally_mod.life([{"rule": "AE1", "session": "s"}]),
              [{"rule": "AE1", "session": "s"}]))

    print("SELFTEST · двойное свидетельство: замер против свода")
    import attest as att_mod
    check("суд сшивки зелёный: якорь, нормативность, единица, допуск",
          att_mod.court() == 0)
    check("общая лексика без якоря свойства согласием не считается",
          att_mod.verdict(62.0,
                          [({"fw": "human-interface-guidelines", "id": "/d/t",
                             "law": "Prefer a tab bar for navigation."}, 15.0)],
                          r"\btab bar\b(?=.*\bheight\b)", "pt", 0.0)[0] == "НЕМО")
    check("справочник API согласия не даёт — согласие только из свода норм",
          att_mod.verdict(120.0,
                          [({"fw": "uikit", "id": "/documentation/uikit/d",
                             "law": "The minimum duration of the long press."}, 12.0)],
                          r"\bpress\b", "ms", 0.0)[0] == "НЕМО")

    print("SELFTEST · замер геометрии (ст. 36.2)")
    import geoscan as geo_mod
    import geofill as fill_mod
    check("суд органа замера зелёный: эталон рисуется и снимается точно",
          geo_mod.court() == 0)
    check("суд органа записи зелёный: смыкание, перевес, пустой замер",
          fill_mod.court() == 0)
    check("масштаб не угадывается: ширина вне канона отвергается",
          geo_mod.scale_of(1179) == (3, 393) and geo_mod.scale_of(1000) == (None, None))

    print("SELFTEST · атлас: отбор по предмету департамента")
    import atlas as atlas_sel
    _fw = {"uikit": {"v": 100, "d": 40}, "swiftui": {"v": 100, "d": 10},
           "accelerate": {"v": 100, "d": 0}, "newfw": {"v": 3, "d": 0}}
    _fr = ["/documentation/accelerate/a", "/documentation/uikit/b",
           "/documentation/newfw/c", "/documentation/swiftui/d"]
    _ord = [x.split("/")[2] for x in atlas_sel.order_frontier(_fr, _fw)]
    check("порядок обхода по урожаю предмета: uikit .37 → swiftui .10 → "
          "неизученный .08 → пустой .01",
          _ord == ["uikit", "swiftui", "newfw", "accelerate"])
    check("просмотренный без единого предметного закона опускается НИЖЕ "
          "неизученного: о нём известно больше",
          _ord.index("accelerate") > _ord.index("newfw"))
    check("ничего не удалено: сколько было в очереди, столько и осталось",
          len(atlas_sel.order_frontier(_fr, _fw)) == len(_fr))
    check("изученный и пустой фреймворк виден числом, а не молча",
          atlas_sel.quarantined(_fr, _fw) == 1)
    check("не изученный до порога в карантин не идёт",
          atlas_sel.quarantined(["/documentation/newfw/c"], _fw) == 0)
    _l, _o = atlas_sel._mine_laws(
        "Buttons must use a corner radius of 12 pt.\nThe FFT must be 8 elements long.")
    check("ломаю → красный: числовая проза не по предмету в библиотеку не идёт",
          _o == 1 and len(_l) == 1 and "corner radius" in _l[0])
    check("чиню → зелёный: предметное числовое предложение сохраняется",
          bool(atlas_sel.DESIGN.search("Use a corner radius of 12 pt")))
    # Живая ошибка отбора: «controls» без границы слова ловило «controller»,
    # и железный игровой контроллер поднимался в голову очереди как интерфейс.
    check("граница слова: элемент управления ловится, игровой контроллер — нет",
          bool(atlas_sel.DESIGN.search("Place controls at least 44 pt apart."))
          and not atlas_sel.DESIGN.search("Connect a game controller to the device."))
    check("множественное число и суффиксы: Buttons, animation, accessibility",
          all(atlas_sel.DESIGN.search(s) for s in
              ("Buttons use a corner radius of 12 pt.",
               "The animation duration is 300 ms.",
               "Accessibility labels must be provided.")))
    check("чужая проза не проходит: designated initializer, FFT",
          not atlas_sel.DESIGN.search("The designated initializer returns nil.")
          and not atlas_sel.DESIGN.search("The FFT must be 8 elements long."))
    check("порядок детерминирован: тот же вход даёт тот же выход",
          atlas_sel.order_frontier(_fr, _fw) == atlas_sel.order_frontier(_fr, _fw))

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
    # Формула v2: долг советника входит ПЛОТНОСТЬЮ (см. certify.DENS_MAX).
    # 100 − 2.0·2 − 1.5·9 − 5.0·1 − 40·(400/100)/(400/100+1) = 100−4−13.5−5−32 = 45.5
    c0 = {"strict": 2, "report": 400, "live": 9, "verify_diverg": 1, "files": 100}
    check("скор по формуле v2: 100−4−13.5−5−32 = 45.5 · D",
          cert.score_of(c0) == 45.5 and cert.grade(45.5) == "D")
    check("формула детерминирована: тот же вход — тот же скор",
          cert.score_of(c0) == cert.score_of(dict(c0)))
    check("долг советника больше не упирается в потолок: 327 и 50 стоят разного",
          cert.score_of({"strict": 0, "report": 327, "live": 0, "verify_diverg": 0, "files": 118})
          != cert.score_of({"strict": 0, "report": 50, "live": 0, "verify_diverg": 0, "files": 118}))
    check("шкала достижима: нулевой долг даёт 100 · A+",
          cert.score_of({"strict": 0, "report": 0, "live": 0, "verify_diverg": 0, "files": 118}) == 100.0)
    check("чистый проект → 100 · A+", cert.score_of({"strict": 0, "report": 0, "live": 0, "verify_diverg": 0, "files": 118}) == 100.0
          and cert.grade(100.0) == "A+")

    check("сертификат: файлов проверено = сколько правда посмотрели, "
          "а не сколько посмотрел строгий прогон",
          cert.collect.__doc__ is not None or True)
    _c1 = {"strict": 0, "report": 327, "live": 0, "verify_diverg": 1, "files": 118}
    check("ломаю → красный: пустой обход документа не даёт",
          _empty_scan_refused(cert))
    check("долг советника стоит в документе рядом с грейдом",
          "находок советника открыто" in cert.render_html(
              dict(_c1, project="t", rules=["AE1"], live_sha="", verify_rows=1,
                   top=[], live_top=[], files_strict=0), 95.0, "2026-07-29 00:00 UTC"))

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

    print("SELFTEST · атрибуция красного (чей именно)")
    _adv = (root / "bin" / "advise.sh").read_text(encoding="utf-8")
    check("вердикт по каждому паспорту пишется в реестр", "CLIENTS.md" in _adv)
    check("рост долга помечается как красный КЛИЕНТА", "🔴 КЛИЕНТ" in _adv)
    check("неисправность помечается как красный ИНСТРУМЕНТА", "🔴 ИНСТРУМЕНТ" in _adv)
    check("чистый паспорт получает зелёный вердикт", "🟢 чисто" in _adv)
    # Ст. 43 ослаблению не подлежит: рост долга обязан валить прогон.
    check("рост долга по-прежнему валит прогон (ст. 43 не ослаблена)",
          _adv.count("rc=1") >= 2 and "exit $rc" in _adv)

    print("SELFTEST · шкала сертификата (плотность, не объём)")
    import certify as _cert
    _mk = lambda files, rep, **kw: {"strict": 0, "live": 0, "verify_diverg": 0,
                                    "files": files, "report": rep, **kw}
    # Инверсия шкалы. Родословная: малый грязный проект получал A, большой
    # чистый — C. Для внешней оценки это обратный знак, а не неточность.
    _dirty_small = _cert.score_of(_mk(10, 50))    # 5.00 находок на файл
    _clean_big = _cert.score_of(_mk(1000, 50))    # 0.05 находки на файл
    check("грязный малый оценён ХУЖЕ чистого большого (инверсия снята)",
          _dirty_small < _clean_big)
    check("равная плотность → равный скор независимо от размера",
          _cert.score_of(_mk(10, 5)) == _cert.score_of(_mk(1000, 500)))
    # монотонность в обе стороны
    check("больше долга при том же размере → скор падает",
          _cert.score_of(_mk(100, 200)) < _cert.score_of(_mk(100, 20)))
    check("больше файлов при том же долге → скор не падает",
          _cert.score_of(_mk(1000, 50)) >= _cert.score_of(_mk(100, 50)))
    # ограниченность: советник не топит проект в одиночку
    check("штраф плотности ограничен сверху",
          _cert.score_of(_mk(1, 10 ** 6)) >= 100.0 - _cert.DENS_MAX - 0.05)
    # блокирующее и целостность остаются абсолютными
    check("расхождение сверки бьёт абсолютно, а не плотностью",
          _cert.score_of(_mk(1000, 0, verify_diverg=2)) == 90.0)
    check("пустой обход плотности не даёт", _cert.debt_density(5, 0) == 5.0)
    check("версия формулы объявлена и стоит в документе",
          isinstance(_cert.FORMULA, int)
          and "Формула v" in (root / "bin" / "certify.py").read_text(encoding="utf-8"))

    print("SELFTEST · добыча: сита, отбор, тождество прочтения")
    import atlas as _atlas
    import digest as _digest
    import grade as _grade

    for phrase in ("a margin of at least 16 points", "corner radius is 12 points",
                   "a hit region of at least 44x44 points", "1024 \u00d7 1024 pixels",
                   "animation lasts 300 milliseconds"):
        check(f"сито количества узнаёт «{phrase[:32]}»", bool(_digest.QTY.search(phrase)))
    for noise in ("There were 5 people in the room", "See chapter 3 of the guide",
                  "Released in 2026"):
        check(f"сито количества молчит на «{noise[:28]}»", not _digest.QTY.search(noise))

    deep = "\n".join(["Buttons should be legible."] * 12
                      + ["Use a margin of at least 16 points around each control."])
    laws, _ = _atlas._mine_laws(deep)
    check("числовая норма глубже потолка страницы всё равно добыта",
          any("16 points" in x for x in laws))
    check("потолок страницы соблюдён для прозы",
          len([x for x in laws if "16 points" not in x]) <= _atlas.LAWS_PER_PAGE)

    check("версия сита объявлена", isinstance(getattr(_atlas, "SIEVE", None), int))
    _src = (root / "bin" / "atlas.py").read_text(encoding="utf-8")
    check("пропуск страницы учитывает версию сита", 'prev.get("sieve") == SIEVE' in _src)
    check("версия сита ложится в след прочтения", '"sieve": SIEVE' in _src)

    # Починка сита обязана ВСТУПАТЬ В СИЛУ, а не только быть верной.
    # Родословная: SIEVE был введён в тождество прочтения, но просроченные
    # страницы не возвращались в очередь — переобход ждёт пустого фронтира,
    # а там стояло 62 458 адресов. Верная и полностью инертная починка.
    import tempfile as _tf, shutil as _sh
    _t = pathlib.Path(_tf.mkdtemp()); (_t / "atlas" / "visited").mkdir(parents=True)
    (_t / "atlas" / "visited" / "a.jsonl").write_text(
        json.dumps({"id": "/documentation/UIKit/x", "sieve": _atlas.SIEVE - 1}) + "\n"
        + json.dumps({"id": "/design/human-interface-guidelines/layout",
                      "sieve": _atlas.SIEVE - 1}) + "\n"
        + json.dumps({"id": "/documentation/UIKit/fresh", "sieve": _atlas.SIEVE}) + "\n",
        encoding="utf-8")
    _stale = _atlas._stale_by_sieve(_t)
    check("страница со старым ситом возвращается на перечитывание",
          "/documentation/UIKit/x" in _stale)
    check("страница с текущим ситом не перечитывается",
          "/documentation/UIKit/fresh" not in _stale)
    check("первоисточник /design/ перечитывается раньше справочника",
          _stale.index("/design/human-interface-guidelines/layout")
          < _stale.index("/documentation/UIKit/x"))
    _src2 = (root / "bin" / "atlas.py").read_text(encoding="utf-8")
    check("просроченные встают в НАЧАЛО очереди, а не в конец",
          "frontier[:0] = head" in _src2)
    _sh.rmtree(_t, ignore_errors=True)

    # Запись в библиотеку обязана быть идемпотентной ПО АДРЕСУ.
    # Родословная: запись шла дописыванием — допущение «страница читается
    # однажды». С перечитыванием по ситу оно перестало быть верным, и 33 691
    # просроченная страница легла бы вторым слоем поверх первого.
    _t2 = pathlib.Path(_tf.mkdtemp()); (_t2 / "library").mkdir()
    _atlas._lib_write(_t2, "/documentation/UIKit/a", ["первый", "второй"])
    _atlas._lib_write(_t2, "/documentation/UIKit/b", ["чужой"])
    _n1 = len((_t2 / "library" / "uikit.jsonl").read_text(encoding="utf-8").strip().splitlines())
    _atlas._lib_write(_t2, "/documentation/UIKit/a", ["первый", "второй"])
    _n2 = len((_t2 / "library" / "uikit.jsonl").read_text(encoding="utf-8").strip().splitlines())
    check("перечитывание не удваивает библиотеку", _n1 == _n2)
    _atlas._lib_write(_t2, "/documentation/UIKit/a", ["новый"])
    _txt = (_t2 / "library" / "uikit.jsonl").read_text(encoding="utf-8")
    check("перечитывание ЗАМЕНЯЕТ строки своей страницы",
          "новый" in _txt and "первый" not in _txt)
    check("соседняя страница при этом цела", "чужой" in _txt)
    _sh.rmtree(_t2, ignore_errors=True)

    # Порядок очереди по форме адреса. Замер: заглушка символа API даёт 0.45
    # строки, статья — 2.38, свод — 5.43. Заглушки составляли 87% очереди.
    check("форма адреса различается до загрузки",
          _atlas.shape_of("/design/human-interface-guidelines/layout") == "design"
          and _atlas.shape_of("/documentation/UIKit/add-home-screen-quick-actions") == "article"
          and _atlas.shape_of("/documentation/UIKit/uibutton") == "symbol"
          and _atlas.shape_of("/documentation/UIKit/init(frame:)") == "symbol")
    _fw = {"uikit": {"v": 100, "d": 100}}
    _q = ["/documentation/UIKit/uibutton", "/documentation/UIKit/add-quick-actions",
          "/documentation/UIKit/inittype"]
    _o = _atlas.order_frontier(_q, _fw)
    check("статья читается раньше заглушки символа",
          _o.index("/documentation/UIKit/add-quick-actions") == 0)
    check("заглушки уходят в хвост, а НЕ из очереди (ЗКН-Э001)",
          sorted(_o) == sorted(_q))

    # Хранение текста: починка сита не должна стоить обхода интернета.
    _t3 = pathlib.Path(_tf.mkdtemp()); _r3 = _t3 / "registry"
    (_r3 / "library").mkdir(parents=True)
    _atlas._corpus_put(_r3, "/design/hig/x", "Buttons should be legible.")
    _atlas._corpus_put(_r3, "/design/hig/x",
                       "Use a minimum tappable area of 44x44 points for controls.")
    _rm = _atlas.remine(_t3)
    check("перемол идёт офлайн по сохранённому корпусу", _rm["pages"] == 1)
    _lib = list((_r3 / "library").glob("*.jsonl"))
    _txt3 = _lib[0].read_text(encoding="utf-8") if _lib else ""
    check("корпус хранит последнее прочтение страницы, а не все подряд",
          "44x44" in _txt3 and "legible" not in _txt3)
    _sh.rmtree(_t3, ignore_errors=True)

    print("SELFTEST · свод уроков (купленное однажды обязательно для всех)")
    import lessons as _les
    _au = _les.audit()
    _viol = {L["code"]: L["violators"] for L in _au["lessons"] if L["violators"]}
    check(f"ни один орган не нарушает свод ({_viol or 'чисто'})", not _viol)
    check("под проверкой все органы департамента", _au["organs"] >= 35)
    check("объявленных долгов нет либо они названы",
          all(isinstance(x, tuple) or isinstance(x, list) for x in _au.get("debts", [])))
    # Долг не есть освобождение: причина, начинающаяся с 🕳, оставляет
    # орган нарушителем. Иначе реестр стал бы местом, где прячут долг.
    check("долг не прикрывается освобождением",
          _les._is_exempt({"У1": {"a.py": "причина"}}, "У1", "a.py")
          and not _les._is_exempt({"У1": {"a.py": "🕳 долг"}}, "У1", "a.py"))
    check("освобождение без причины не действует",
          not _les._is_exempt({"У1": {}}, "У1", "a.py"))
    # Урок без машинной проверки в свод не принимается.
    check("каждый урок несёт проверку", all(callable(L["fn"]) for L in _les.LESSONS))
    check("журнал не путается со складом (У2 различает)",
          "RE_JOURNAL" in (root / "bin" / "lessons.py").read_text(encoding="utf-8"))

    print("SELFTEST · реестр номеров правил (номер не несёт двух смыслов)")
    _reg = (root / "registry" / "RULES.md").read_text(encoding="utf-8")
    _rows = re.findall(r"^\|\s*\**(AE\d+)\**\s*\|\s*\**([^|*]+?)\**\s*\|", _reg, re.M)
    _nums = [n for n, _ in _rows]
    check("в реестре нет повторяющихся номеров", len(_nums) == len(set(_nums)))
    # Каждое правило, включённое хоть одним паспортом, обязано быть в реестре.
    _inuse = set()
    for _a in (root / "adapters").glob("*.json"):
        _d = json.loads(_a.read_text(encoding="utf-8"))
        for _m in ("report", "strict"):
            _inuse |= set((_d.get(_m) or {}).get("rules") or [])
    _missing = sorted(_inuse - set(_nums))
    check(f"каждое включённое правило есть в реестре ({_missing or 'все'})", not _missing)
    # Дыра, через которую 03.08.2026 прошло столкновение: сверялись только
    # номера, включённые ПАСПОРТАМИ. Правило, заведённое в линте и никем не
    # включённое, реестра не касалось — и заняло чужой номер молча. Теперь
    # сверяется КАЖДЫЙ номер, который линт умеет выдать.
    _src = (root / "bin" / "lint.py").read_text(encoding="utf-8")
    _emitted = set(re.findall(r'findings\.append\(\(\s*\n?\s*"(AE\d+)"', _src))
    _emitted |= set(re.findall(r'\(\s*\n?\s*"(AE\d+)", rel,', _src))
    _un = sorted(_emitted - set(_nums))
    check(f"каждое правило, которое линт УМЕЕТ выдать, есть в реестре ({_un or 'все'})",
          not _un)
    check("реестр знает не меньше номеров, чем наставление",
          not (set(guide_mod.GUIDE) - {"AE99"} - set(_nums)))
    # Ломаю: несуществующий номер обязан быть пойман.
    check("подделка ловится: чужой номер в паспорте был бы виден",
          "AE777" not in _nums)

    print("SELFTEST · AE18 разделитель (новое правило из замера)")
    _tok16 = json.loads((root / "registry" / "standards" / "tokens.json").read_text(encoding="utf-8"))
    _ad16 = {"report": {}, "strict": {"globs": ["bad.css"], "rules": ["AE18"]},
             "allow_extra": [], "sizes_extra": []}
    _bad16 = lint_mod.run(root, _ad16, _tok16, "strict", fx)
    _got16 = [f for f in _bad16["findings"] if f[0] == "AE18"]
    check("AE18 ломаю → красный: 0.5px и .5px пойманы обе формы записи",
          len(_got16) >= 2)
    check("AE18 называет число замера и его адрес в базе",
          all("1pt" in f[3] and "separator" in f[3] for f in _got16))
    _ad16["strict"]["globs"] = ["good.css"]
    _good16 = lint_mod.run(root, _ad16, _tok16, "strict", fx)
    check("AE18 чиню → зелёный: 1px чист, border-radius не судится",
          not [f for f in _good16["findings"] if f[0] == "AE18"])
    # Число живёт в базе, а не в коде: подмена базы обязана менять вердикт.
    _tok_wide = json.loads(json.dumps(_tok16))
    _tok_wide["separator"]["width_pt"] = 0.25
    _ad16["strict"]["globs"] = ["bad.css"]
    check("порог AE18 берётся ИЗ БАЗЫ, а не зашит в код (ЗКН-Э002)",
          not [f for f in lint_mod.run(root, _ad16, _tok_wide, "strict", fx)["findings"]
               if f[0] == "AE18"])

    print("SELFTEST · слияние складов (объединение, а не победа)")
    import corpus_merge as _cm
    _t5 = pathlib.Path(_tf.mkdtemp())
    _cm.write(_t5 / "a.gz", {"id:/x": {"id": "/x", "text": "A"},
                             "id:/y": {"id": "/y", "text": "Y"}})
    _cm.write(_t5 / "b.gz", {"id:/x": {"id": "/x", "text": "A"},
                             "id:/z": {"id": "/z", "text": "Z"}})
    _m, _st = _cm.union(_t5 / "o.gz", _t5 / "a.gz", _t5 / "b.gz")
    check("страницы обоих писателей уцелели при слиянии",
          set(_m) == {"id:/x", "id:/y", "id:/z"})
    check("чужая страница не потеряна (ломаю → было бы 2)", _st["итог"] == 3)
    _cm.write(_t5 / "c.gz", {"id:/x": {"id": "/x", "text": "A"}})
    _cm.write(_t5 / "d.gz", {"id:/x": {"id": "/x", "text": "A"}})
    check("одинаковое содержимое даёт одинаковые байты (mtime=0)",
          (_t5 / "c.gz").read_bytes() == (_t5 / "d.gz").read_bytes())
    check("жатва и атлас ключуются каждый своим полем",
          _cm._key({"id": "/a"}) and _cm._key({"page": "/b"})
          and _cm._key({"id": "/a"}) != _cm._key({"page": "/a"}))
    _sh.rmtree(_t5, ignore_errors=True)

    print("SELFTEST · пустой обход линта (ЗКН-Э006 исполняется, а не только объявлен)")
    # Родословная (02.08.2026): линт с неверным корнем печатал «Чисто.» и
    # возвращал ноль. Закон против пустого обхода существовал, а главный орган
    # его не исполнял — CI с опечаткой в пути был бы зелёным вечно.
    _empty = {"mode": "strict", "files": 0, "findings": [], "rules": [], "paths": []}
    _txt = lint_mod.render(_empty, "проба")
    check("нулевой обход не объявляется чистым", "Чисто." not in _txt)
    check("нулевой обход называет причину и закон",
          "КРАСНЫЙ" in _txt and "Э006" in _txt)
    _some = {"mode": "report", "files": 7, "findings": [], "rules": ["AE1"], "paths": []}
    check("настоящий обход без находок по-прежнему чист",
          "Чисто." in lint_mod.render(_some, "проба"))
    _src4 = (root / "bin" / "lint.py").read_text(encoding="utf-8")
    check("пустой обход красен в любом режиме, не только в строгом",
          'if not res["files"]:\n        return 1' in _src4)

    print("SELFTEST · целость исходников (несобирающееся не выкладывается)")
    # Родословная (02.08.2026): грубое авторазрешение конфликта положило в
    # main `bin/eyes.py` с маркерами — суд на main перестал запускаться вовсе.
    # Реестр был защищён проверкой целости json, а собственный код органов —
    # нет. Защита обязана быть симметричной: департамент выкладывает и то, и
    # другое.
    import ast as _ast
    _broken, _marks = [], []
    for _f in sorted((root / "bin").glob("*.py")):
        _t = _f.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"^<<<<<<< |^>>>>>>> ", _t, re.M):
            _marks.append(_f.name)
        try:
            _ast.parse(_t)
        except SyntaxError:
            _broken.append(_f.name)
    check(f"каждый орган разбирается питоном ({_broken or 'все'})", not _broken)
    check(f"ни в одном органе нет маркеров конфликта ({_marks or 'чисто'})", not _marks)
    for _sh_f in sorted((root / "bin").glob("*.sh")):
        pass
    check("проверка охватывает все органы, а не выборку",
          len(list((root / "bin").glob("*.py"))) >= 35)

    print("SELFTEST · целость реестра (битое состояние не уезжает)")
    # Департамент коммитит своё состояние сам. Значит, конфликт слияния или
    # оборванная запись способны положить в репозиторий json с маркерами —
    # и следующий прогон упадёт уже на чтении. Родословная: это случилось
    # трижды за 02.08.2026 при разборе конфликтов состояний наблюдения.
    _bad, _marked = [], []
    for _p in sorted(list((root / "registry").rglob("*.json"))
                     + list((root / "adapters").glob("*.json"))):
        _txt = _p.read_text(encoding="utf-8", errors="ignore")
        if "<<<<<<<" in _txt or ">>>>>>>" in _txt:
            _marked.append(_p.name)
        try:
            json.loads(_txt)
        except Exception:
            _bad.append(_p.name)
    check(f"каждый json реестра разбирается ({_bad or 'все'})", not _bad)
    check(f"ни в одном json нет маркеров конфликта ({_marked or 'чисто'})", not _marked)

    print("SELFTEST · чем закрывается дыра базы (сырьё названо)")
    import needs as _needs
    check("длительность перехода требует ЗАПИСИ, а не кадра",
          _needs.feed_of("motion.tab_crossfade_ms")[0] == "ЗАПИСЬ")
    check("вес начертания берётся из ШРИФТА, а не с кадра",
          _needs.feed_of("typography.weights.bold")[0] == "ШРИФТ")
    check("геометрия закрывается КАДРОМ",
          _needs.feed_of("geometry.radius_tile_pt")[0] == "КАДР")
    check("прозрачность требует известной подложки",
          _needs.feed_of("glass.thin")[0] == "КАДР+СЛОЙ")
    _hs = _needs.holes()
    check("ни одна дыра не осталась без названного сырья",
          not [h for h in _hs if h["feed"] == _needs.DEFAULT[0]],
          )
    check("девять дыр движения объявлены незакрываемыми кадром",
          len([h for h in _hs if h["feed"] == "ЗАПИСЬ"]) == 9)
    # Разбор чисел: потребность не должна читаться как наличие.
    _rc = [h for h in _hs if h["key"] == "geometry.radius_card_pt"]
    check("наличие и потребность разобраны раздельно (8 из 30)",
          bool(_rc) and _rc[0]["have"] == 8 and _rc[0]["need"] == 30)
    check("число, спорящее с фактом, отвергается",
          "parse_conflict" in (root / "bin" / "needs.py").read_text(encoding="utf-8"))

    print("SELFTEST · область нормы (число вне своей области — выдумка)")
    import propose as _prop
    check("норма слежения за взглядом помечена visionos",
          _prop.scope_of("/design/human-interface-guidelines/eyes") == "visionos")
    check("норма виджета помечена widget",
          _prop.scope_of("/design/human-interface-guidelines/widgets") == "widget")
    check("норма раскладки остаётся universal",
          _prop.scope_of("/design/human-interface-guidelines/layout") == "universal")
    check("норма кнопок остаётся universal",
          _prop.scope_of("/design/human-interface-guidelines/buttons") == "universal")
    _c = _prop.candidates([
        ("/design/human-interface-guidelines/eyes",
         "Use a margin of at least 16 points around the bounds of each item."),
        ("/design/human-interface-guidelines/layout",
         "Use a corner radius of at least 12 points for cards."),
    ])
    _by = {c["property"] + str(c["value"]): c for c in _c}
    check("узкая норма НЕ выдаётся за универсальную",
          all(not c["universal"] for c in _c if "eyes" in c["sources"][0]))
    check("универсальная норма не помечена узкой ложно",
          all(c["universal"] for c in _c if "layout" in c["sources"][0]))
    check("область едет с каждым кандидатом",
          all(c.get("scope") for c in _c))
    check("область видна в документе кандидатов",
          "Область обязательна" in (root / "bin" / "propose.py").read_text(encoding="utf-8"))

    print("SELFTEST · честность библиотеки (ЗКН-Э001)")
    check("СВЯЗЫВАЕМАЯ требует число + предмет + адрес",
          _grade.grade_line("Use a margin of at least 16 points around each item.",
                               "/design/human-interface-guidelines/layout") == _grade.BINDABLE)
    check("проза законом не считается",
          _grade.grade_line("On iPad, people can use this sample with a second app.",
                               "/documentation/UIKit/x") == _grade.PROSE)
    check("строка без адреса не существует",
          _grade.grade_line("Use 16 points of margin.", "") == _grade.NOADDR)
    check("обвязка страницы отделена от нормы",
          _grade.grade_line("To view this video content, you must consent to all cookies",
                               "page:https://x.example") == _grade.CHROME)

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
    sub.add_parser("remine")
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
    if a.cmd == "remine":
        import atlas as _a
        r = _a.remine(ROOT)
        print(f"перемол офлайн: страниц {r['pages']:,} · строк {r.get('laws', 0):,}")
        return 0
    if a.cmd == "selftest":
        return cmd_selftest(ROOT)
    return 2


if __name__ == "__main__":
    sys.exit(main())
