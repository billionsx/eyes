#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ПЕРЕСБОРКА. Разводит хранимое и выводимое.

Зачем орган. У департамента два рода файлов, и до сих пор они лежали
вперемешку:

  ХРАНИМОЕ — то, чего нельзя восстановить, если потерять:
      registry/corpus/            склад страниц Apple
      registry/library/*.jsonl    законы
      registry/standards/tokens.json   измеренная база
      registry/standards/symbols/      перечень глифов с macOS-плеча

  ВЫВОДИМОЕ — то, что пересобирается из хранимого за секунду:
      registry/standards/palette.json     ← законы образцов
      registry/standards/typescale.json   ← таблицы типографики
      registry/standards/devices.json     ← таблицы устройств

Смешение стоило дорого. Ежедневный работник переписывал выводимое каждым
прогоном, и оно конфликтовало с любой правкой в тот же день. Разрешать
конфликт СЛИЯНИЕМ выводимого бессмысленно: у него нет своей истины, вся
истина в источнике. Верный ответ на конфликт — пересобрать.

Второе, что даёт разведение: СНОС. Если выводимый файл в репозитории не
совпадает с тем, что даёт пересборка, значит его правили руками. Правка
руками выводимого — тихая порча: она переживёт один прогон и умрёт на
следующем, а между ними департамент будет судить по числу, которого нет
в источнике.

Приложения:
    python3 bin/rebuild.py           — пересобрать выводимое
    python3 bin/rebuild.py --check   — снос: расходится ли с источником
    python3 bin/rebuild.py --court
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin"
STD = ROOT / "registry" / "standards"

# Выводимое объявлено списком: файл → чем пересобирается. Угадывать
# «похоже на выводимое» нельзя — однажды под снос попадёт измеренная база.
DERIVED = (
    ("palette.json", ["palette.py", "--write"]),
    ("typescale.json", ["typescale.py", "--write"]),
    ("devices.json", ["devices.py", "--write"]),
)


def rebuild(one=None):
    """Пересобирает выводимое. Возвращает [(файл, ок, вывод)]."""
    out = []
    for name, cmd in DERIVED:
        if one and name != one:
            continue
        r = subprocess.run([sys.executable, str(BIN / cmd[0])] + cmd[1:],
                           capture_output=True, text=True, cwd=str(ROOT))
        out.append((name, r.returncode == 0, (r.stdout or r.stderr)[-200:]))
    return out


def _load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def check():
    """Снос: сравнивает лежащее с пересобранным. Возвращает список расхождений."""
    drift = []
    before = {n: _load(STD / n) for n, _ in DERIVED}
    rebuild()
    for name, _ in DERIVED:
        after = _load(STD / name)
        if before[name] is None and after is not None:
            drift.append({"file": name, "why": "файла не было — собран заново"})
        elif before[name] != after:
            drift.append({"file": name,
                          "why": "лежащее не совпадает с выводимым из "
                                 "источника — правили руками либо источник "
                                 "изменился"})
    return drift


def court():
    ok = True

    def chk(n, c):
        nonlocal ok
        ok = ok and bool(c)
        print(f"  {'✓' if c else '✗'} {n}")

    print("СУД · пересборка (хранимое против выводимого)")

    chk("выводимое объявлено списком, а не угадывается",
        {n for n, _ in DERIVED} == {"palette.json", "typescale.json",
                                    "devices.json"})
    chk("измеренная база в выводимое НЕ входит: её нельзя пересобрать",
        "tokens.json" not in {n for n, _ in DERIVED})
    chk("склад и библиотека в выводимое НЕ входят",
        not any("corpus" in n or "library" in n for n, _ in DERIVED))

    res = rebuild()
    chk("все выводимые своды пересобираются", all(o for _n, o, _t in res))
    chk("пересобрано ровно объявленное", len(res) == len(DERIVED))

    # Определённость: два прогона подряд обязаны дать один и тот же файл.
    # Недетерминированная пересборка порождала бы вечный «снос» на пустом
    # месте и обесценила бы саму проверку.
    snap1 = {n: _load(STD / n) for n, _ in DERIVED}
    rebuild()
    snap2 = {n: _load(STD / n) for n, _ in DERIVED}
    chk("пересборка ОПРЕДЕЛЁННАЯ: два прогона дают один результат",
        snap1 == snap2)

    chk("после пересборки сноса нет", check() == [])

    # Порча руками обязана быть замечена.
    victim = STD / "palette.json"
    keep = victim.read_text(encoding="utf-8")
    d = json.loads(keep)
    d.setdefault("gray", {}).setdefault("systemGray6", {})["light"] = "#DEADBE"
    victim.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    dr = check()
    chk("правка выводимого РУКАМИ ловится сносом",
        any(x["file"] == "palette.json" for x in dr))
    chk("после сноса файл восстановлен из источника",
        _load(victim)["gray"]["systemGray6"]["light"] != "#DEADBE")

    chk("одиночная пересборка берёт только названное",
        len(rebuild("devices.json")) == 1)

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()
    if a.court:
        return court()
    if a.check:
        dr = check()
        if not dr:
            print("сноса нет: выводимое совпадает с источником")
            return 0
        for x in dr:
            print(f"СНОС · {x['file']}: {x['why']}")
        return 1
    for name, ok_, tail in rebuild():
        print(f"  {'✓' if ok_ else '✗'} {name}")
        if not ok_:
            print("    ", tail.strip()[:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
