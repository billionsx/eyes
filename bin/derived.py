#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ПРОИЗВОДНЫЕ ФАЙЛЫ (ст. 54).

Зачем орган. Хроника отказывается выбирать сторону в столкновении — и права:
03.08.2026 стратегия «оставить свою сторону» молча стёрла из суда чужие
проверки, и суд остался зелёным, потому что краснеть стало нечему. Правило
верное, но оно оказалось СЛИШКОМ ШИРОКИМ.

Столкновение бывает двух разных родов:

  · в ИСТОЧНИКЕ — файл написан руками, другой стороны не восстановить.
    Выбирать сторону молча нельзя, и хроника обязана остановиться;
  · в ПРОИЗВОДНОМ — файл собирается прогоном из источника. Терять там нечего:
    достаточно пересобрать. Останавливать запись из-за него значит терять
    ДОКУМЕНТ ОБ ОТКАЗЕ ровно тогда, когда он нужнее всего.

05.08.2026 это и случилось: суд в CI упал, отказ положил свои красные строки в
реестр — и хроника не смогла их записать из-за столкновения в перегенерируемом
эфире. Диагноз погиб от столкновения в файле, который пересобирается одной
командой.

Орган объявляет, ЧТО производно и ЧЕМ пересобирается. Список поимённый: глухое
«всё в этой папке производно» однажды проглотит источник.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# путь → команда пересборки. Пустая команда: файл пересоберётся следующим
# прогоном своего органа, и терять в нём нечего.
DERIVED = {
    "dashboard/DASHBOARD.md": "python3 bin/dashboard.py",
    "dashboard/data.json": "python3 bin/dashboard.py",
    "dashboard/index.html": "python3 bin/dashboard.py",
    "registry/state/SERVICE.md": "",
    "registry/state/SITE.md": "",
    "registry/state/COURT-LAST.md": "",
    "registry/screens/SCAN-appstore.json": "",
    "registry/state/keys.json": "",
    "registry/state/KEYS.md": "",
    "registry/state/CLIENTS.md": "",
    "registry/state/FRESH.json": "",
}


def is_derived(path: str) -> bool:
    return path.strip() in DERIVED


def all_derived(paths) -> bool:
    """Все ли столкнувшиеся пути производны. Пустой список — НЕ повод продолжать."""
    ps = [p for p in (paths or []) if str(p).strip()]
    return bool(ps) and all(is_derived(p) for p in ps)


def rebuild(paths) -> list:
    done = []
    for cmd in sorted({DERIVED[p.strip()] for p in paths
                       if is_derived(p) and DERIVED[p.strip()]}):
        subprocess.run(cmd, shell=True, cwd=str(ROOT), capture_output=True)
        done.append(cmd)
    return done


def court() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    print("СУД · производные файлы")
    chk("эфир объявлен производным и знает, чем пересобирается",
        is_derived("dashboard/data.json")
        and DERIVED["dashboard/data.json"].startswith("python3"))
    chk("ломаю → красный: ИСТОЧНИК производным не считается",
        not is_derived("bin/eyes.py") and not is_derived("CONSTITUTION.md")
        and not is_derived("registry/state/CHANGELOG.md"))
    chk("столкновение только в производных — запись продолжается",
        all_derived(["dashboard/data.json", "registry/state/CLIENTS.md"]))
    chk("хоть один источник в столкновении — запись останавливается",
        not all_derived(["dashboard/data.json", "bin/lint.py"]))
    chk("пустой список НЕ повод продолжать: не бывает столкновения ни в чём",
        not all_derived([]))
    chk("список поимённый, а не по папкам: глухое «всё в registry» "
        "проглотило бы конституцию департамента",
        not is_derived("registry/standards/tokens.json")
        and not is_derived("registry/lessons-exempt.json"))
    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--court":
        sys.exit(court())
    if a and a[0] == "--check":
        paths = [p for p in a[1:] if p.strip()]
        if all_derived(paths):
            rebuild(paths)
            sys.exit(0)
        sys.exit(1)
    print("\n".join(f"{k}\t{v or '(пересоберётся своим органом)'}"
                    for k, v in sorted(DERIVED.items())))
