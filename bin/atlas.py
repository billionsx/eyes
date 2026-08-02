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
# ЗАТРАВКИ ОБХОДА. Первая — сам свод правил интерфейса, вторая — справочник API.
#
# Трое суток атлас ходил только по /documentation и накопил 62 466 адресов, из
# которых к HIG не относился НИ ОДИН. Справочник API описывает классы и методы;
# нормы дизайна с числами живут в /design/human-interface-guidelines. Департамент,
# судящий интерфейс, читал документацию по классам и называл это изучением Apple.
SEEDS = ("/design/human-interface-guidelines", "/documentation")
SEED = SEEDS[0]

# ПЕРВОИСТОЧНИК. Свод правил интерфейса читается раньше всего остального,
# пока не измерен: это предмет департамента (ст. 2), а справочник API лишь
# косвенная улика. Привилегия ограничена порогом PROBE — после него свод
# соревнуется по урожаю наравне со всеми, как и положено уликам.
PRIMARY = "/design/"
BUDGET = 700
DELAY = 1.0
LAWS_PER_PAGE = 10

# ВЕРСИЯ СИТА. Входит в тождество прочтения наравне с sha текста.
#
# Родословная (02.08.2026): отпечаток страницы считался только по её тексту.
# Отсюда следовало, что ЛЮБАЯ починка добытчика не применялась к уже
# прочитанному: текст не менялся — страница пропускалась. Департамент мог
# сколько угодно чинить сита, библиотека оставалась прежней. Починка, которая
# по построению не может вступить в силу, — худший вид долга: она выглядит
# сделанной. Поднял версию — корпус подлежит перечитыванию. Дорого и верно.
SIEVE = 2
RECYCLE_BATCH = 400  # размер переобхода на круге
PROBE = 25           # с этого числа страниц фреймворк считается изученным
PRIOR_D, PRIOR_V = 1, 10  # поправка на малое число наблюдений (см. order_frontier)

# ПРЕДМЕТ ДЕПАРТАМЕНТА (ст. 2). Департамент судит интерфейс: цвет, шрифт,
# геометрию, движение, прозрачность, материал, элементы управления, доступность.
# Словарь не выдуман — он собран из того, что департамент УЖЕ принуждает
# правилами AE1..AE13 и хранит в registry/standards/tokens.json.
#
# Зачем он здесь. Добытчик считал законом любое предложение с числом или
# долженствованием — и тащил в библиотеку прозу о разреженных матрицах,
# аудиокодеках и БПФ. Замер на 29.07.2026: из 23 448 собранных «законов» к
# предмету относились 3 333, то есть 14%. Девять десятых хода уходило в шум,
# и этот шум ставил в очередь новый шум: фронтир рос вдвое быстрее чтения
# (+3 395 против +1 500 за сутки), полных кругов — ноль.
DESIGN = re.compile(
    r"\b(?:colou?rs?|contrast|appearances?|dark mode|light mode|tints?|"
    r"fonts?|typograph\w*|text style|tracking|leading|kerning|type size|dynamic type|"
    r"layouts?|spacing|margins?|insets?|padding|safe area|alignment|"
    r"corners?|radius|radii|rounded|shapes?|"
    r"animat\w*|motion|durations?|easing|transitions?|springs?|"
    r"opacity|alpha|blurs?|materials?\b|glass|vibranc\w*|shadows?|elevation|"
    r"buttons?\b|controls?\b|navigation bar|tab bar|toolbars?|sheets?|alerts?|menus?|"
    r"pickers?|sliders?|switch(?:es)?|"
    r"icons?|symbols?|thumbnails?|"
    r"gestures?|tappable|touch targets?|tap targets?|hit (?:area|region|target)s?|"
    r"target size|pointer|focus\w*|"
    r"accessib\w*|voiceover|legibil\w*|"
    r"human interface|designs?\b|designing\b)", re.I)


def framework_of(pid: str) -> str:
    """Фреймворк по адресу: /documentation/<fw>/... → <fw>. Корень → _root."""
    parts = [x for x in (pid or "").split("/") if x]
    return (parts[1].lower() if len(parts) > 1 else "_root") or "_root"


def order_frontier(frontier: list, fw: dict, probe: int = PROBE) -> list:
    """Порядок обхода по УРОЖАЮ ПРЕДМЕТА, а не по времени попадания в очередь.

    Вес фреймворка — доля предметных законов на страницу, с поправкой на малое
    число наблюдений: (d + 1) / (v + 10). Поправка нужна, потому что порог
    «изучен / не изучен» на 402 фреймворках даёт обрыв: почти всё оказывается
    «ещё не изучено», и отбор перестаёт действовать. С поправкой шкала
    непрерывна: неизученный фреймворк получает нейтральный вес 0.10 и будет
    посмотрен, фреймворк с уликами поднимается или опускается по факту, а
    просмотренный без единого предметного закона опускается НИЖЕ неизученного —
    потому что о нём уже известно больше.

    Ничего не удаляется. Отсутствие находок на первых `probe` страницах — не
    доказательство пустоты фреймворка, а основание смотреть его последним
    (ЗКН-Э001). Как только у департамента появится причина, хвост будет пройден.
    """
    def rank(pid):
        # Первоисточник идёт вперёд ВСЕГО, пока он не измерен: департамент
        # обязан прочесть свой предмет прежде косвенных улик. Как только его
        # фреймворка пройдено `probe` страниц, привилегия снимается и дальше
        # решают улики — иначе на каждом круге переобхода свод занимал бы
        # голову и глушил обнаружение дрейфа (эту регрессию поймал суд).
        #
        # Мера изученности берётся по фреймворку САМОГО адреса, а не по
        # захардкоженному ключу: первая версия смотрела в fw["design"],
        # которого не существует (framework_of("/design/hig/x") даёт
        # "human-interface-guidelines"), и привилегия не гасла никогда —
        # код молча не делал того, что обещал его комментарий.
        s = fw.get(framework_of(pid)) or {}
        if pid.startswith(PRIMARY) and s.get("v", 0) < probe:
            return -1e9
        d, v = s.get("d", 0), s.get("v", 0)
        return -(d + PRIOR_D) / (v + PRIOR_V)
    return [p for _, p in sorted(enumerate(frontier),
                                 key=lambda ip: (rank(ip[1]), ip[0]))]


def quarantined(frontier: list, fw: dict, probe: int = PROBE) -> int:
    """Сколько адресов в очереди принадлежит изученным и пустым фреймворкам."""
    n = 0
    for pid in frontier:
        s = fw.get(framework_of(pid))
        if s and s.get("v", 0) >= probe and not s.get("d", 0):
            n += 1
    return n


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
    """Законы страницы: нормативное или числовое предложение О ПРЕДМЕТЕ.

    Возврат: (законы, сколько нормативных предложений отсеяно как не по теме).

    Отбор ПО ЦЕННОСТИ, а не по порядку следования. Родословная (02.08.2026):
    здесь стоял потолок в 10 предложений с ДОСРОЧНЫМ ВЫХОДОМ — извлекалось
    начало страницы, а не её нормы. След обрыва виден в замере: ровно 156
    страниц HIG по 10 строк каждая. Числовые нормы HIG лежат глубже десятого
    предложения и терялись все до одной.

    Числовая норма не отбрасывается НИКОГДА: она редка и есть единственное,
    из чего рождается проверяемое правило. Потолок остаётся для прозы.
    """
    bind, num, norm = [], [], []
    off = 0
    for raw in text.splitlines():
        if raw.startswith("## "):
            continue
        for s in _sentences(raw):
            has_q = bool(QTY.search(s))
            if not (NORM.search(s) or has_q):
                continue
            if not DESIGN.search(s):
                off += 1
                continue
            if has_q and NORM.search(s):
                bind.append(s)
            elif has_q:
                num.append(s)
            else:
                norm.append(s)
    room = max(0, LAWS_PER_PAGE - len(bind) - len(num))
    return bind + num + norm[:room], off


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
        if u.startswith("/documentation") or u.startswith("/design/"):
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


def bootstrap_fw(reg: Path) -> dict:
    """Копилка по фреймворкам из того, что уже пройдено и собрано.

    Считается один раз, чтобы отбор заработал сразу, а не после ещё одного
    полного обхода: посещённые страницы — из шардов, предметные законы — из
    библиотеки, пропущенной через тот же словарь предмета.
    """
    out = {}
    for f in sorted((reg / "atlas" / "visited").glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                pid = json.loads(line).get("id", "")
            except Exception:
                continue
            out.setdefault(framework_of(pid), {"v": 0, "d": 0})["v"] += 1
    for f in sorted((reg / "library").glob("*.jsonl")):
        s = out.setdefault(f.stem.lower(), {"v": 0, "d": 0})
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                law = json.loads(line).get("law", "")
            except Exception:
                continue
            if DESIGN.search(law):
                s["d"] += 1
    return out


def step(root: Path, budget: int = BUDGET, delay: float = DELAY, fixtures: Path = None) -> dict:
    reg = root / "registry"
    stf = reg / "atlas" / "state.json"
    stf.parent.mkdir(parents=True, exist_ok=True)
    st = json.loads(stf.read_text(encoding="utf-8")) if stf.exists() else {
        "frontier": list(SEEDS), "visited": 0, "laws": 0, "cycles": 0, "started": _now()}
    # ДОСЕВ ОДНОКРАТНЫЙ. Живой обход, начатый до появления первоисточника,
    # обязан его получить — но ровно один раз. Досев на каждом шаге держал бы
    # очередь вечно непустой, переобход никогда бы не запускался, и дрейф
    # законов перестал бы замечаться. Эту регрессию поймал суд.
    if not st.get("seeded"):
        for s0 in reversed(SEEDS):
            if s0 not in st["frontier"]:
                st["frontier"].insert(0, s0)
        st["seeded"] = True
    frontier = st["frontier"]
    fw = st.setdefault("fw", {})
    booted = 0
    if not fw:
        fw.update(bootstrap_fw(reg))
        booted = len(fw)
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

    offtopic = 0
    frontier[:] = order_frontier(frontier, fw)
    q0 = quarantined(frontier, fw)
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
        # Пропуск только если И текст тот же, И сито то же.
        if prev and prev.get("sha") == sha and prev.get("sieve") == SIEVE:
            continue
        laws, off = _mine_laws(ex["text"])
        offtopic += off
        s = fw.setdefault(framework_of(pid), {"v": 0, "d": 0})
        s["v"] += 1
        s["d"] += len(laws)
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
        _record(reg, {"id": pid, "sha": sha, "sieve": SIEVE, "t": ex["title"][:120],
                      "n": len(ex["text"]), "laws": len(laws), "ts": _now()})

    frontier[:] = order_frontier(frontier, fw)
    q1 = quarantined(frontier, fw)
    if booted:
        log.append(f"копилка фреймворков собрана из пройденного: {booted}")
    log.append(f"отбор: отсеяно не по предмету {offtopic} · в очереди изученных "
               f"и пустых фреймворков {q1} из {len(frontier)} (было {q0})")
    st["fw"] = fw
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
