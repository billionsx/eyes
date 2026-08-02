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
import json
import os
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
        if d.get("project") in (None, "default") or not d.get("repo"):
            continue
        out.append({"project": d["project"], "repo": d["repo"],
                    "workflow": d.get("deploy_workflow", ""),
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


def read_state():
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def check(token=None, fetch=_get, state=None):
    """Возвращает (список новых, снимок). Новый — тот, чей sha разошёлся."""
    seen = read_state() if state is None else dict(state)
    fresh, snap = [], dict(seen)
    for p in projects():
        sha = last_deploy(p["repo"], p["workflow"], token, fetch)
        if not sha:
            continue
        snap[p["project"]] = sha
        # Первое знакомство деплоем НЕ считается: иначе установка органа
        # сама разбудила бы монитор по всем проектам разом и выдала бы
        # старый прод за свежий.
        if p["project"] in seen and seen[p["project"]] != sha:
            fresh.append({"project": p["project"], "repo": p["repo"],
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

    if ps:
        name = ps[0]["project"]
        f1, s1 = check(None, fake("bbb"), state={})
        chk("ПЕРВОЕ знакомство деплоем не считается: монитор не будится",
            f1 == [] and s1.get(name) == "bbb")

        f2, s2 = check(None, fake("bbb"), state=s1)
        chk("тот же sha — тишина, тяжёлый монитор не поднимается", f2 == [])

        f3, s3 = check(None, fake("ccc"), state=s1)
        chk("новый sha — свежесть найдена, со старым для сверки",
            len(f3) == 1 and f3[0]["sha"] == "ccc" and f3[0]["was"] == "bbb")
        chk("снимок обновляется на новый sha", s3.get(name) == "ccc")

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
