#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ПЕТЛЯ РЕВЬЮ (ст. 58).

Зачем орган. Департамент судил код двумя способами: гейт на PR (после того,
как написано) и монитор прода (после того, как отгружено). Оба говорят
«поздно». Петля ревью встаёт в третье место — между письмом и коммитом — и
не выпускает изменение, пока независимый ревьюер не подпишет его, а гейт не
станет зелёным.

Устройство петли взято целиком в базу департамента: `skills/loop-code-review/`
хранит дословную копию первоисточника (MIT, автор Dima Sukharev, коммит и
отпечатки — в ORIGIN.md рядом), `skills/loop-code-review-bxe/` — редакцию
департамента. Из сети при работе не тянется НИЧЕГО: копия здесь и есть
источник.

ЧТО ЭТОТ ФАЙЛ ДОБАВЛЯЕТ К ОПИСАНИЮ. Первоисточник описывает петлю словами:
«прогони подходящие тесты, линт и сборку», «не принимай оценку при неснятой
находке», «пять проходов». Слова исполняются агентом — значит, исполняются
по-разному. Здесь те же правила стоят машиной:

  scope    принадлежность изменений НЕ УГАДЫВАЕТСЯ. Пока задача не объявила
           свои пути, промпт не строится (первоисточник: «если принадлежность
           неоднозначна — спроси, а не гадай»).
  gate     измеримое условие выхода вместо «подходящих проверок»: находки AE
           ровно на ДОБАВЛЕННЫХ строках плюс объявленные внешние проверки с
           их кодами возврата. Находка на нетронутой строке названа, но не
           блокирует — регрессия задачи и доставшийся долг это разные вещи.
  prompt   промпт ревьюера самодостаточен, и это проверяется: примесь
           родительского контекста («предыдущий ревьюер сказал…») отбивается
           отказом, а не вежливой просьбой так не делать.
  verdict  таблица приёмки как автомат состояний. Оценка 10 при неснятой
           находке — не приём. Оценка 10 при красном гейте — не приём.
           Исчерпание предела проходов — НЕПОЛНО, а не успех.

ЗКН-Э009 · ОЦЕНКА НЕ ОТМЕНЯЕТ НАХОДКУ. Балл — сводка ревью, а не право
подписи. Любая неснятая действенная находка и любая красная проверка
сильнее любого балла.

ЗКН-Э001 здесь тоже действует: файл, который линт читать не умеет, попадает
в ответ отдельной строкой «не судится» — молчание органа нельзя предъявлять
как чистоту.

Запуск:
    python3 bin/loop.py scope   --root <проект> [--paths a,b] [--exclude c]
    python3 bin/loop.py gate    --root <проект> --paths a,b [--validated "npm test=0"]
    python3 bin/loop.py start   --root <проект> --paths a,b   # scope+gate+промпт
    python3 bin/loop.py verdict --score 9.6 [--finding "..."] [--no-actionable]
    python3 bin/loop.py status | reset
    python3 bin/loop.py --court                                # суд органа

Только stdlib.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BIN = Path(__file__).resolve().parent
ROOT = BIN.parent
sys.path.insert(0, str(BIN))
import lint as lint_mod  # noqa: E402  один закон — одно исполнение

SKILL_DIR = ROOT / "skills"
STATE = ROOT / "registry" / "state" / "loop-review.json"

# Планка приёмки первоисточника. Держится здесь одним числом, потому что
# число, размазанное по тексту, стареет молча (ЗКН-Э002).
ACCEPT_SCORE = 9.5
PASS_LIMIT = 5

LINTABLE = {".css", ".scss", ".sass", ".html", ".tsx", ".ts",
            ".jsx", ".js", ".vue", ".svelte"}

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
FILEHDR = re.compile(r"^\+\+\+ b/(.+)$")

# Отпечатки дословной копии. Подмена без правки ORIGIN.md валит суд:
# происхождение — документ, а не обещание.
VENDOR_SHA = {
    "loop-code-review/SKILL.md":
        "2f055ca9c6b0e9ec7520f3c808cf139e191252febcd265be9d5e59f59c3bed86",
    "loop-code-review/agents/openai.yaml":
        "17ef6b8bc2f9b1bda31748ec1f73691c404a5c3a804f8a0bee3a994783660a67",
    "loop-code-review/LICENSE":
        "44c274faa4134c198f9684280e03608066263491decccf706debcbb97ef8dec8",
}

# Примеси родительского контекста. Ревьюер, получивший вывод предыдущего
# ревьюера или догадку оркестратора, перестаёт быть независимым — и его
# подпись перестаёт что-либо значить.
LEAK = (
    "предыдущий ревьюер", "прошлый ревьюер", "ревьюер сказал", "я подозреваю",
    "мне кажется", "оркестратор", "родительск", "из прошлой сессии",
    "previous reviewer", "prior reviewer", "i suspect", "i think the bug",
    "parent agent", "parent thread", "earlier review",
)

NO_ACTIONABLE = (
    "замечаний нет", "нет замечаний", "находок нет", "нет находок",
    "нет действенных", "действенных находок нет",
    "no actionable", "no findings", "nothing actionable", "no comments",
)


class ScopeError(Exception):
    """Принадлежность изменений не объявлена — гадать запрещено."""


class LeakError(Exception):
    """В промпт ревьюера просочился родительский контекст."""


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(root: Path, *args) -> str:
    # core.quotePath=false обязателен: по умолчанию git отдаёт путь с
    # кириллицей как "\321\207..." — и файл задачи молча не находится ни в
    # области, ни в гейте. Молчание нельзя предъявлять как чистоту (ЗКН-Э001).
    r = subprocess.run(["git", "-c", "core.quotePath=false", *args],
                       cwd=str(root), capture_output=True, text=True)
    if r.returncode != 0 and "diff" not in args[:1]:
        return ""
    return r.stdout


# ─────────────────────────────────────────────────────────── ОБЛАСТЬ

def changed(root: Path) -> dict:
    """Живые изменения дерева: индекс, рабочая копия, неотслеживаемые."""
    staged = [x for x in _git(root, "diff", "--cached", "--name-only").splitlines() if x]
    unstaged = [x for x in _git(root, "diff", "--name-only").splitlines() if x]
    untracked = [x for x in _git(root, "ls-files", "--others",
                                 "--exclude-standard").splitlines() if x]
    allf = sorted(set(staged) | set(unstaged) | set(untracked))
    return {"staged": staged, "unstaged": unstaged, "untracked": untracked,
            "all": allf,
            "mixed": sorted(set(staged) & set(unstaged))}


def scope(root: Path, paths=None, exclude=None) -> dict:
    """Область задачи. Объявленные пути правят; git status лишь показывает,
    что ещё лежит в дереве и будет ИСКЛЮЧЕНО.

    Первоисточник запрещает выводить принадлежность из `git status`: в дереве
    может лежать чужая работа. Поэтому необъявленная область — не «взять всё»,
    а отказ на этапе промпта.
    """
    ch = changed(root)
    declared = [p.strip() for p in (paths or []) if p.strip()]
    excl = [p.strip() for p in (exclude or []) if p.strip()]
    if declared:
        owned = [p for p in declared if p not in excl]
        unrelated = [p for p in ch["all"] if p not in owned]
        missing = [p for p in owned if not (root / p).exists()]
    else:
        owned, unrelated, missing = [], ch["all"], []
    lintable = [p for p in owned if Path(p).suffix.lower() in LINTABLE]
    return {
        "root": str(root), "declared": bool(declared),
        "owned": owned, "unrelated": unrelated, "missing": missing,
        "mixed": [p for p in ch["mixed"] if p in owned],
        "untracked_owned": [p for p in ch["untracked"] if p in owned],
        "lintable": lintable,
        "not_lintable": [p for p in owned if p not in lintable],
        "dirty_total": len(ch["all"]),
    }


def added_lines(root: Path, files) -> dict:
    """{файл: {номера ДОБАВЛЕННЫХ строк}}. Неотслеживаемый файл добавлен весь."""
    out = {f: set() for f in files}
    untracked = set(_git(root, "ls-files", "--others", "--exclude-standard").splitlines())
    tracked = [f for f in files if f not in untracked]
    for f in files:
        if f in untracked:
            p = root / f
            if p.exists():
                try:
                    n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
                except OSError:
                    n = 0
                out[f] = set(range(1, n + 1))
    if tracked:
        diff = _git(root, "diff", "HEAD", "--unified=0", "--", *tracked)
        cur, ln = None, 0
        for row in diff.splitlines():
            m = FILEHDR.match(row)
            if m:
                cur, ln = m.group(1), 0
                continue
            m = HUNK.match(row)
            if m:
                ln = int(m.group(1)) - 1
                continue
            if row.startswith("-") or cur is None:
                continue
            if row.startswith("+"):
                ln += 1
                out.setdefault(cur, set()).add(ln)
    return {f: out.get(f, set()) for f in files}


def surface(root: Path, files) -> str:
    """Отпечаток поверхности. Меняется от любой правки — по нему видно,
    был ли между проходами хоть один код-шаг (застой ловится числом)."""
    h = hashlib.sha256()
    for f in sorted(files):
        p = root / f
        h.update(f.encode())
        h.update(p.read_bytes() if p.exists() else b"<absent>")
    return h.hexdigest()[:16]


# ─────────────────────────────────────────────────────────── ГЕЙТ

def _adapter(files, passport=None):
    rules = [f"AE{i}" for i in range(1, 19)]
    ad = {"report": {"globs": list(files), "rules": rules},
          "strict": {"globs": [], "rules": []},
          "allow_extra": [], "sizes_extra": [], "pt_to_css_px": 1}
    if passport:
        for k in ("allow_extra", "sizes_extra", "radius_extra", "pt_to_css_px"):
            if k in passport:
                ad[k] = passport[k]
    return ad


def gate(root: Path, project_root: Path, sc: dict, validated=None,
         passport=None) -> dict:
    """Измеримое условие выхода петли.

    Блокирует ТОЛЬКО находка на строке, которую задача добавила. Находка на
    нетронутой строке называется отдельно: это доставшийся долг, и требовать
    его снятия внутри чужой задачи — навязывать работу, а не судить работу.

    Внешние проверки (тесты, типы, сборка) объявляются вызывающим вместе с
    кодом возврата: `--validated "npm test=0"`. Необъявленных проверок гейт
    не выдумывает.
    """
    files = sc["lintable"]
    res = {"commands": [], "blocking": [], "inherited": [],
           "not_lintable": sc["not_lintable"], "external": []}
    if files:
        tokens = json.loads((root / "registry" / "standards" / "tokens.json")
                            .read_text(encoding="utf-8"))
        out = lint_mod.run(root, _adapter(files, passport), tokens, "report",
                           project_root)
        res["commands"].append(f"bxe lint (AE1..AE18) · файлов: {len(files)}")
        adds = added_lines(project_root, files)
        for rule, rel, line, msg in out["findings"]:
            row = {"rule": rule, "path": rel, "line": line, "msg": msg}
            (res["blocking"] if line in adds.get(rel, set())
             else res["inherited"]).append(row)
    for v in (validated or []):
        name, _, code = str(v).rpartition("=")
        try:
            rc = int(code)
        except ValueError:
            name, rc = str(v), 1
        res["external"].append({"command": name or str(v), "rc": rc})
        res["commands"].append(f"{name or v} → rc={rc}")
    res["green"] = (not res["blocking"]
                    and all(e["rc"] == 0 for e in res["external"]))
    return res


# ─────────────────────────────────────────────────────────── ПРОМПТ

def _leaks(text: str):
    low = (text or "").lower()
    return [m for m in LEAK if m in low]


def prompt(sc: dict, g: dict, extra: str = None) -> str:
    """Самодостаточный промпт ревьюера.

    Отказывает в двух случаях, и оба — по существу, а не по форме:
    область не объявлена (ревьюер получил бы чужую работу как свою) и в
    текст просочился родительский контекст (ревьюер перестал бы быть
    независимым).
    """
    if not sc.get("declared"):
        raise ScopeError(
            "область задачи не объявлена. В дереве изменённых файлов: "
            f"{sc['dirty_total']}. Назови пути задачи (--paths), либо спроси "
            "у пользователя — угадывать принадлежность запрещено.")
    if not sc["owned"]:
        raise ScopeError("объявленная область пуста — судить нечего.")
    if extra:
        bad = _leaks(extra)
        if bad:
            raise LeakError("в промпт просочился родительский контекст: "
                            + ", ".join(bad))
    ev = "\n".join(f"  - {c}" for c in g.get("commands", [])) or "  - не объявлены"
    owned = "\n".join(f"  - {p}" for p in sc["owned"])
    excl = "\n".join(f"  - {p}" for p in sc["unrelated"]) or "  - нет"
    mixed = ("\nСмешанные файлы (в них есть и чужие правки — суди только "
             "изменения задачи):\n" + "\n".join(f"  - {p}" for p in sc["mixed"])
             if sc["mixed"] else "")
    nl = ("\nВне досягаемости линта департамента (суди глазами): "
          + ", ".join(sc["not_lintable"]) if sc["not_lintable"] else "")
    tail = f"\n\nДополнительно от задачи:\n{extra.strip()}" if extra else ""
    return f"""Проверь ТОЛЬКО изменения задачи в этом дереве, самостоятельно. В рабочей копии могут лежать чужие правки — не трогай их, если изменения задачи от них прямо не зависят и не делают их хуже.

У тебя НЕТ истории родительского разговора. Не опирайся ни на какие прошлые обсуждения, выводы ведущего агента или чужие ревью. Все выводы делай только из состояния репозитория и вывода команд, которые запустишь сам. Оставайся в режиме чтения: не правь, не индексируй, не коммить, не сбрасывай, не прячь в stash, не пушь.

Корень репозитория: {sc['root']}

Область задачи:
{owned}{mixed}{nl}

Исключено (чужие активные правки):
{excl}

Уже прогнанные проверки (перезапусти сам, если сомневаешься):
{ev}

Считай это ревью передачей кода будущему сопровождающему. Сначала восстанови, что изменение делает, как идёт его важный поток управления или данных, на каких инвариантах оно стоит, как ведёт себя при отказе и почему приняты неочевидные решения. Если после разумного чтения соседнего кода часть объяснить не удаётся — назови точный символ или поток, что именно осталось неясным, и какую будущую правку или диагностику эта неясность делает рискованной. Незнакомая предметная логика сама по себе не есть плохая сопровождаемость; «непонятный код» без такой улики — не находка.

В первую очередь ищи действенные риски сопровождения, ошибки корректности, регрессии поведения, дыры безопасности и приватности, нарушения целостности данных, эксплуатационные опасности и отсутствие ценных тестов — всё это в границах изменений задачи. Соседний код читай для контекста, но не сообщай о находках в чужих правках и о доставшихся проблемах, если изменения задачи их не усугубляют. Не проси умозрительных рефакторингов и необязательного упрочнения там, где решение объективно крепкое.

Когда уместно, оцени также:
- Доказательность тестов: тест обязан прогонять изменённое поведение, падать на правдоподобной регрессии, утверждать наблюдаемый контракт и не подменять моком то, что проверяет. Если тесты добавлены или изменены — дай отдельную оценку их качества от 1 до 10 с коротким основанием. Если проверяемое поведение изменилось без тестов — скажи, оправдано ли это.
- Повторное использование: поищи существующие компоненты, хуки, утилиты, библиотеки, клиенты и службы проекта, прежде чем предлагать новую абстракцию. Находку о переиспользовании давай, только если можешь назвать конкретного кандидата и объяснить выигрыш.
- Архитектура и обычай: сверь изменение с различимыми границами проекта, направлением зависимостей и местными соглашениями. Не навязывай новую архитектуру и не выдавай предпочтение за нарушение.

Верни сначала находки, по убыванию тяжести, с конкретными ссылками «файл:строка» и коротким объяснением, чем это грозит пользователю или сопровождению. Если действенных находок нет — скажи это прямо и явно. Затем дай краткую сводку понимания: изменённая ответственность и важный поток, — чтобы сопровождаемость была проверена, а не предположена. Низкую оценку качества тестов считай находкой только тогда, когда назвал недостающее или вводящее в заблуждение покрытие.

Оценка: 10 — изменение понятно, известных дефектов в области нет, доказательства проверок полны; {ACCEPT_SCORE} — изменение понятно, действенных находок не осталось, возможны лишь необязательные придирки; ниже {ACCEPT_SCORE} — осталась хотя бы одна действенная находка либо доказательства проверок отсутствуют или красные. Закончи числовой оценкой от 1 до 10 и объясни, что конкретно мешает {ACCEPT_SCORE}/10, если что-то мешает.{tail}"""


# ─────────────────────────────────────────────────────────── ВЕРДИКТ

def fingerprint(text: str) -> str:
    """Отпечаток находки: одна и та же претензия, пересказанная другими
    словами, всё равно должна опознаваться как та же (застой)."""
    t = re.sub(r"[^\w\s/.:]+", " ", (text or "").lower())
    t = re.sub(r"\s+", " ", t).strip()
    return hashlib.sha256(t.encode()).hexdigest()[:12]


def parse_review(text: str) -> dict:
    """Из свободного текста ревьюера снимаются ДВА сигнала: числовая оценка и
    явное «действенных находок нет». Список находок отсюда НЕ угадывается —
    орган, который сам решает, что в абзаце было находкой, ошибается молча.
    """
    low = (text or "").lower()
    score = None
    for m in re.finditer(r"(\d+(?:[.,]\d+)?)\s*(?:/|из)\s*10", low):
        try:
            score = float(m.group(1).replace(",", "."))
        except ValueError:
            pass
    return {"score": score,
            "no_actionable": any(s in low for s in NO_ACTIONABLE)}


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    return {"passes": [], "limit": PASS_LIMIT, "persist": False,
            "seen": [], "asked": False}


def save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")


def verdict(st: dict, score=None, findings=None, no_actionable=False,
            gate_green=True, surface_hash=None, limit=None,
            persist=None) -> dict:
    """Таблица приёмки. Порядок проверок — порядок старшинства.

    1. Красный гейт сильнее любого балла.
    2. Неснятая действенная находка сильнее любого балла (ЗКН-Э009).
    3. Приём: находок нет И (балл ≥ планки ИЛИ явное «замечаний нет»).
    4. Балл ниже планки без находок и без явного сигнала — не приём и не
       провал: спросить ОДИН раз, что мешает планке.
    5. Предел проходов и застой закрывают петлю как НЕПОЛНУЮ, а не как успех.
    """
    findings = [f for f in (findings or []) if str(f).strip()]
    lim = int(limit if limit is not None else st.get("limit", PASS_LIMIT))
    pers = bool(st.get("persist") if persist is None else persist)
    fps = [fingerprint(f) for f in findings]
    n = len(st.get("passes", [])) + 1
    rec = {"n": n, "at": _now(), "score": score, "findings": fps,
           "gate": "зелёный" if gate_green else "КРАСНЫЙ",
           "surface": surface_hash, "no_actionable": bool(no_actionable)}

    if not gate_green:
        rec["decision"] = "ПРОДОЛЖИТЬ"
        rec["why"] = ("проверки затронутой поверхности красные — балл не "
                      "принимается ни при каком значении")
    elif findings:
        rec["decision"] = "ПРОДОЛЖИТЬ"
        rec["why"] = (f"неснятых действенных находок: {len(findings)}. "
                      f"ЗКН-Э009: оценка{f' {score}' if score else ''} не "
                      "отменяет находку")
    elif (score is not None and score >= ACCEPT_SCORE) or no_actionable:
        rec["decision"] = "ПРИЁМ"
        rec["why"] = ("находок нет, проверки зелёные, сигнал ревьюера: "
                      + (f"{score}/10" if score is not None
                         and score >= ACCEPT_SCORE else "«действенных находок нет»"))
    else:
        rec["decision"] = "ПРОДОЛЖИТЬ"
        rec["why"] = (f"находок ревьюер не назвал, но балл {score} ниже "
                      f"{ACCEPT_SCORE} и явного «замечаний нет» не дал. "
                      "Спроси ОДИН раз, что конкретно мешает планке; если "
                      "ответ не назовёт действенного — прими сигнал "
                      "(--no-actionable), а не гонись за баллом")
        rec["ask_once"] = True

    # Застой: два прохода подряд без единого код-шага и без новых претензий.
    prev = (st.get("passes") or [])[-1] if st.get("passes") else None
    stagnant = bool(
        prev and surface_hash and prev.get("surface") == surface_hash
        and set(fps) <= set(prev.get("findings") or [])
        and rec["decision"] != "ПРИЁМ")
    rec["stagnant"] = stagnant

    if rec["decision"] != "ПРИЁМ" and not pers:
        if n >= lim:
            rec["decision"] = "НЕПОЛНО"
            rec["why"] = (f"предел проходов исчерпан ({n}/{lim}) без сигнала "
                          f"приёмки. Это незакрытая петля, а не успех. "
                          f"Блокирует: {rec['why']}")
        elif stagnant:
            rec["decision"] = "НЕПОЛНО"
            rec["why"] = ("застой: поверхность между проходами не изменилась, "
                          "новых претензий нет. Планку не опускаем — "
                          f"блокирует: {rec['why']}")

    st.setdefault("passes", []).append(rec)
    st["seen"] = sorted(set(st.get("seen", [])) | set(fps))
    st["limit"], st["persist"] = lim, pers
    return rec


# ─────────────────────────────────────────────────────────── ЦЕЛОСТНОСТЬ

def vendor_check() -> dict:
    """Дословная копия должна быть дословной. Иначе `ORIGIN.md` врёт."""
    out = {"ok": True, "files": []}
    for rel, want in VENDOR_SHA.items():
        p = SKILL_DIR / rel
        got = (hashlib.sha256(p.read_bytes()).hexdigest() if p.exists()
               else "<нет файла>")
        ok = got == want
        out["ok"] = out["ok"] and ok
        out["files"].append({"file": rel, "ok": ok, "sha256": got})
    return out


# ─────────────────────────────────────────────────────────── СУД

def court() -> int:
    import shutil
    import tempfile
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    print("СУД · петля ревью (ст. 58)")

    v = vendor_check()
    chk("дословная копия первоисточника цела: отпечатки сошлись", v["ok"])
    org = (SKILL_DIR / "loop-code-review" / "ORIGIN.md")
    chk("происхождение предъявлено: коммит, лицензия, автор",
        org.exists() and "be0d6cc" in org.read_text(encoding="utf-8")
        and "MIT" in org.read_text(encoding="utf-8"))
    bxe = SKILL_DIR / "loop-code-review-bxe" / "SKILL.md"
    chk("редакция департамента на месте и зовёт СВОЙ гейт",
        bxe.exists() and "bin/loop.py" in bxe.read_text(encoding="utf-8"))

    tmp = Path(tempfile.mkdtemp(prefix="eyes-loop-"))
    try:
        subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
        subprocess.run(["git", "config", "user.email", "c@e"], cwd=tmp)
        subprocess.run(["git", "config", "user.name", "court"], cwd=tmp)
        # Базовая версия: одна ЧИСТАЯ строка и одна с нарушением — она войдёт
        # в историю и станет доставшимся долгом.
        (tmp / "a.css").write_text(".ok{color:#000000}\n.old{opacity:0.37}\n",
                                   encoding="utf-8")
        (tmp / "чужое.css").write_text(".x{opacity:0.41}\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp, check=True)

        # Правка задачи добавляет НОВОЕ нарушение; чужой файл трогает другая задача.
        (tmp / "a.css").write_text(
            ".ok{color:#000000}\n.old{opacity:0.37}\n.new{opacity:0.43}\n",
            encoding="utf-8")
        (tmp / "чужое.css").write_text(".x{opacity:0.41}\n.y{opacity:0.47}\n",
                                       encoding="utf-8")

        s_undecl = scope(tmp)
        chk("необъявленная область видит оба файла как чужие",
            s_undecl["owned"] == [] and len(s_undecl["unrelated"]) == 2)
        try:
            prompt(s_undecl, {"commands": []})
            leaked = False
        except ScopeError:
            leaked = True
        chk("ломаю → красный: без объявления путей промпт НЕ строится "
            "(принадлежность не угадывается)", leaked)

        s = scope(tmp, paths=["a.css"])
        chk("чиню → зелёный: объявлен a.css — чужое.css названо исключённым",
            s["owned"] == ["a.css"] and s["unrelated"] == ["чужое.css"])

        adds = added_lines(tmp, ["a.css"])
        chk("добавленная строка опознана по номеру (3), старые не тронуты",
            adds["a.css"] == {3})

        g = gate(ROOT, tmp, s)
        b_lines = {x["line"] for x in g["blocking"]}
        i_lines = {x["line"] for x in g["inherited"]}
        chk("ломаю → красный: нарушение на ДОБАВЛЕННОЙ строке блокирует",
            not g["green"] and b_lines == {3})
        chk("доставшийся долг на строке 2 назван, но петлю не держит",
            i_lines == {2})
        chk("чужой файл в гейт не попал", all(
            x["path"] == "a.css" for x in g["blocking"] + g["inherited"]))

        # Чиню добавленную строку — гейт зеленеет.
        (tmp / "a.css").write_text(
            ".ok{color:#000000}\n.old{opacity:0.37}\n.new{opacity:0.3}\n",
            encoding="utf-8")
        s2 = scope(tmp, paths=["a.css"])
        g2 = gate(ROOT, tmp, s2)
        chk("чиню → зелёный: правка добавленной строки открывает гейт",
            g2["green"] and not g2["blocking"] and g2["inherited"])

        gx = gate(ROOT, tmp, s2, validated=["npm test=1"])
        chk("объявленная внешняя проверка с rc=1 закрывает гейт",
            not gx["green"])
        gy = gate(ROOT, tmp, s2, validated=["npm test=0", "tsc=0"])
        chk("две зелёные внешние проверки гейт не трогают", gy["green"])

        import contextlib
        import io as _io

        def _run(*argv):
            buf = _io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = main(list(argv))
            return rc, buf.getvalue()

        rc, out = _run("start", "--root", str(tmp), "--paths", "a.css",
                       "--validated", "npm test=1")
        chk("ломаю → красный: при красной проверке промпт НЕ выдаётся "
            "(ревьюер не тратит проход на названное машиной)",
            rc == 1 and "ПРОМПТ РЕВЬЮЕРА" not in out)
        rc, out = _run("start", "--root", str(tmp), "--paths", "a.css")
        chk("чиню → зелёный: по зелёной проверке промпт выдан",
            rc == 0 and "ПРОМПТ РЕВЬЮЕРА" in out)

        p = prompt(s2, g2)
        chk("промпт самодостаточен: назван корень, область и исключённое",
            "чужое.css" in p and "a.css" in p and str(tmp) in p)
        chk("промпт запрещает опору на родительскую историю прямым текстом",
            "НЕТ истории родительского разговора" in p)
        try:
            prompt(s2, g2, extra="Предыдущий ревьюер сказал, что тут гонка.")
            blocked = False
        except LeakError:
            blocked = True
        chk("ломаю → красный: примесь родительского контекста отбита",
            blocked)
        chk("чиню → зелёный: чистое дополнение проходит и видно в промпте",
            "Уточни поведение при офлайне." in
            prompt(s2, g2, extra="Уточни поведение при офлайне."))

        h1 = surface(tmp, ["a.css"])
        (tmp / "a.css").write_text(".ok{color:#000000}\n", encoding="utf-8")
        chk("отпечаток поверхности меняется от правки (застой ловится числом)",
            surface(tmp, ["a.css"]) != h1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("СУД · таблица приёмки")

    def st():
        return {"passes": [], "limit": 5, "persist": False, "seen": []}

    r = verdict(st(), score=9.6, findings=["утечка ключа в лог"],
                gate_green=True, surface_hash="a")
    chk("ЗКН-Э009: 9.6 при неснятой находке — НЕ приём",
        r["decision"] == "ПРОДОЛЖИТЬ" and "ЗКН-Э009" in r["why"])
    r = verdict(st(), score=10.0, findings=[], gate_green=False,
                surface_hash="a")
    chk("10/10 при красных проверках — НЕ приём",
        r["decision"] == "ПРОДОЛЖИТЬ")
    r = verdict(st(), score=9.6, findings=[], gate_green=True,
                surface_hash="a")
    chk("9.6 без находок при зелёном гейте — ПРИЁМ", r["decision"] == "ПРИЁМ")
    r = verdict(st(), score=9.5, findings=[], gate_green=True,
                surface_hash="a")
    chk("ровно на планке 9.5 — ПРИЁМ (планка включительная)",
        r["decision"] == "ПРИЁМ")
    r = verdict(st(), score=9.0, findings=[], no_actionable=True,
                gate_green=True, surface_hash="a")
    chk("9.0 с явным «действенных находок нет» — ПРИЁМ",
        r["decision"] == "ПРИЁМ")
    r = verdict(st(), score=9.0, findings=[], gate_green=True,
                surface_hash="a")
    chk("9.0 без находок и без сигнала — не приём, но и не провал: "
        "спросить ОДИН раз",
        r["decision"] == "ПРОДОЛЖИТЬ" and r.get("ask_once"))

    def _st4():
        return {"passes": [{"n": i, "surface": "s", "findings": []}
                           for i in range(1, 5)],
                "limit": 5, "persist": False, "seen": []}
    r = verdict(_st4(), score=8.0, findings=["та же претензия"],
                gate_green=True, surface_hash="s")
    chk("исчерпание предела проходов — НЕПОЛНО, а не успех",
        r["decision"] == "НЕПОЛНО" and "предел" in r["why"])
    r = verdict({"passes": [{"n": 1, "surface": "s",
                             "findings": [fingerprint("та же претензия")]}],
                 "limit": 5, "persist": False, "seen": []},
                score=8.0, findings=["та же претензия"], gate_green=True,
                surface_hash="s")
    chk("застой (нет код-шага, претензия та же) — НЕПОЛНО",
        r["decision"] == "НЕПОЛНО" and "застой" in r["why"])
    r = verdict(_st4(), score=8.0, findings=["ещё живая находка"],
                gate_green=True, surface_hash="s", persist=True)
    chk("требование дожать снимает предел, но НЕ опускает планку",
        r["decision"] == "ПРОДОЛЖИТЬ")

    pr = parse_review("Находок нет. Итог: 9.7/10.")
    chk("свободный текст ревьюера читается: балл и явный сигнал",
        pr["score"] == 9.7 and pr["no_actionable"])
    pr = parse_review("Сначала 6/10, после правок итог 9.8 / 10")
    chk("берётся ПОСЛЕДНЯЯ оценка, а не первая", pr["score"] == 9.8)
    chk("одна претензия разными словами даёт разные отпечатки только "
        "при разной сути",
        fingerprint("Утечка ключа в лог!") == fingerprint("утечка ключа в лог")
        and fingerprint("гонка в очереди") != fingerprint("утечка ключа в лог"))

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────── CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description="BXE · петля ревью (ст. 58)")
    ap.add_argument("--court", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("scope", "gate", "start"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".")
        p.add_argument("--paths", default="")
        p.add_argument("--exclude", default="")
        p.add_argument("--project", default="")
        p.add_argument("--validated", action="append", default=[])
        p.add_argument("--extra", default="")
        p.add_argument("--anyway", action="store_true")
        p.add_argument("--json", action="store_true")
    v = sub.add_parser("verdict")
    v.add_argument("--root", default=".")
    v.add_argument("--paths", default="")
    v.add_argument("--score", type=float)
    v.add_argument("--finding", action="append", default=[])
    v.add_argument("--no-actionable", action="store_true")
    v.add_argument("--gate-red", action="store_true")
    v.add_argument("--review-file", default="")
    v.add_argument("--limit", type=int)
    v.add_argument("--persist", action="store_true")
    v.add_argument("--json", action="store_true")
    sub.add_parser("status")
    sub.add_parser("reset")
    a = ap.parse_args(argv)

    if a.court or a.cmd is None and "--court" in (argv or sys.argv):
        return court()
    if a.cmd is None:
        ap.print_help()
        return 2

    if a.cmd == "reset":
        if STATE.exists():
            STATE.unlink()
        print("петля сброшена")
        return 0
    if a.cmd == "status":
        st = load_state()
        print(f"проходов: {len(st.get('passes', []))}/{st.get('limit', PASS_LIMIT)}"
              f" · дожимать: {'да' if st.get('persist') else 'нет'}")
        for r in st.get("passes", []):
            print(f"  #{r['n']} {r.get('decision')} · балл {r.get('score')} · "
                  f"гейт {r.get('gate')} · находок {len(r.get('findings') or [])}")
        return 0

    proot = Path(a.root).resolve()
    paths = [x.strip() for x in a.paths.split(",") if x.strip()]
    excl = [x.strip() for x in getattr(a, "exclude", "").split(",") if x.strip()]

    if a.cmd == "verdict":
        st = load_state()
        score, no_act = a.score, a.no_actionable
        if a.review_file:
            pr = parse_review(Path(a.review_file).read_text(encoding="utf-8"))
            score = score if score is not None else pr["score"]
            no_act = no_act or pr["no_actionable"]
        sh = surface(proot, paths) if paths else None
        r = verdict(st, score=score, findings=a.finding, no_actionable=no_act,
                    gate_green=not a.gate_red, surface_hash=sh,
                    limit=a.limit, persist=a.persist or None)
        save_state(st)
        if a.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print(f"проход #{r['n']} · {r['decision']}\n  {r['why']}")
        return 0 if r["decision"] == "ПРИЁМ" else 1

    passport = None
    if a.project:
        f = ROOT / "adapters" / f"{a.project}.json"
        if f.exists():
            passport = json.loads(f.read_text(encoding="utf-8"))
    sc = scope(proot, paths=paths, exclude=excl)
    if a.cmd == "scope":
        print(json.dumps(sc, ensure_ascii=False, indent=2))
        return 0
    g = gate(ROOT, proot, sc, validated=a.validated, passport=passport)
    if a.cmd == "gate":
        print(json.dumps(g, ensure_ascii=False, indent=2))
        return 0 if g["green"] else 1
    if not g["green"] and not a.anyway:
        print(f"ГЕЙТ КРАСНЫЙ · блокирующих находок {len(g['blocking'])}"
              + (f" · внешних провалов {sum(1 for e in g['external'] if e['rc'])}"
                 if any(e["rc"] for e in g["external"]) else ""))
        for x in g["blocking"]:
            print(f"  ✗ {x['rule']} {x['path']}:{x['line']} — {x['msg']}")
        for e in g["external"]:
            if e["rc"]:
                print(f"  ✗ {e['command']} → rc={e['rc']}")
        print("\nПромпт НЕ выдан: свежего ревьюера зовут по зелёной проверке, "
              "иначе он тратит проход на то, что уже названо машиной. "
              "Почини и повтори (--anyway обходит, но проход всё равно "
              "не примут).")
        return 1
    try:
        pr = prompt(sc, g, extra=a.extra or None)
    except (ScopeError, LeakError) as e:
        print(f"ОТКАЗ: {e}")
        return 2
    if a.json:
        print(json.dumps({"scope": sc, "gate": g, "prompt": pr},
                         ensure_ascii=False, indent=2))
    else:
        print(f"ГЕЙТ: {'зелёный' if g['green'] else 'КРАСНЫЙ'} · "
              f"блокирующих находок {len(g['blocking'])} · "
              f"доставшихся {len(g['inherited'])}")
        for x in g["blocking"]:
            print(f"  ✗ {x['rule']} {x['path']}:{x['line']} — {x['msg']}")
        print("\n─── ПРОМПТ РЕВЬЮЕРА (отдать свежему агенту без истории) ───\n")
        print(pr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
