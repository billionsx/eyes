#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · РЕЕСТР ПОДКЛЮЧЁННЫХ ПРОЕКТОВ (ст. 57).

Департамент автономен: он не знает ни одного проекта в коде. Всё, что он
знает о проекте, лежит в `adapters/<имя>.json` — это единственный паспорт
подключения. Здесь только чтение этого паспорта, ни одного имени проекта
в исходниках.

Паспорт (поля сверх правил линта):
  project        имя (совпадает с именем файла)
  repo           "owner/name" — репозиторий проекта (для обхода в CI)
  prod           корень прода (для живого взгляда и монитора)
  live_pages     страницы живого взгляда (если пусто — берётся prod)
  deploy_workflow имя воркфлоу деплоя проекта (для сцепки монитора)
  enabled        false → паспорт есть, но департамент проект не трогает

Выбор проекта по умолчанию: переменная окружения EYES_PROJECT → файл
adapters/DEFAULT (одна строка с именем) → единственный включённый паспорт
→ adapters/default.json.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def all_adapters(root: Path = None) -> dict:
    """Все паспорта: имя → словарь. Порядок — алфавитный, детерминированный."""
    root = root or ROOT
    out = {}
    d = root / "adapters"
    if not d.exists():
        return out
    for f in sorted(d.glob("*.json")):
        a = _read(f)
        if isinstance(a, dict):
            a.setdefault("project", f.stem)
            out[f.stem] = a
    return out


def enabled(root: Path = None) -> dict:
    """Паспорта, которые департамент обслуживает (enabled != false, не default)."""
    return {k: v for k, v in all_adapters(root).items()
            if v.get("enabled", True) and k != "default"}


def default_name(root: Path = None) -> str:
    root = root or ROOT
    env = os.environ.get("EYES_PROJECT")
    if env:
        return env
    f = root / "adapters" / "DEFAULT"
    if f.exists():
        n = f.read_text(encoding="utf-8").strip()
        if n:
            return n
    en = enabled(root)
    if len(en) == 1:
        return next(iter(en))
    return "default"


def pick(root: Path = None, name: str = None) -> dict:
    """Паспорт проекта, с которым идёт работа. Никогда не падает: default.json —
    нейтральный паспорт, он есть в репозитории всегда."""
    root = root or ROOT
    ads = all_adapters(root)
    n = name or default_name(root)
    if n in ads:
        return ads[n]
    if "default" in ads:
        return ads["default"]
    return {"project": n, "report": {"globs": [], "rules": []}, "strict": {"globs": [], "rules": []}}


def client_pick(root: Path = None, name: str = None, globs: list = None,
                report_rules: list = None, strict_rules: list = None) -> dict:
    """Паспорт для КЛИЕНТСКОГО пути (reusable-воркфлоу M1/M7).

    Клиент кладёт себе десять строк, называет себя в `project:` и перечисляет
    глобы. До сих пор оба входа (ревью PR и надзор по коммиту) синтезировали
    паспорт на лету из этих двух полей — и паспорт проекта в `adapters/`
    на клиентском пути НЕ ДЕЙСТВОВАЛ: ни `pt_to_css_px`, ни `allow_extra`,
    ни свой набор правил, ни строгие гейты. Паспорт был, но не правил.

    Порядок: имя названо и паспорт есть → правит ПАСПОРТ; глобы из воркфлоу
    лишь уточняют, где смотреть. Имени в реестре нет → синтез как раньше:
    неизвестный проект подключается без нашего участия и получает совет.

    Строгие глобы синтезом НЕ выдаются и в паспорте не подменяются, если их
    там нет: право вето включается решением основателя (ст. 7.4), а не тем,
    что клиент вписал строку в свой воркфлоу.

    `enabled: false` — паспорт есть, но департамент проект не обслуживает.
    Такой ответ помечается ключом `_disabled`, чтобы вызывающий сказал это
    вслух: молчание читается как чистота (ЗКН-Э001).
    """
    root = root or ROOT
    if name is None:
        name = os.environ.get("EYES_CLIENT_PROJECT", "")
    name = (name or "").strip()
    if globs is None:
        globs = [g.strip() for g in
                 os.environ.get("EYES_CLIENT_GLOBS", "").split(",") if g.strip()]
    globs = list(globs or [])

    ad = all_adapters(root).get(name) if name and name != "default" else None
    if ad is not None:
        ad = json.loads(json.dumps(ad))          # копия: паспорт на диске цел
        if ad.get("enabled", True) is False:
            ad["_disabled"] = True
            ad["report"] = {"globs": [], "rules": []}
            ad["strict"] = {"globs": [], "rules": []}
            return ad
        if globs:
            ad.setdefault("report", {})["globs"] = list(globs)
            st = ad.setdefault("strict", {})
            if st.get("globs"):                  # были строгие — там же и смотрим
                st["globs"] = list(globs)
        return ad

    return {"project": name or "client",
            "report": {"globs": globs, "rules": list(report_rules or [])},
            "strict": {"globs": list(globs) if strict_rules else [],
                       "rules": list(strict_rules or [])}}


def live_pages(root: Path = None) -> list:
    """Страницы живого взгляда: сначала явный список в live-sources.json
    (совместимость), затем live_pages/prod всех включённых паспортов."""
    root = root or ROOT
    pages, seen = [], set()
    cfg = _read(root / "registry" / "live-sources.json") or {}
    for u in cfg.get("pages", []) or []:
        if u not in seen:
            pages.append(u); seen.add(u)
    for a in enabled(root).values():
        for u in (a.get("live_pages") or ([a["prod"]] if a.get("prod") else [])):
            if u not in seen:
                pages.append(u); seen.add(u)
    return pages


if __name__ == "__main__":
    ads = all_adapters()
    print(f"паспортов: {len(ads)} · обслуживается: {len(enabled())} · "
          f"по умолчанию: {default_name()}")
    for k, v in ads.items():
        mark = "·" if v.get("enabled", True) and k != "default" else "○"
        print(f"  {mark} {k}: repo={v.get('repo','—')} prod={v.get('prod','—')} "
              f"globs={len((v.get('report') or {}).get('globs', []))}")
    print("страниц живого взгляда:", len(live_pages()))
