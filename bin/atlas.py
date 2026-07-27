#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · АТЛАС. Автономный цикл по ВСЕЙ документации разработчика Apple.

Задача основателя: скрипт сам, шаг за шагом, без ИИ, входит в цикл изучения
всех внутренних пунктов https://developer.apple.com/documentation/ и
превращает документацию в собственную библиотеку законов.

Как устроено:
  ФРОНТИР  — очередь непройденных страниц. Семя: корень /documentation.
             Каждая пройденная страница отдаёт ссылки (references DocC-JSON)
             на новые /documentation/* — они встают в очередь. Так обход сам
             раскрывает всё дерево, ничего не зная о нём заранее.
  ШАГ ДНЯ  — бюджет страниц за прогон (по умолчанию 700, пауза 1.0 с):
             ежедневный воркфлоу делает шаг, состояние переживает прогоны.
  РЕЕСТР   — пройденное шардируется: registry/atlas/visited/<00..ff>.jsonl
             (страница · sha текста · заголовок · объём · метка времени).
             Полного текста атлас не хранит — хранит ЗАКОНЫ.
  ЗАКОНЫ   — из каждой страницы детерминированно выжимаются нормативные
             предложения (те же маркеры, что у знания) — до 10 на страницу —
             в библиотеку registry/library/<framework>.jsonl; INDEX.md
             считает масштаб. Это и есть «документация, ставшая законом».
  КРУГ     — когда фронтир пуст, атлас сам заводит второй круг: берёт самые
             старые пройденные страницы на переобход; изменение sha — строка
             в хронике («закон изменился»).
Граница прежняя (устав ст. 3): атлас пишет ТЕКСТ законов и адреса, числа
базы стандартов рождаются только замером или официальным китом с адресом.
"""
import hashlib
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extractor import extract_docc  # noqa: E402
from digest import NORM, QTY, _sentences  # noqa: E402
from crawler import UA, _robots_ok  # noqa: E402

HOST = "https://developer.apple.com"
SEED = "/documentation"
BUDGET = 700
DELAY = 1.0
LAWS_PER_PAGE = 10
RECYCLE_BATCH = 400  # размер переобхода на круге


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _shard(reg: Path, pid: str) -> Path:
    h = hashlib.sha256(pid.encode()).hexdigest()[:2]
    return reg / "atlas" / "visited" / f"{h}.jsonl"


def _seen(reg: Path, pid: str):
    f = _shard(reg, pid)
    if not f.exists():
        return None
    for ln in f.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("id") == pid:
            return r
    return None


def _record(reg: Path, rec: dict):
    f = _shard(reg, rec["id"])
    f.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    if f.exists():
        rows = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]
        rows = [r for r in rows if r.get("id") != rec["id"]]
    rows.append(rec)
    f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")


def _mine_laws(text: str):
    out = []
    for raw in text.splitlines():
        if raw.startswith("## "):
            continue
        for s in _sentences(raw):
            if NORM.search(s) or QTY.search(s):
                out.append(s)
                if len(out) >= LAWS_PER_PAGE:
                    return out
    return out


def _lib_write(reg: Path, pid: str, laws: list):
    fw = (pid.split("/") + ["", ""])[2] or "_root"
    fw = re.sub(r"[^a-z0-9_-]", "", fw.lower()) or "_root"
    f = reg / "library" / f"{fw}.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        for law in laws:
            fh.write(json.dumps({"id": pid, "law": law}, ensure_ascii=False) + "\n")


def _refs(raw: str):
    try:
        d = json.loads(raw)
    except Exception:
        return []
    out = set()
    for r in (d.get("references") or {}).values():
        u = r.get("url") or ""
        if u.startswith("/documentation"):
            out.add(u.split("#")[0].split("?")[0].rstrip("/"))
    return sorted(out)


def _fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", "replace")


def lib_index(reg: Path) -> dict:
    lib = reg / "library"
    lib.mkdir(parents=True, exist_ok=True)
    stats = {}
    for f in sorted(lib.glob("*.jsonl")):
        stats[f.stem] = sum(1 for _ in f.open(encoding="utf-8"))
    total = sum(stats.values())
    out = ["# БИБЛИОТЕКА ЗАКОНОВ · выжато атласом из документации Apple",
           "Нормативные предложения по фреймворкам (registry/library/*.jsonl).",
           "Текст закона несёт адрес страницы; в базу стандартов числа отсюда не переносятся (устав ст. 3).",
           "", "| Фреймворк | Законов |", "|---|---|"]
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        out.append(f"| {k} | {v} |")
    out.append("")
    out.append(f"Итого законов: {total} · фреймворков: {len(stats)}")
    (lib / "INDEX.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    return {"total": total, "frameworks": len(stats)}


def step(root: Path, budget: int = BUDGET, delay: float = DELAY, fixtures: Path = None) -> dict:
    reg = root / "registry"
    stf = reg / "atlas" / "state.json"
    stf.parent.mkdir(parents=True, exist_ok=True)
    st = json.loads(stf.read_text(encoding="utf-8")) if stf.exists() else {
        "frontier": [SEED], "visited": 0, "laws": 0, "cycles": 0, "started": _now()}
    frontier = st["frontier"]
    walked = changed = mined = enq = 0
    log = []

    if not frontier:  # круг завершён — переобход самых старых
        old = []
        vdir = reg / "atlas" / "visited"
        for f in sorted(vdir.glob("*.jsonl")):
            for ln in f.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(ln)
                    old.append((r.get("ts", ""), r["id"]))
                except Exception:
                    pass
        old.sort()
        frontier[:] = [pid for _, pid in old[:RECYCLE_BATCH]]
        st["cycles"] += 1
        log.append(f"круг {st['cycles']}: фронтир пуст — переобход {len(frontier)} старейших")

    while frontier and walked < budget:
        pid = frontier.pop(0)
        if fixtures is not None:
            fx = fixtures / (pid.strip("/").replace("/", "__") + ".json")
            if not fx.exists():
                continue
            raw = fx.read_text(encoding="utf-8")
            status = 200
        else:
            url = f"{HOST}/tutorials/data{pid}.json"
            if not _robots_ok(url):
                continue
            try:
                status, raw = _fetch(url)
            except Exception:
                status, raw = 0, ""
            time.sleep(delay)
        walked += 1
        if status != 200 or not raw.lstrip().startswith("{"):
            continue
        try:
            ex = extract_docc(raw)
        except Exception:
            continue
        prev = _seen(reg, pid)
        sha = ex["sha"]
        if prev and prev.get("sha") == sha:
            continue
        laws = _mine_laws(ex["text"])
        if prev is None:
            for ref in _refs(raw):
                if ref != pid and _seen(reg, ref) is None and ref not in frontier:
                    frontier.append(ref)
                    enq += 1
            if laws:
                _lib_write(reg, pid, laws)
                mined += len(laws)
        else:
            changed += 1
            log.append(f"закон изменился: {pid} · «{ex['title'][:60]}»")
        _record(reg, {"id": pid, "sha": sha, "t": ex["title"][:120],
                      "n": len(ex["text"]), "laws": len(laws), "ts": _now()})

    st["frontier"] = frontier
    st["visited"] = st.get("visited", 0) + walked
    st["laws"] = st.get("laws", 0) + mined
    st["last_step"] = _now()
    stf.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    idx = lib_index(reg)
    if walked or log:
        with (reg / "state" / "CHANGELOG.md").open("a", encoding="utf-8") as f:
            f.write(f"### {_now()} · атлас · шаг дня\n"
                    f"- пройдено {walked} · в очередь {enq} · законов добыто {mined} · изменилось {changed}\n"
                    f"- фронтир {len(frontier)} · всего пройдено {st['visited']} · библиотека {idx['total']} законов / {idx['frameworks']} фреймворков\n"
                    + "".join(f"- {l}\n" for l in log[:12]) + "\n")
    return {"walked": walked, "enqueued": enq, "mined": mined, "changed": changed,
            "frontier": len(frontier), "visited_total": st["visited"], "library": idx}


if __name__ == "__main__":
    b = int(sys.argv[sys.argv.index("--budget") + 1]) if "--budget" in sys.argv else BUDGET
    r = step(Path(__file__).resolve().parents[1], budget=b)
    print(f"атлас: пройдено {r['walked']} · очередь {r['frontier']} · всего {r['visited_total']} · "
          f"законов добыто {r['mined']} · библиотека {r['library']['total']}")
