#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СВЕЖЕСТЬ. Департамент сам замечает деплой клиента.

Зачем орган. До сих пор монитор просыпался пингом: проект после деплоя стучал
в департамент через repository_dispatch, и для этого клиенту требовался
ЛИЧНЫЙ КЛЮЧ с правом писать в чужой репозиторий. Ключ надо было заводить,
хранить, помнить о сроке и менять при ротации — и всё это ради того, чтобы
департамент узнал про событие, которое и так видно снаружи.

Ключ, который можно не выдавать, не выдают. Оба репозитория публичные, и
последний успешный деплой виден любому без всякой авторизации. Департамент
смотрит сам.

Механика: раз в четверть часа орган спрашивает публичный API про последний
успешный прогон воркфлоу деплоя каждого подключённого проекта и сверяет с
записанным. Совпало — выходит за секунды и тяжёлый монитор не поднимается.
Разошлось — печатает новый sha, и монитор идёт смотреть живыми глазами.

Что это меняет по существу:
  · клиенту больше не нужен ключ доступа к департаменту — совсем;
  · реакция стала быстрее: до 15 минут вместо расписания раз в 6 часов;
  · при ротации ключей ломаться нечему — здесь ключей нет.

Приложения:
    python3 bin/fresh.py            — есть ли новый деплой (код 0/1)
    python3 bin/fresh.py --write    — то же и запомнить увиденное
    python3 bin/fresh.py --court
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "registry" / "state" / "FRESH.json"
API = "https://api.github.com"


def projects():
    """Подключённые проекты из паспортов. Только те, у кого объявлены и
    репозиторий, и воркфлоу деплоя: без них следить не за чем."""
    out = []
    for p in sorted(glob.glob(str(ROOT / "adapters" / "*.json"))):
        try:
            d = json.loads(Path(p).read_text(encoding="utf-8"))
        except ValueError:
            continue
        if d.get("project") in (None, "default"):
            continue
        if not d.get("repo") and d.get("deploy_source") != "prod":
            continue
        if d.get("enabled", True) is False:
            continue
        out.append({"project": d["project"], "repo": d.get("repo", ""),
                    "workflow": d.get("deploy_workflow", ""),
                    "source": d.get("deploy_source", "actions"),
                    "environment": d.get("deploy_environment", "Production"),
                    "prod": d.get("prod", "")})
    return out


def _get(url, token=None, timeout=20):
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "billions-x-eyes"})
    # Токен НЕ обязателен: репозитории публичные. Он берётся только затем,
    # чтобы не упереться в лимит анонимных запросов, и это встроенный
    # GITHUB_TOKEN прогона, а не чей-то личный ключ.
    if token:
        req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError, TimeoutError, OSError):
        return None


def workflow_id(repo, workflow_name, token=None, fetch=_get):
    """id воркфлоу по объявленному имени. None — не найден."""
    d = fetch(f"{API}/repos/{repo}/actions/workflows?per_page=100", token)
    if not d or "workflows" not in d:
        return None
    for w in d["workflows"]:
        if w.get("name") == workflow_name:
            return w.get("id")
    return None


def last_deploy(repo, workflow_name, token=None, fetch=_get):
    """sha последнего УСПЕШНОГО прогона воркфлоу деплоя. None — не выяснено.

    Воркфлоу опознаётся по ИМЕНИ ИЗ ЕГО ОПИСАНИЯ, а не по заголовку прогона.
    Это не педантизм: заголовок прогона задаётся полем run-name и живёт
    своей жизнью — у клиента он выглядит как «goswami-ingest · осталось: 19»
    и с именем воркфлоу не совпадает никогда. Сверка по заголовку молча не
    находила бы деплой всегда, и департамент считал бы, что прода нет.

    Поэтому два шага: имя → id воркфлоу, id → его последний успешный прогон.
    """
    if not workflow_name:
        return None
    wid = workflow_id(repo, workflow_name, token, fetch)
    if not wid:
        return None
    d = fetch(f"{API}/repos/{repo}/actions/workflows/{wid}/runs"
              f"?status=success&per_page=1", token)
    if not d or not d.get("workflow_runs"):
        return None
    return d["workflow_runs"][0].get("head_sha")


def last_deployment(repo, environment="Production", token=None, fetch=_get):
    """sha последнего УСПЕШНОГО деплоя, объявленного записью Deployments.

    Не всякий проект деплоится из GitHub Actions. Внешние площадки — Vercel,
    Netlify, Render — воркфлоу не заводят вовсе: они отмечаются в самом
    репозитории записью Deployments и статусом `success`. Для таких проектов
    путь через воркфлоу не находит НИЧЕГО НИКОГДА, и департамент молча считал
    бы, что прода нет. Молчание читается как чистота — а это ЗКН-Э001.

    Поэтому источник деплоя объявлен в паспорте полем `deploy_source`:
    `actions` (по умолчанию, воркфлоу) либо `deployments` (внешняя площадка).
    Здесь второй путь: свежие записи среды → первая, у которой есть успешный
    статус. Записей без успеха у Vercel много (сборка упала, превью) — берётся
    именно успешная, иначе департамент пошёл бы смотреть несуществующий прод.
    """
    d = fetch(f"{API}/repos/{repo}/deployments?per_page=50", token)
    if not isinstance(d, list) or not d:
        return None
    want = (environment or "Production").strip().lower()
    for dep in d:
        # Среда сверяется НАЧАЛОМ имени, а не равенством. Vercel называет её
        # «Production – имя-проекта» (с тире и именем), Netlify — своим
        # словом. Точное равенство не совпало бы никогда, и департамент
        # молча решил бы, что прода нет. Начало отличает прод от превью:
        # «Preview – имя» с «production» не начинается.
        env = str(dep.get("environment") or "").strip().lower()
        if not env.startswith(want):
            continue
        if not dep.get("id"):
            continue
        st = fetch(f"{API}/repos/{repo}/deployments/{dep['id']}/statuses"
                   f"?per_page=10", token)
        if isinstance(st, list) and any(s.get("state") == "success" for s in st):
            return dep.get("sha")
    return None


def _text(url, timeout=20):
    """Живая страница как текст. Никакой авторизации: прод открыт всем."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "billions-x-eyes",
        "Accept": "text/html,application/xhtml+xml"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(600000).decode("utf-8", "replace")
    except (urllib.error.URLError, ValueError, TimeoutError, OSError):
        return None


_ASSET = re.compile(r'(?:src|href)\s*=\s*["\']([^"\']*?/[^"\']*?'
                    r'[A-Za-z0-9_-]{8,}[^"\']*?\.(?:js|css|mjs))["\']')


def prod_fingerprint(url, fetch=_text):
    """Отпечаток собранного прода. БЕЗ ЕДИНОГО КЛЮЧА.

    Зачем путь. Свежесть через GitHub — и воркфлоу, и Deployments — упирается
    в доступ: приватный репозиторий чужим взглядом не виден, и департаменту
    пришлось бы держать ключ клиента. Ключ, который можно не выдавать, не
    выдают; ключ клиента департамент не держит вовсе.

    Прод при этом открыт всем. Сборщик подписывает файлы содержимым —
    `/_next/static/<build>/main-<hash>.js`, `assets/index-<hash>.css`. Новая
    сборка меняет эти имена, старая не меняет их никогда. Значит départament
    видит факт деплоя ИЗМЕРЕНИЕМ живого прода, а не рассказом о нём — и это
    сильнее источника: ключ может протухнуть, право отозваться, репозиторий
    закрыться, а прод остаётся тем, что видит пользователь.

    Отпечаток — sha256 отсортированного набора адресов сборки. Порядок в
    разметке не считается изменением: иначе перестановка тега читалась бы
    как деплой. Ни одного адреса не нашлось — None: врать нечем (ЗКН-Э001).
    """
    html = fetch(url)
    if not html:
        return None
    names = sorted(set(m.group(1) for m in _ASSET.finditer(html)))
    if not names:
        return None
    return hashlib.sha256("\n".join(names).encode("utf-8")).hexdigest()


def deploy_sha(p, token=None, fetch=_get, fetch_text=_text):
    """Отметка последнего деплоя — тем путём, который объявлен в паспорте.

    prod        — отпечаток живого прода, ключ не нужен (годится всем,
                  обязателен для приватного репозитория);
    deployments — запись GitHub Deployments (внешняя площадка, публичный репо);
    actions     — воркфлоу деплоя (как было).
    """
    src = p.get("source") or "actions"
    if src == "prod":
        return prod_fingerprint(p.get("prod") or "", fetch_text)
    if src == "deployments":
        return last_deployment(p["repo"], p.get("environment") or "Production",
                               token, fetch)
    return last_deploy(p["repo"], p.get("workflow", ""), token, fetch)


def read_state():
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def check(token=None, fetch=_get, state=None, items=None, fetch_text=_text):
    """Возвращает (список новых, снимок). Новый — тот, чья отметка разошлась.

    `items` — список проектов вместо реестра. Нужен суду: иначе исход суда
    зависел бы от того, каким путём деплоится ПЕРВЫЙ паспорт в реестре, и
    подключение нового проекта роняло бы суд, ничего в органе не сломав.
    """
    seen = read_state() if state is None else dict(state)
    fresh, snap = [], dict(seen)
    for p in (projects() if items is None else items):
        sha = deploy_sha(p, token, fetch, fetch_text)
        if not sha:
            continue
        snap[p["project"]] = sha
        # Первое знакомство деплоем НЕ считается: иначе установка органа
        # сама разбудила бы монитор по всем проектам разом и выдала бы
        # старый прод за свежий.
        if p["project"] in seen and seen[p["project"]] != sha:
            fresh.append({"project": p["project"], "repo": p.get("repo", ""),
                          "sha": sha, "was": seen[p["project"]]})
    return fresh, snap


def court():
    ok = True

    def chk(n, c):
        nonlocal ok
        ok = ok and bool(c)
        print(f"  {'✓' if c else '✗'} {n}")

    print("СУД · свежесть (департамент сам замечает деплой)")

    # Подделка отвечает и на список воркфлоу, и на прогоны — как живой API.
    def fake(sha, names=("Deploy Web (Cloudflare)", "Другой")):
        def f(url, token=None):
            if "/actions/workflows?" in url:
                return {"workflows": [{"name": n, "id": 100 + i}
                                      for i, n in enumerate(names)]}
            if "/runs" in url:
                return {"workflow_runs": ([{"head_sha": sha}] if sha else [])}
            # Подделка отвечает и за внешнюю площадку: суд снимка не должен
            # зависеть от того, каким путём деплоится ПЕРВЫЙ паспорт в
            # реестре. Иначе подключение нового проекта роняло бы суд.
            if "/deployments?" in url:
                return ([{"id": 7, "sha": sha, "environment": "Production"}]
                        if sha else [])
            if "/statuses" in url:
                return [{"state": "success"}]
            return None
        return f

    chk("воркфлоу опознаётся по ИМЕНИ ОПИСАНИЯ, а не по заголовку прогона",
        last_deploy("o/r", "Deploy Web (Cloudflare)", None, fake("bbb")) == "bbb")
    chk("заголовок прогона на опознание НЕ влияет",
        last_deploy("o/r", "Deploy Web (Cloudflare)", None,
                    fake("bbb", ("Deploy Web (Cloudflare)",))) == "bbb")
    chk("чужое имя воркфлоу → None, монитор впустую не будим",
        last_deploy("o/r", "Нет такого", None, fake("bbb")) is None)
    chk("пустое имя воркфлоу → None, гадать нечего",
        last_deploy("o/r", "", None, fake("bbb")) is None)
    chk("недоступный API не роняет орган",
        last_deploy("o/r", "x", None, lambda u, token=None: None) is None)
    chk("воркфлоу есть, успешных прогонов нет — None",
        last_deploy("o/r", "Deploy Web (Cloudflare)", None, fake(None)) is None)

    ps = projects()
    chk("реестр проектов читается из паспортов", isinstance(ps, list))
    chk("шаблон паспорта проектом не считается",
        all(p["project"] != "default" for p in ps))

    if True:
        # Проект суда — свой, не из реестра: исход не зависит от того, кто
        # подключён сегодня и каким путём он деплоится.
        name = "судебный"
        ps_c = [{"project": name, "repo": "o/r", "source": "actions",
                 "workflow": "Deploy Web (Cloudflare)", "prod": ""}]
        check_ = lambda st, fk: check(None, fk, state=st, items=ps_c)
        f1, s1 = check_({}, fake("bbb"))
        chk("ПЕРВОЕ знакомство деплоем не считается: монитор не будится",
            f1 == [] and s1.get(name) == "bbb")

        f2, s2 = check_(s1, fake("bbb"))
        chk("тот же sha — тишина, тяжёлый монитор не поднимается", f2 == [])

        f3, s3 = check_(s1, fake("ccc"))
        chk("новый sha — свежесть найдена, со старым для сверки",
            len(f3) == 1 and f3[0]["sha"] == "ccc" and f3[0]["was"] == "bbb")
        chk("снимок обновляется на новый sha", s3.get(name) == "ccc")

    # Внешняя площадка: записи Deployments + статусы, как у живого API.
    def fake_dep(rows, statuses):
        def f(url, token=None):
            if "/deployments?" in url:
                return rows
            if "/statuses" in url:
                did = int(url.split("/deployments/")[1].split("/")[0])
                return statuses.get(did, [])
            return None
        return f

    two = [{"id": 2, "sha": "new", "environment": "Production"},
           {"id": 1, "sha": "old", "environment": "Production"}]
    # Так среду называет Vercel на живом API: тире и имя проекта.
    vercel = [{"id": 3, "sha": "prev", "environment": "Preview – ui"},
              {"id": 2, "sha": "new", "environment": "Production – ui"},
              {"id": 1, "sha": "old", "environment": "Production – ui"}]
    ok_all = {1: [{"state": "success"}], 2: [{"state": "success"}],
              3: [{"state": "success"}]}
    chk("среда сверяется НАЧАЛОМ имени: «Production – ui» это прод",
        last_deployment("o/r", "Production", None,
                        fake_dep(vercel, ok_all)) == "new")
    chk("превью за прод НЕ выдаётся, даже если оно свежее",
        last_deployment("o/r", "Production", None,
                        fake_dep(vercel, ok_all)) != "prev")
    chk("чужая среда — None, монитор впустую не будим",
        last_deployment("o/r", "Staging", None,
                        fake_dep(vercel, ok_all)) is None)
    chk("имя среды без учёта регистра",
        last_deployment("o/r", "production", None,
                        fake_dep(vercel, ok_all)) == "new")
    chk("запись без имени среды продом не считается",
        last_deployment("o/r", "Production", None,
                        fake_dep([{"id": 9, "sha": "x"}],
                                 {9: [{"state": "success"}]})) is None)
    chk("внешняя площадка: берётся sha записи с успешным статусом",
        last_deployment("o/r", "Production", None,
                        fake_dep(two, {2: [{"state": "success"}],
                                       1: [{"state": "success"}]})) == "new")
    chk("упавшая сборка продом не считается — берём предыдущую успешную",
        last_deployment("o/r", "Production", None,
                        fake_dep(two, {2: [{"state": "failure"}],
                                       1: [{"state": "success"}]})) == "old")
    chk("ни одного успешного статуса — None, монитор впустую не будим",
        last_deployment("o/r", "Production", None,
                        fake_dep(two, {2: [{"state": "in_progress"}],
                                       1: [{"state": "error"}]})) is None)
    chk("записей нет — None, а не падение",
        last_deployment("o/r", "Production", None, fake_dep([], {})) is None)
    chk("недоступный API не роняет орган и на этом пути",
        last_deployment("o/r", "Production", None,
                        lambda u, token=None: None) is None)
    chk("паспорт выбирает путь: deployments идёт мимо воркфлоу",
        deploy_sha({"repo": "o/r", "source": "deployments",
                    "environment": "Production"}, None,
                   fake_dep(two, {2: [{"state": "success"}]})) == "new")
    chk("паспорт без deploy_source идёт прежним путём — воркфлоу",
        deploy_sha({"repo": "o/r", "workflow": "Deploy Web (Cloudflare)"},
                   None, fake("bbb")) == "bbb")
    chk("выключенный паспорт в реестр свежести не попадает",
        all(p["project"] != "default" for p in ps))

    # ── бесключевой путь: отпечаток живого прода ──
    build_a = ('<html><script src="/_next/static/AbCd1234xyz/main-9f3a11c2.js">'
               '</script><link href="/_next/static/css/7b2e44aa19.css"></html>')
    build_b = build_a.replace("9f3a11c2", "0011dead")
    swapped = ('<html><link href="/_next/static/css/7b2e44aa19.css">'
               '<script src="/_next/static/AbCd1234xyz/main-9f3a11c2.js">'
               '</script></html>')
    fa = prod_fingerprint("https://x/", lambda u: build_a)
    chk("отпечаток прода снимается БЕЗ КЛЮЧА, по живой странице",
        isinstance(fa, str) and len(fa) == 64)
    chk("та же сборка — тот же отпечаток, монитор не будится",
        prod_fingerprint("https://x/", lambda u: build_a) == fa)
    chk("новая сборка меняет отпечаток — деплой виден",
        prod_fingerprint("https://x/", lambda u: build_b) != fa)
    chk("перестановка тегов деплоем НЕ считается",
        prod_fingerprint("https://x/", lambda u: swapped) == fa)
    chk("страница без адресов сборки — None, врать нечем",
        prod_fingerprint("https://x/", lambda u: "<html>привет</html>") is None)
    chk("прод недоступен — None, а не падение",
        prod_fingerprint("https://x/", lambda u: None) is None)
    chk("паспорт выбирает бесключевой путь мимо GitHub целиком",
        deploy_sha({"source": "prod", "prod": "https://x/"}, None,
                   lambda u, token=None: None, lambda u: build_a) == fa)
    chk("приватность репозитория бесключевому пути безразлична",
        deploy_sha({"source": "prod", "prod": "https://x/", "repo": ""}, None,
                   lambda u, token=None: None, lambda u: build_a) == fa)

    chk("битый снимок читается как пустой, а не роняет орган",
        isinstance(read_state(), dict))
    chk("ключ доступа органу НЕ НУЖЕН: репозитории публичные",
        last_deploy("o/r", "Deploy Web (Cloudflare)", None, fake("bbb")) == "bbb")

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()

    # Ключа департамент не держит. Встроенный ключ прогона берётся лишь
    # затем, чтобы не упереться в лимит анонимных запросов; проект, чей
    # репозиторий закрыт, смотрится бесключевым путём (deploy_source: prod).
    fresh, snap = check(os.environ.get("GITHUB_TOKEN"))
    if a.write:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(snap, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    for f in fresh:
        print(f"СВЕЖИЙ ДЕПЛОЙ · {f['project']} · {f['sha'][:9]} "
              f"(было {f['was'][:9]})")
    if not fresh:
        print("нового деплоя нет — монитор не поднимаем")
    # Вывод для воркфлоу.
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a", encoding="utf-8") as f:
            f.write(f"new={'true' if fresh else 'false'}\n")
            if fresh:
                f.write(f"sha={fresh[0]['sha']}\n")
                f.write(f"repo={fresh[0]['repo']}\n")
    return 0 if fresh else 1


if __name__ == "__main__":
    sys.exit(main())
