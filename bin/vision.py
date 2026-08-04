#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ОТПЕЧАТОК ЗРЕНИЯ (ст. 43).

Зачем орган. Храповик держит долг клиента: вырос — красный. Правило верное,
но у него был слепой шов. Долг может вырасти по двум РАЗНЫМ причинам:

  1. клиент написал новое нарушение — это регрессия клиента;
  2. департамент стал видеть больше — новое правило, новый разборщик, новый
     замер в базе. Код клиента при этом не менялся ни на строку.

Обе причины давали один и тот же вердикт «🔴 КЛИЕНТ · долг вырос». 04.08.2026
это поймали на живом: код ISKCON от 01.08 и от 04.08 дал ОДИНАКОВЫЕ 774
находки, а храповик объявил регрессию клиента и красил сборку третьи сутки.
Инструмент, ошибающийся в адресате обвинения, теряет ровно то, ради чего
существует.

Что делает орган. Снимает отпечаток ТОГО, ЧТО ДЕПАРТАМЕНТ СПОСОБЕН УВИДЕТЬ,
и кладёт его рядом с базой долга. Дальше храповик сравнивает два отпечатка:

  отпечаток тот же + долг вырос  → виноват клиент, красный по адресу;
  отпечаток другой + долг вырос  → приписывать НЕКОМУ. Храповик отказывается
                                   обвинять и требует осознанного пересчёта
                                   базы с записью в хронике (ст. 43);
  отпечаток другой + роста нет   → база и отпечаток обновляются молча:
                                   обвинять не в чем.

ИЗ ЧЕГО ОТПЕЧАТОК. Не из версии, объявленной руками, — объявление стареет
молча, и первый же тихо добавленный разборщик обошёл бы защиту. Отпечаток
ПОВЕДЕНЧЕСКИЙ: линт прогоняется по замороженному эталонному корпусу
`tests/fixtures/vision/` полным набором правил, и хэшируется весь его
вердикт — правило, файл, строка, текст с числом. Меняется что угодно из
списка ниже — меняется отпечаток:

  · добавилось или изменилось правило AE;
  · разборщик научился читать новый язык или новую запись (utility-классы,
    встроенный стиль, переменные CSS);
  · изменилось ЧИСЛО в измеренной базе — потому что вердикт несёт число.

Последнее особенно важно: еженедельный замер геометрии двигает базу, и после
такого сдвига рост долга — тоже не вина клиента.

Комментарий, переименование переменной и перестановка строк внутри `lint.py`
отпечаток НЕ трогают: они не меняют того, что департамент видит.

Эталонный корпус заморожен. Правка любого файла в `tests/fixtures/vision/`
меняет отпечаток и требует пересчёта баз — это цена честности и она осознанная.
"""
import hashlib
import json
import sys
from pathlib import Path

BIN = Path(__file__).resolve().parent
ROOT = BIN.parent
sys.path.insert(0, str(BIN))
import lint as lint_mod  # noqa: E402

CORPUS = ROOT / "tests" / "fixtures" / "vision"
VISION_FILE = ROOT / "registry" / "state" / "ae-vision.json"
ALL_RULES = [f"AE{i}" for i in range(1, 21)]


def fingerprint(root: Path = None, corpus: Path = None,
                tokens: dict = None) -> str:
    """Отпечаток зрения департамента: 12 знаков sha256 от полного вердикта
    линта на замороженном корпусе."""
    root = root or ROOT
    corpus = corpus or CORPUS
    if tokens is None:
        tokens = json.loads((root / "registry" / "standards" / "tokens.json")
                            .read_text(encoding="utf-8"))
    ad = {"report": {"globs": ["**/*"], "rules": list(ALL_RULES)},
          "strict": {"globs": [], "rules": []},
          "allow_extra": [], "sizes_extra": [], "pt_to_css_px": 1}
    res = lint_mod.run(root, ad, tokens, "report", corpus)
    rows = sorted(f"{r}|{rel}|{line}|{msg}"
                  for r, rel, line, msg in res["findings"])
    # Набор объявленных правил входит отдельно: правило, которое пока ничего
    # не находит на корпусе, всё равно есть в зрении, и его появление обязано
    # быть видно.
    body = "\n".join(rows) + "\n#правила:" + ",".join(sorted(res.get("rules", [])))
    return hashlib.sha256(body.encode()).hexdigest()[:12]


def load() -> dict:
    if VISION_FILE.exists():
        try:
            return json.loads(VISION_FILE.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    return {}


def save(d: dict):
    VISION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VISION_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=1,
                                      sort_keys=True) + "\n", encoding="utf-8")


def known(adapter: str) -> str:
    return (load().get("adapters") or {}).get(adapter, "")


def remember(adapter: str, fp: str):
    d = load()
    d.setdefault("adapters", {})[adapter] = fp
    d["_смысл"] = ("Отпечаток того, ЧТО департамент способен увидеть. Рядом с "
                   "базой долга он отвечает на вопрос, чья вина в росте: "
                   "клиента или расширившегося зрения (ст. 43).")
    save(d)


if __name__ == "__main__":
    fp = fingerprint()
    print(f"отпечаток зрения: {fp}")
    d = load().get("adapters") or {}
    for k in sorted(d):
        mark = "=" if d[k] == fp else "≠"
        print(f"  {mark} {k}: {d[k]}")
