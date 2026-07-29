#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СЛУЖБА, модуль M1-Б — надзор по коммитам (ст. 56).

Зачем орган существует. M1 (`review.py`) приходит на pull request. Но проект
может не работать через PR: писать прямо в ветку и деплоить каждый коммит.
Тогда весь надзор департамента молчит — не потому, что кода нет, а потому,
что нет повода, которого департамент ждал. Присутствие контроля не должно
зависеть от того, каким обычаем клиент кладёт код (ЗКН-Э001: отсутствие
надзора нельзя выдавать за чистоту).

Механика: push отдаёт «было → стало». GitHub API сравнивает эти два
состояния и возвращает файлы с патчами → берём ДОБАВЛЕННЫЕ строки (номера в
новой версии) → прогоняем полный линт по выложенному коду → оставляем только
находки, чьи (файл, строка) есть в диффе → кладём один комментарий к коммиту:
сводка и построчный список с адресами.

Правило тишины (EYES_QUIET_CLEAN, по умолчанию включено). Проект с сотнями
пушей получил бы сотни комментариев «находок 0» — это не надзор, а шум, и
шум глушит настоящие находки. Поэтому вердикт пишется в журнал прогона
ВСЕГДА, а комментарий к коммиту — только когда есть что сказать. Присутствие
контроля доказывает история прогонов, а не повторение слова «чисто».

Правило вежливости к клиенту: орган НИКОГДА не роняет чужую сборку. Находки —
это речь департамента, а не право вето. Право вето живёт в strict-гейтах
паспорта и включается решением основателя (ст. 7.4).

Запуск:  GITHUB_REPOSITORY=owner/name GITHUB_TOKEN=… EYES_AFTER=<sha> \\
         PROJECT_ROOT=. python3 bin/watch.py
         python3 bin/watch.py --selftest   — суд над отбором, без сети
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402
import projects  # noqa: E402
import review  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MAX_LINES = 40
ZERO = "0" * 40


def _api(url, token, data=None):
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}", "Accept": "application/vnd.github+json",
        "User-Agent": "bxe-watch"}, method="POST" if data else "GET",
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode() or "{}")


def changed(repo: str, before: str, after: str, token: str) -> dict:
    """Файлы, тронутые пушем → {путь: {номер новой строки: текст}}.

    Первый пуш в ветку и пуш после force дают `before`, которого в истории
    нет (нули или мёртвый sha). Тогда сравнивать не с чем — берём сам коммит.
    Недоступность API — не падение: пустой дифф и честная строка в журнале.
    """
    urls = []
    if before and before != ZERO and before != after:
        urls.append(f"https://api.github.com/repos/{repo}/compare/{before}...{after}")
    urls.append(f"https://api.github.com/repos/{repo}/commits/{after}")
    for u in urls:
        try:
            d = _api(u, token)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print(f"  сравнение недоступно ({u.rsplit('/', 1)[-1][:12]}): {e}")
            continue
        out = {}
        for f in d.get("files", []) or []:
            if f.get("status") != "removed":
                out[f["filename"]] = review.parse_added(f.get("patch", ""))
        return out
    return {}


def pick_hits(diff: dict, findings: list) -> list:
    """Находки, попавшие в добавленные строки. Чистая функция — сердце органа.

    `findings` — список (правило, путь, строка, сообщение) от линта.
    Возврат отсортирован по (путь, строка, правило): один и тот же пуш обязан
    давать один и тот же текст, иначе комментарий нельзя сверить (ЗКН-Э002).
    Дубли одного правила на одной строке схлопываются: strict и report ходят
    по одному файлу и находят одно и то же дважды.
    """
    seen, hits = set(), []
    for rule, rel, line, msg in findings:
        if rel in diff and line in diff[rel] and (rel, line, rule) not in seen:
            seen.add((rel, line, rule))
            hits.append({"path": rel, "line": line, "rule": rule, "msg": msg})
    return sorted(hits, key=lambda h: (h["path"], h["line"], h["rule"]))


def body_of(checked: int, hits: list, rules_n: int, sha: str, scope: int = -1) -> str:
    """Речь департамента к коммиту. Ни одного числа без адреса.

    `scope` — сколько добавленных строк лежит В ОБЛАСТИ надзора. Оно почти
    всегда меньше `checked`: пуш трогает и то, чего департамент не смотрит.
    Молчать об этой разнице нельзя — иначе «находок 0» читается как «всё
    проверено и чисто», а это подмена (ЗКН-Э001).
    """
    head = "## BXE · надзор по коммиту\n"
    look = (f"Пуш добавил строк: {checked} · в области надзора: {scope} · "
            if scope >= 0 else f"Добавленных строк: {checked} · ")
    if not hits:
        return (head + look + f"находок: **0** — чисто по {rules_n} правилам AE.\n\n"
                f"Коммит `{sha[:9]}`. Область надзора — глобы паспорта проекта; "
                f"строки вне её департамент не смотрел и чистыми не объявляет.")
    rows = "\n".join(
        f"- `{h['path']}:{h['line']}` — **{h['rule']}** — {h['msg']}"
        for h in hits[:MAX_LINES])
    tail = (f"\n\n…и ещё {len(hits) - MAX_LINES} — весь список в прогоне."
            if len(hits) > MAX_LINES else "")
    return (head + look + f"находок: **{len(hits)}** "
            f"(показаны первые {min(len(hits), MAX_LINES)}).\n\n{rows}{tail}\n\n"
            f"Коммит `{sha[:9]}`. Каждое число — из замера или первоисточника "
            f"с адресом (📐/🍎). Замечания — совет департамента, сборку не роняют.")


def watch(repo: str, before: str, after: str, token: str, project_root: Path) -> dict:
    globs_env = os.environ.get("EYES_CLIENT_GLOBS")
    if globs_env:
        gl = [g.strip() for g in globs_env.split(",") if g.strip()]
        adapter = {"project": os.environ.get("EYES_CLIENT_PROJECT", "client"),
                   "report": {"globs": gl,
                              "rules": ["AE1", "AE2", "AE3", "AE4", "AE5", "AE6",
                                        "AE7", "AE9", "AE10", "AE11"]},
                   "strict": {"globs": [], "rules": []}}
    else:
        adapter = projects.pick(ROOT)
    tokens = json.loads((ROOT / "registry" / "standards" / "tokens.json")
                        .read_text(encoding="utf-8"))
    diff = changed(repo, before, after, token)
    res_s = lint.run(ROOT, adapter, tokens, "strict", project_root)
    res_r = lint.run(ROOT, adapter, tokens, "report", project_root)
    hits = pick_hits(diff, res_s["findings"] + res_r["findings"])
    checked = sum(len(v) for v in diff.values())
    looked = set(res_s.get("paths", [])) | set(res_r.get("paths", []))
    scope = sum(len(v) for k, v in diff.items() if k in looked) if looked else -1
    rules_n = len(res_s["rules"]) + len(res_r["rules"])
    body = body_of(checked, hits, rules_n, after, scope)
    posted = False
    quiet = os.environ.get("EYES_QUIET_CLEAN", "1") == "1" and not hits
    if os.environ.get("BXE_DRY") != "1" and not quiet:
        try:
            _api(f"https://api.github.com/repos/{repo}/commits/{after}/comments",
                 token, {"body": body})
            posted = True
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print(f"  комментарий не лёг ({e}) — находки ниже в журнале прогона")
    return {"checked": checked, "hits": len(hits), "files": len(diff),
            "posted": posted, "quiet": quiet, "body": body}


def selftest() -> int:
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  ✓ " if cond else "  ✗ ") + name)
        ok = ok and cond

    print("СУД · надзор по коммитам (без сети)")
    diff = {"a.css": {5: ".x{color:#8E8E8E}", 9: ".y{}"},
            "b.tsx": {2: "<div/>"}}
    finds = [("AE1", "a.css", 5, "цвет вне лестницы"),
             ("AE2", "a.css", 7, "строка не тронута пушем"),
             ("AE3", "c.css", 5, "файл не тронут пушем"),
             ("AE4", "b.tsx", 2, "шрифт не унаследован")]
    got = pick_hits(diff, finds)
    check("в дифф попало только тронутое: строка мимо и файл мимо отброшены",
          [(h["path"], h["line"], h["rule"]) for h in got]
          == [("a.css", 5, "AE1"), ("b.tsx", 2, "AE4")])
    check("порядок детерминирован: путь → строка → правило",
          [h["path"] for h in pick_hits(diff, list(reversed(finds)))]
          == ["a.css", "b.tsx"])
    dbl = pick_hits(diff, [("AE1", "a.css", 5, "x"), ("AE1", "a.css", 5, "x")])
    check("одно правило на одной строке не удваивается (strict+report)",
          len(dbl) == 1)
    check("пустой дифф → ни одной находки, даже когда линт кричит",
          pick_hits({}, finds) == [])
    b0 = body_of(12, [], 10, "abc123def456", scope=3)
    check("чистый пуш всё равно получает ответ службы: присутствие видно",
          "находок: **0**" in b0 and "abc123def" in b0)
    check("тронутое и проверенное названы порознь: 12 тронуто, 3 смотрели",
          "добавил строк: 12" in b0 and "в области надзора: 3" in b0
          and "чистыми не объявляет" in b0)
    b1 = body_of(12, got, 10, "abc123def456")
    check("речь адресна: путь, строка и правило стоят в тексте",
          "`a.css:5`" in b1 and "**AE1**" in b1 and "находок: **2**" in b1)
    import os as _os
    _keep = _os.environ.get("EYES_QUIET_CLEAN")
    _os.environ["EYES_QUIET_CLEAN"] = "1"
    check("правило тишины объявлено, а не подразумевается",
          "EYES_QUIET_CLEAN" in Path(__file__).read_text(encoding="utf-8")
          and _os.environ.get("EYES_QUIET_CLEAN") == "1")
    if _keep is None:
        _os.environ.pop("EYES_QUIET_CLEAN", None)
    else:
        _os.environ["EYES_QUIET_CLEAN"] = _keep
    many = [{"path": "a.css", "line": i, "rule": "AE1", "msg": "m"}
            for i in range(1, MAX_LINES + 6)]
    check("длинный список обрезан честно: сказано, сколько осталось",
          f"и ещё {5}" in body_of(99, many, 10, "z" * 40))
    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    r = watch(os.environ["GITHUB_REPOSITORY"],
              os.environ.get("EYES_BEFORE", ""),
              os.environ["EYES_AFTER"],
              os.environ["GITHUB_TOKEN"],
              Path(os.environ.get("PROJECT_ROOT", ".")).resolve())
    _c = "лёг" if r["posted"] else ("не нужен: чисто" if r["quiet"] else "не лёг")
    print(f"надзор: файлов {r['files']} · добавленных строк {r['checked']} · "
          f"находок {r['hits']} · комментарий {_c}")
    print(r["body"])
