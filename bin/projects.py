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
