#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ПРИСУТСТВИЕ (MCP-сервер департамента).

Зачем орган. До сих пор департамент судил ПОСЛЕ факта: PR-гейт ловит уже
написанное, монитор — уже отгруженное. Приговор приходит, когда нарушение
стоило рабочего дня. Инструмент, стоящий рядом в момент письма, снимает
нарушение до того, как оно родилось, и стоит поэтому дороже приговора.

Что это. Сервер Model Context Protocol поверх stdio: JSON-RPC 2.0, ни одной
внешней зависимости, как и весь департамент. Любой агент (Claude Code,
Cursor, Windsurf) получает четыре инструмента:

  eyes_check    судит фрагмент кода ТЕМИ ЖЕ правилами AE, что и CI
  eyes_law      ищет норму Apple под вопрос — с адресом страницы
  eyes_token    выдаёт измеренное число базы — с адресом замера
  eyes_attest   показывает, подтверждён ли замер словами свода

ГЛАВНОЕ РЕШЕНИЕ. eyes_check не имеет собственных правил. Он кладёт фрагмент
во временное дерево и зовёт bin/lint.py — тот самый орган, что стоит в
гейте. Своя копия правил внутри сервера означала бы два вердикта об одном
коде и медленное расхождение между ними; расхождение обнаружилось бы у
клиента и стоило бы репутации. Закон один — исполнение одно.

Чего орган НЕ делает. Не пишет код, не чинит, не советует «как лучше». Он
предъявляет норму с адресом. Вкус остаётся человеку (ст. 7.4).

Запуск:
    python3 bin/mcp.py                — сервер на stdio
    python3 bin/mcp.py --court        — суд, без сети и без клиента

Подключение (mcp.json клиента):
    {"mcpServers": {"eyes": {"command": "python3",
                             "args": ["<путь>/bin/mcp.py"]}}}
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint as lint_mod    # noqa: E402  один закон — одно исполнение
import law as law_mod      # noqa: E402
import attest as att_mod   # noqa: E402
import tally as tally_mod  # noqa: E402  журнал присутствия (только локально)
import guide as guide_mod  # noqa: E402  цель берётся из замера
import symbols as sym_mod  # noqa: E402  перечень системных глифов

PROTOCOL = "2025-06-18"
NAME = "billions-x-eyes"
VERSION = "1.0.0"

TOKENS = ROOT / "registry" / "standards" / "tokens.json"
ADAPTERS = ROOT / "adapters"

# Расширения, которые линт умеет читать. Фрагмент без объявленного языка
# кладётся как .css: правила AE поверхностей, теней и трекинга живут в
# стилях, и это самый частый предмет вопроса.
SUFFIX = {"css": ".css", "scss": ".scss", "sass": ".sass",
          "html": ".html", "tsx": ".tsx", "ts": ".ts",
          "jsx": ".jsx", "js": ".js", "vue": ".vue", "svelte": ".svelte"}

TOOLS = [
    {"name": "eyes_scan",
     "description": "ГЛАВНЫЙ ИНСТРУМЕНТ. Судит ВЕСЬ проект по пути: обходит "
                    "дерево сам, паспорт и настройка не нужны. Возвращает "
                    "балл, грейд, разбивку по правилам с ЦЕЛЬЮ для каждого "
                    "(что именно поставить вместо нарушения) и худшие файлы. "
                    "Работает с любым стеком: css, scss, html, ts, tsx, js, "
                    "jsx, vue, svelte.",
     "inputSchema": {
         "type": "object",
         "properties": {
             "path": {"type": "string",
                      "description": "Путь к корню проекта."},
             "mode": {"type": "string", "enum": ["strict", "report"]}},
         "required": ["path"]}},
    {"name": "eyes_guide",
     "description": "Что делать с находкой. По номеру правила выдаёт "
                    "проблему, действие и ЦЕЛЬ — измеренное число, которое "
                    "надо поставить, — плюс слова Apple с адресом, если "
                    "норма подтверждена двойным свидетельством.",
     "inputSchema": {
         "type": "object",
         "properties": {"rule": {"type": "string",
                                 "description": "Например AE11."}},
         "required": ["rule"]}},
    {"name": "eyes_symbol",
     "description": "Есть ли у Apple СИСТЕМНЫЙ глиф под этот смысл. Ищет по "
                    "9184 именам SF Symbols, снятым с настоящего приложения "
                    "Apple. Понимает словарь веба: search → magnifyingglass, "
                    "close → xmark, share → square.and.arrow.up. Возвращает "
                    "точные имена — рисовать свою иконку там, где есть "
                    "системная, значит разойтись с системой на глазах "
                    "у пользователя.",
     "inputSchema": {
         "type": "object",
         "properties": {"query": {"type": "string",
                                  "description": "Смысл иконки: search, "
                                                 "close, back, share…"},
                        "limit": {"type": "integer"}},
         "required": ["query"]}},
    {"name": "eyes_business",
     "description": "Норма бизнес-логики Большой семёрки (Deloitte, PwC, EY, "
                    "KPMG, McKinsey, BCG, Bain) под вопрос стратегии, "
                    "продукта или аналитики. Отдаёт положение фирмы и АДРЕС "
                    "страницы первоисточника.",
     "inputSchema": {
         "type": "object",
         "properties": {"query": {"type": "string"},
                        "limit": {"type": "integer"}},
         "required": ["query"]}},
    {"name": "eyes_check",
     "description": "Судит фрагмент кода правилами департамента Apple-стандартов "
                    "(AE1–AE15): поверхности, тени, форма угла, трекинг, кегль, "
                    "стекло, кинетика, прозрачность, шрифтовой стек, радиус, "
                    "отклик нажатия, цель касания, контраст. Каждая находка "
                    "несёт номер правила и причину. Те же правила, что в CI.",
     "inputSchema": {
         "type": "object",
         "properties": {
             "code": {"type": "string", "description": "Фрагмент кода."},
             "language": {"type": "string", "enum": sorted(SUFFIX),
                          "description": "Язык фрагмента. По умолчанию css."},
             "mode": {"type": "string", "enum": ["strict", "report"],
                      "description": "strict — гейт, report — советник."}},
         "required": ["code"]}},
    {"name": "eyes_law",
     "description": "Ищет норму Apple в библиотеке департамента (30 000+ норм, "
                    "336 фреймворков). Возвращает текст нормы и АДРЕС страницы "
                    "первоисточника. Свод норм (HIG) идёт впереди справочника API.",
     "inputSchema": {
         "type": "object",
         "properties": {
             "query": {"type": "string"},
             "limit": {"type": "integer", "description": "По умолчанию 5."},
             "bindable_only": {"type": "boolean",
                               "description": "Только нормы с числом и "
                                              "направлением — годные в правила."}},
         "required": ["query"]}},
    {"name": "eyes_token",
     "description": "Выдаёт измеренное число базы департамента (снято с кадров "
                    "iOS, а не процитировано). Без пути — весь список путей.",
     "inputSchema": {
         "type": "object",
         "properties": {
             "path": {"type": "string",
                      "description": "Путь вида tap_target.min_pt."}}}},
    {"name": "eyes_attest",
     "description": "Двойное свидетельство: подтверждён ли измеренный замер "
                    "словами свода Apple. ПОДТВЕРЖДЕНО — замер и текст "
                    "совпали; ПРОТИВОРЕЧИЕ — Apple пишет одно, отгружает "
                    "другое; НЕМО — свод молчит, число держится на замере.",
     "inputSchema": {
         "type": "object",
         "properties": {
             "path": {"type": "string", "description": "Предмет, например "
                                                       "tap_target."}}}},
]


def _tokens():
    return json.loads(TOKENS.read_text(encoding="utf-8"))


def _adapter():
    """Адаптер присутствия. Глоб один — временное дерево фрагмента; набор
    правил ПОЛНЫЙ, потому что вопрос задаётся про кусок, а не про проект:
    сужать нечего и незачем."""
    return {"allow_extra": [],
            "strict": {"globs": ["**/*"], "rules": [f"AE{i}" for i in range(1, 19)]},
            "report": {"globs": ["**/*"], "rules": [f"AE{i}" for i in range(1, 19)]}}


def check(code, language="css", mode="report"):
    """Судит фрагмент. Возвращает список находок [(правило, строка, причина)].

    Фрагмент кладётся во временное дерево и судится ПРОДУКТОВЫМ линтом.
    Каталог сносится в любом исходе: сервер живёт долго, мусор копился бы.
    """
    suffix = SUFFIX.get((language or "css").lower(), ".css")
    tmp = Path(tempfile.mkdtemp(prefix="eyes-mcp-"))
    try:
        (tmp / f"fragment{suffix}").write_text(code, encoding="utf-8")
        res = lint_mod.run(tmp, _adapter(), _tokens(),
                           mode if mode in ("strict", "report") else "report", tmp)
        return [{"rule": r, "line": ln, "why": why}
                for r, _f, ln, why in res["findings"]]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# Каталоги, куда департамент не заходит: чужой код не судится по законам
# проекта, а мусор сборки не является интерфейсом.
SKIP = {"node_modules", ".git", "dist", "build", "out", ".next", ".nuxt",
        "vendor", "coverage", "__pycache__", ".venv", "venv", "target",
        "Pods", "DerivedData", ".cache", "public/assets"}
# Список обязан совпадать с тем, что ЧИТАЕТ линт. Расхождение стоило
# дорого: сканер объявлял scss/vue/svelte, линт их пропускал, и проект на
# SCSS получал грейд A при нуле прочитанных файлов.
SCAN_SUFFIX = (".css", ".scss", ".sass", ".html", ".htm", ".tsx", ".ts",
               ".jsx", ".js", ".vue", ".svelte")
MAX_FILES = 3000


def collect_files(root):
    """Файлы проекта, годные к суду. Обходит ЛЮБОЕ дерево: паспорт не нужен."""
    root = Path(root)
    out = []
    for p in sorted(root.rglob("*")):
        if len(out) >= MAX_FILES:
            break
        if not p.is_file() or p.suffix.lower() not in SCAN_SUFFIX:
            continue
        if any(part in SKIP for part in p.parts):
            continue
        out.append(p)
    return out


def scan(root, mode="report"):
    """Судит ПРОЕКТ целиком. Возвращает находки, счёт по правилам и балл.

    Работает без паспорта: дерево обходится само, стек определяется по
    расширениям. Это и есть «любой проект» — подключение не требует ни
    настройки, ни присутствия департамента в чужом репозитории.

    Файлы зеркалятся во временное дерево, потому что продуктовый линт ходит
    по глобам и не умеет исключать чужие каталоги. Зеркало решает это, не
    трогая линт: один закон — одно исполнение.
    """
    root = Path(root).expanduser().resolve()
    if not root.exists():
        return {"error": f"нет такого пути: {root}"}
    files = collect_files(root)
    if not files:
        return {"error": "в дереве нет файлов интерфейса "
                         f"({', '.join(SCAN_SUFFIX)}) — судить нечего",
                "root": str(root)}
    tmp = Path(tempfile.mkdtemp(prefix="eyes-scan-"))
    try:
        for f in files:
            rel = f.relative_to(root)
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, dst)
        res = lint_mod.run(tmp, _adapter(), _tokens(),
                           mode if mode in ("strict", "report") else "report",
                           tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    findings = [{"rule": r, "file": f, "line": ln, "why": why}
                for r, f, ln, why in res["findings"]]
    from collections import Counter
    by_rule = Counter(x["rule"] for x in findings)
    by_file = Counter(x["file"] for x in findings)
    # Балл по объявленной формуле департамента в режиме советника.
    score = round(max(0.0, 100.0 - 0.05 * len(findings)), 1)
    gr = ("A" if score >= 93 else "B" if score >= 85 else
          "C" if score >= 70 else "D" if score >= 50 else "E")
    unres = res.get("vars_unresolved") or []
    return {"root": str(root), "files": res["files"],
            "vars_resolved": res.get("vars_resolved", 0),
            "vars_unresolved": len(unres),
            "blind_spot": (
                f"{len(unres)} переменных объявлены по-разному в темах и НЕ "
                f"разобраны — значения за ними не судились. Балл выше, чем "
                f"был бы при полном разборе." if unres else None),
            "findings_total": len(findings),
            "score": score, "grade": gr,
            "by_rule": [{"rule": r, "count": n,
                         **{k: v for k, v in guide_mod.guide(r).items()
                            if k in ("problem", "action", "target")}}
                        for r, n in by_rule.most_common()],
            "worst_files": [{"file": f, "count": n}
                            for f, n in by_file.most_common(10)],
            "sample": findings[:40]}


def business(query, limit=5):
    """Норма бизнес-логики Большой семёрки (Deloitte · PwC · EY · KPMG ·
    McKinsey · BCG · Bain) с адресом страницы фирмы.

    Библиотека семёрки хранится в своих полях (firm/text/at) — приводим к
    виду дознания, чтобы поиск был ОДИН на департамент, а не два похожих."""
    src = ROOT / "registry" / "library" / "big7.jsonl"
    if not src.exists():
        return []
    recs = []
    for line in src.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("text"):
            recs.append({"fw": d.get("firm", "big7"),
                         "id": d.get("at", ""), "law": d["text"]})
    return [{"firm": r["fw"], "insight": r["law"], "address": r["id"],
             "score": round(s, 2)}
            for r, s in law_mod.rank(recs, query, limit)]


def _flatten(tree, prefix=""):
    out = {}
    for k, v in tree.items():
        if k.startswith("_") or k in ("refs", "debts"):
            continue
        p = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, p + "."))
        elif isinstance(v, (int, float)) or (
                isinstance(v, list) and v and all(
                    isinstance(x, (int, float)) for x in v)):
            out[p] = v
    return out


def token(path=None):
    flat = _flatten(_tokens())
    if not path:
        return {"paths": sorted(flat)}
    if path in flat:
        return {"path": path, "value": flat[path]}
    near = sorted(p for p in flat if p.startswith(path))
    if near:
        return {"path": path, "value": None,
                "under": {p: flat[p] for p in near}}
    return {"path": path, "value": None,
            "note": "такого замера в базе нет — департамент не выдумывает чисел"}


# ── протокол ───────────────────────────────────────────────────────────────

def _text(payload):
    return {"content": [{"type": "text",
                         "text": json.dumps(payload, ensure_ascii=False,
                                            indent=2)}]}


def call_tool(name, args):
    args = args or {}
    if name == "eyes_scan":
        path = args.get("path")
        if not isinstance(path, str) or not path.strip():
            return _text({"error": "нужен path — корень проекта"})
        res = scan(path, args.get("mode", "report"))
        if "error" not in res:
            try:
                tally_mod.record([x["rule"] for x in res["sample"]], "project",
                                 scope=[f"AE{i}" for i in range(1, 19)])
            except Exception:
                pass
        return _text(res)
    if name == "eyes_guide":
        return _text(guide_mod.guide(str(args.get("rule", "")).upper()))
    if name == "eyes_symbol":
        q = args.get("query")
        if not isinstance(q, str) or not q.strip():
            return _text({"error": "нужен непустой query"})
        names, at = sym_mod.load()
        if not names:
            return _text({"error": "перечень символов недоступен"})
        res = sym_mod.rank(names, q, int(args.get("limit", 6) or 6))
        return _text({"query": q, "source": at, "total": len(names),
                      "symbols": [{"name": n, "score": round(s2, 1)}
                                  for n, s2 in res],
                      "note": ("системного глифа под этот смысл нет — "
                               "своя иконка оправдана") if not res else None})
    if name == "eyes_business":
        q = args.get("query")
        if not isinstance(q, str) or not q.strip():
            return _text({"error": "нужен непустой query"})
        return _text({"insights": business(q, int(args.get("limit", 5) or 5))})
    if name == "eyes_check":
        code = args.get("code")
        if not isinstance(code, str) or not code.strip():
            return _text({"error": "нужен непустой code"})
        lang = args.get("language", "css")
        f = check(code, lang, args.get("mode", "report"))
        # Журнал жизни правила. Уходят ТОЛЬКО номера правил и язык — ни
        # строки кода, ни причины находки (причина цитирует значение из
        # кода). Отказ журнала не имеет права отменить вердикт: клиент
        # пришёл за судом, а не за статистикой.
        try:
            tally_mod.record([x["rule"] for x in f], lang)
        except Exception:
            pass
        return _text({"findings": f, "count": len(f),
                      "verdict": "ЧИСТО" if not f else "ЕСТЬ НАРУШЕНИЯ"})
    if name == "eyes_law":
        q = args.get("query")
        if not isinstance(q, str) or not q.strip():
            return _text({"error": "нужен непустой query"})
        recs = law_mod.load()
        hits = law_mod.rank(recs, q, int(args.get("limit", 5) or 5),
                            bool(args.get("bindable_only")))
        return _text({"laws": [{"law": r["law"], "address": r["id"],
                                "framework": r["fw"], "score": round(s, 2),
                                "bindable": law_mod.is_bindable(r["law"])}
                               for r, s in hits],
                      "count": len(hits)})
    if name == "eyes_token":
        return _text(token(args.get("path")))
    if name == "eyes_attest":
        rows = att_mod.attest(_tokens(), law_mod.load(), args.get("path"))
        return _text({"attestations": rows})
    return _text({"error": f"нет такого инструмента: {name}"})


def handle(msg):
    """Один кадр JSON-RPC → ответ или None.

    None означает уведомление: у него нет id, и отвечать на него ЗАПРЕЩЕНО
    протоколом. Ответ на уведомление ломает клиента молча — он ждёт кадр с
    известным id и получает чужой.
    """
    mid = msg.get("id")
    method = msg.get("method")

    if mid is None:
        return None

    def ok(result):
        return {"jsonrpc": "2.0", "id": mid, "result": result}

    def err(code, message):
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": code, "message": message}}

    if method == "initialize":
        return ok({"protocolVersion": PROTOCOL,
                   "capabilities": {"tools": {}},
                   "serverInfo": {"name": NAME, "version": VERSION}})
    if method in ("tools/list", "tools/listChanged"):
        return ok({"tools": TOOLS})
    if method == "tools/call":
        p = msg.get("params") or {}
        try:
            return ok(call_tool(p.get("name"), p.get("arguments")))
        except Exception as e:  # инструмент упал — но сервер обязан жить
            return ok({"content": [{"type": "text",
                                    "text": f"сбой инструмента: {e}"}],
                       "isError": True})
    if method == "ping":
        return ok({})
    return err(-32601, f"метод не поддержан: {method}")


def serve(stdin=None, stdout=None):
    """Цикл stdio: кадр в строке, ответ в строке."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            stdout.write(json.dumps(
                {"jsonrpc": "2.0", "id": None,
                 "error": {"code": -32700, "message": "нечитаемый кадр"}}) + "\n")
            stdout.flush()
            continue
        out = handle(msg)
        if out is not None:
            stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
            stdout.flush()
    return 0


def court():
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    print("СУД · присутствие (MCP-сервер)")

    r = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {}})
    chk("рукопожатие отвечает версией протокола и именем",
        r["result"]["protocolVersion"] == PROTOCOL
        and r["result"]["serverInfo"]["name"] == NAME)

    chk("уведомление остаётся БЕЗ ответа (иначе клиент ломается молча)",
        handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None)

    r = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = [t["name"] for t in r["result"]["tools"]]
    chk("объявлены все восемь инструментов департамента",
        names == ["eyes_scan", "eyes_guide", "eyes_symbol", "eyes_business",
                  "eyes_check", "eyes_law", "eyes_token", "eyes_attest"])
    chk("главный инструмент объявлен ПЕРВЫМ: агент берёт верхний",
        names[0] == "eyes_scan")
    chk("у каждого инструмента объявлена схема входа",
        all(t.get("inputSchema", {}).get("type") == "object"
            for t in r["result"]["tools"]))

    r = handle({"jsonrpc": "2.0", "id": 3, "method": "нет/такого"})
    chk("неизвестный метод — ошибка -32601, а не молчание",
        r["error"]["code"] == -32601)

    # Нарушение, которое обязано ловиться: тень на чёрном холсте (AE2).
    r = handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                "params": {"name": "eyes_check", "arguments": {
                    "code": ".x{background:#000000;box-shadow:0 2px 8px #333;}",
                    "language": "css"}}})
    body = json.loads(r["result"]["content"][0]["text"])
    chk("тень на чёрном холсте поймана правилом AE2",
        any(f["rule"] == "AE2" for f in body["findings"]))

    # Та же проверка через продуктовый линт напрямую: вердикты обязаны совпасть.
    direct = check(".x{background:#000000;box-shadow:0 2px 8px #333;}", "css")
    chk("вердикт сервера равен вердикту продуктового линта",
        [f["rule"] for f in body["findings"]] == [f["rule"] for f in direct])

    r = handle({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                "params": {"name": "eyes_check", "arguments": {
                    "code": ".x{background:#1C1C1E;}", "language": "css"}}})
    body = json.loads(r["result"]["content"][0]["text"])
    chk("измеренная ступень поверхности нарушением не считается",
        body["verdict"] == "ЧИСТО")

    # Обещание клиенту проверяется машиной, а не декларируется в документе.
    import tempfile as _tf
    jr = Path(_tf.mkdtemp(prefix="eyes-jr-")) / "p.jsonl"
    _save = tally_mod.JOURNAL
    tally_mod.JOURNAL = jr
    handle({"jsonrpc": "2.0", "id": 51, "method": "tools/call",
            "params": {"name": "eyes_check", "arguments": {
                "code": ".secret{background:#123456;/*КОММЕРЧЕСКАЯ ТАЙНА*/}",
                "language": "css"}}})
    written = jr.read_text(encoding="utf-8") if jr.exists() else ""
    tally_mod.JOURNAL = _save
    chk("в журнал легло срабатывание правила", '"AE1"' in written)
    chk("КОД В ЖУРНАЛ НЕ ПОПАЛ: ни тайны, ни цвета, ни причины",
        "ТАЙНА" not in written and "123456" not in written
        and "лестниц" not in written)
    chk("в журнале нет полей сверх разрешённых",
        tally_mod.leaked(tally_mod.read(jr)) == [])
    shutil.rmtree(jr.parent, ignore_errors=True)

    # Проект целиком: сканер обязан работать без паспорта на любом дереве.
    import tempfile as _tf2
    proj = Path(_tf2.mkdtemp(prefix="eyes-proj-"))
    (proj / "src").mkdir()
    (proj / "src" / "a.css").write_text(
        ".x{background:#123456;border-radius:20px;}", encoding="utf-8")
    (proj / "node_modules").mkdir()
    (proj / "node_modules" / "junk.css").write_text(
        ".y{background:#abcdef;}", encoding="utf-8")
    sc = scan(proj)
    chk("проект судится без паспорта и без настройки",
        sc.get("findings_total", 0) >= 2 and sc["files"] == 1)
    chk("чужой код (node_modules) в суд НЕ берётся",
        all("node_modules" not in f["file"] for f in sc["sample"]))
    chk("у каждого правила в разбивке есть ЦЕЛЬ, а не только упрёк",
        all(b.get("target") for b in sc["by_rule"]))
    chk("балл и грейд выставлены", sc["grade"] in "ABCDE" and sc["score"] <= 100)
    empty = scan(proj / "node_modules" / "nope")
    chk("несуществующий путь — внятный отказ, а не пустой отличный отчёт",
        "error" in empty)
    (proj / "src2").mkdir()
    (proj / "src2" / "readme.txt").write_text("нет интерфейса", encoding="utf-8")
    shutil.rmtree(proj / "src")
    chk("дерево без интерфейса — ЧЕСТНЫЙ отказ, а не грейд A",
        "error" in scan(proj))
    shutil.rmtree(proj, ignore_errors=True)

    g = json.loads(handle({"jsonrpc": "2.0", "id": 61, "method": "tools/call",
                           "params": {"name": "eyes_guide",
                                      "arguments": {"rule": "ae11"}}}
                          )["result"]["content"][0]["text"])
    chk("наставление отвечает на строчный номер правила и несёт цель",
        g["rule"] == "AE11" and g["target"])

    sy = json.loads(handle({"jsonrpc": "2.0", "id": 63, "method": "tools/call",
                            "params": {"name": "eyes_symbol",
                                       "arguments": {"query": "search",
                                                     "limit": 2}}}
                           )["result"]["content"][0]["text"])
    chk("системный глиф находится по слову веба",
        sy["symbols"] and sy["symbols"][0]["name"] == "magnifyingglass")
    chk("выдача несёт ИСТОЧНИК перечня, а не голые имена",
        "name_availability" in (sy.get("source") or ""))
    sy2 = json.loads(handle({"jsonrpc": "2.0", "id": 64, "method": "tools/call",
                             "params": {"name": "eyes_symbol",
                                        "arguments": {"query": "квазар"}}}
                            )["result"]["content"][0]["text"])
    chk("нет глифа — так и сказано, своя иконка оправдана",
        sy2["symbols"] == [] and "оправдана" in (sy2["note"] or ""))

    b = json.loads(handle({"jsonrpc": "2.0", "id": 62, "method": "tools/call",
                           "params": {"name": "eyes_business",
                                      "arguments": {"query": "customer insight",
                                                    "limit": 2}}}
                          )["result"]["content"][0]["text"])
    chk("бизнес-норма приходит с фирмой и адресом первоисточника",
        b["insights"] and all(x["firm"] and x["address"]
                              for x in b["insights"]))

    r = handle({"jsonrpc": "2.0", "id": 6, "method": "tools/call",
                "params": {"name": "eyes_check", "arguments": {"code": "   "}}})
    chk("пустой фрагмент — внятная ошибка, а не падение",
        "error" in json.loads(r["result"]["content"][0]["text"]))

    r = handle({"jsonrpc": "2.0", "id": 7, "method": "tools/call",
                "params": {"name": "eyes_token",
                           "arguments": {"path": "tap_target.min_pt"}}})
    chk("измеренное число выдаётся из базы",
        json.loads(r["result"]["content"][0]["text"])["value"] == 44)

    r = handle({"jsonrpc": "2.0", "id": 8, "method": "tools/call",
                "params": {"name": "eyes_token",
                           "arguments": {"path": "нет.такого"}}})
    chk("несуществующий замер не выдумывается",
        json.loads(r["result"]["content"][0]["text"])["value"] is None)

    r = handle({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                "params": {"name": "eyes_token", "arguments": {"path": "geometry"}}})
    chk("узел раскрывается списком своих замеров",
        "under" in json.loads(r["result"]["content"][0]["text"]))

    r = handle({"jsonrpc": "2.0", "id": 10, "method": "tools/call",
                "params": {"name": "нетинструмента", "arguments": {}}})
    chk("неизвестный инструмент — ответ с ошибкой, сервер жив",
        "error" in json.loads(r["result"]["content"][0]["text"]))

    import io
    out = io.StringIO()
    serve(io.StringIO('{"jsonrpc":"2.0","id":1,"method":"ping"}\n'
                      'кривой кадр\n'
                      '{"jsonrpc":"2.0","method":"notifications/x"}\n'
                      '{"jsonrpc":"2.0","id":2,"method":"ping"}\n'), out)
    lines = [json.loads(x) for x in out.getvalue().strip().splitlines()]
    chk("нечитаемый кадр не роняет цикл: три ответа на четыре кадра",
        len(lines) == 3 and lines[1]["error"]["code"] == -32700)
    chk("после сбойного кадра сервер продолжает отвечать",
        lines[-1]["id"] == 2)

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    if "--court" in sys.argv:
        return court()
    return serve()


if __name__ == "__main__":
    sys.exit(main())
