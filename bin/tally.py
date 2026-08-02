#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ЖИЗНЬ ПРАВИЛА (реестр присутствия).

Зачем орган. Департамент до сих пор учился в одну сторону: обходил
документацию Apple и выводил нормы. Но у правила есть вторая жизнь — как оно
ведёт себя, когда его применяют. Правило, срабатывающее у всех, — кандидат
в норму по умолчанию. Правило, не срабатывающее нигде, — вопрос, на который
департамент обязан себе ответить.

ГРАНИЦА, КОТОРУЮ ОРГАН НЕ ПЕРЕСТУПАЕТ. Клиенту объявлено: код никуда не
уходит, сеть серверу не нужна и он в неё не ходит. Обещание связывает.
Поэтому журнал:

  · пишется ТОЛЬКО на машину клиента (var/presence.jsonl рядом с сервером);
  · содержит номер правила, отметку времени, язык фрагмента и метку сеанса —
    и НИЧЕГО БОЛЬШЕ. Ни строки кода, ни имени файла, ни пути, ни причины
    находки (причина цитирует значение из кода и потому запрещена);
  · никуда не отправляется. Департамент увидит его, только если клиент сам
    пришлёт сводку;
  · выключается одним EYES_NO_JOURNAL=1.

Телеметрия, тайком уносящая код, дала бы департаменту больше данных и
уничтожила бы то единственное, чем локальный сервер ценен юрлицу с NDA.
Обмен невыгодный, и он не рассматривается.

ЧЕСТНОСТЬ О МОЛЧАНИИ. Молчащее правило имеет ДВА объяснения: оно бесполезно
или оно работает как сдерживание — разработчик не пишет запрещённого, потому
что знает о запрете. Журнал их не различает, и орган не делает вид, что
различает: он предъявляет молчание как ВОПРОС, а не как приговор.

Запуск:
    python3 bin/tally.py              — свод жизни правил
    python3 bin/tally.py --digest     — сводка для отправки (без кода)
    python3 bin/tally.py --forget     — стереть журнал
    ... | python3 bin/tally.py --ingest [--lang css]
                                      — принять срабатывания с потока
                                        (номера правил по одному в строке);
                                        так журнал кормит гейт и монитор,
                                        а не только присутствие
    python3 bin/tally.py --court
"""
import argparse
import json
import os
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = Path(os.environ.get("EYES_JOURNAL", ROOT / "var" / "presence.jsonl"))

# Полный набор правил департамента. Объявлен здесь, а не выведен из журнала:
# орган обязан знать о правиле, которое ни разу не сработало, — иначе
# молчание невидимо, а именно оно и есть предмет разбора.
RULES = [f"AE{i}" for i in range(1, 16)]

# Метка сеанса живёт в памяти процесса и умирает вместе с ним. Она нужна,
# чтобы отличить «правило сработало 500 раз в одном файле» от «правило
# срабатывает у всех» — без неё один шумный проект перевесит десять тихих.
SESSION = uuid.uuid4().hex[:12]

# Разрешённые поля записи. Список закрытый: если однажды кто-то добавит
# в запись «why» или «file», суд обязан это поймать.
ALLOWED = {"ts", "rule", "lang", "session", "scope", "kind"}


def enabled():
    return os.environ.get("EYES_NO_JOURNAL", "").strip() not in ("1", "true", "yes")


def record(rules, lang="css", journal=None, session=None, scope=None):
    """Записывает СРАБОТАВШИЕ правила и, если известен, ОХВАТ наблюдения.

    Охват — те правила, что были включены в этом прогоне. Без него молчание
    правила неразличимо надвое: «не сработало» и «не запускалось» выглядят
    одинаково, и департамент отправил бы на пересмотр правило, которое ни
    разу не работало. Та же ошибка, что обрезанный долг в формуле балла:
    две разные вещи, сведённые в одно число.

    Пустой список срабатываний записи о правилах не даёт — журнал о жизни
    ПРАВИЛ, а не о числе обращений; но охват пишется и при чистом прогоне:
    «правило работало и промолчало» — самое ценное наблюдение из всех.
    """
    if not enabled():
        return 0
    j = Path(journal) if journal else JOURNAL
    if not rules and not scope:
        return 0
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sid = session or SESSION
    lines = [json.dumps({"ts": ts, "rule": r, "lang": lang, "session": sid},
                        ensure_ascii=False) for r in rules]
    if scope:
        lines.append(json.dumps(
            {"ts": ts, "kind": "scope", "session": sid, "lang": lang,
             "scope": sorted(set(scope), key=lambda x: int(x[2:]))},
            ensure_ascii=False))
    try:
        j.parent.mkdir(parents=True, exist_ok=True)
        with j.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except OSError:
        # Журнал — удобство, а не обязанность. Невозможность писать не
        # имеет права ронять проверку кода: клиент пришёл за вердиктом.
        return 0
    return len(lines)


def read(journal=None):
    j = Path(journal) if journal else JOURNAL
    if not j.exists():
        return []
    out = []
    for line in j.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if isinstance(d, dict) and (d.get("rule") or d.get("kind") == "scope"):
            out.append(d)
    return out


def leaked(entries):
    """Поля сверх разрешённых. Пустой список — журнал чист.

    Это НЕ проверка чужого файла, это самопроверка обещания: если однажды
    в запись просочится путь или строка кода, орган обязан сказать об этом
    громко, а не хранить это молча.
    """
    extra = set()
    for e in entries:
        extra |= set(e) - ALLOWED
    return sorted(extra)


def life(entries):
    """Жизнь каждого правила: срабатываний, сеансов, охвата, языков."""
    fired = [e for e in entries if e.get("rule")]
    hits = Counter(e["rule"] for e in fired)
    sess = defaultdict(set)
    langs = defaultdict(set)
    for e in fired:
        sess[e["rule"]].add(e.get("session", "?"))
        langs[e["rule"]].add(e.get("lang", "?"))
    ran = defaultdict(set)
    for e in entries:
        if e.get("kind") == "scope":
            for r in e.get("scope", []):
                ran[r].add(e.get("session", "?"))
    return [{"rule": r, "hits": hits.get(r, 0),
             "sessions": len(sess.get(r, ())),
             "ran": len(ran.get(r, ())),
             "langs": sorted(langs.get(r, ()))}
            for r in RULES]


def render(rows, entries):
    total = sum(r["hits"] for r in rows)
    # Молчание надвое. Правило, ни разу не включённое, вопроса не задаёт —
    # о нём попросту ничего не известно, и выдавать его на пересмотр значит
    # судить по отсутствию улик как по уликам.
    quiet = [r["rule"] for r in rows if r["hits"] == 0 and r["ran"] > 0]
    unseen = [r["rule"] for r in rows if r["hits"] == 0 and r["ran"] == 0]
    wide = sorted((r for r in rows if r["sessions"] >= 2),
                  key=lambda r: (-r["sessions"], -r["hits"]))

    L = ["# ЖИЗНЬ ПРАВИЛА · реестр присутствия",
         "",
         "Журнал ведётся ТОЛЬКО на машине, где стоит сервер. В записи — "
         "номер правила, время, язык фрагмента и метка сеанса. Ни строки "
         "кода, ни имени файла, ни причины находки. Никуда не отправляется.",
         ""]

    bad = leaked(entries)
    if bad:
        L += ["> **ЖУРНАЛ ЗАГРЯЗНЁН.** В записях найдены поля сверх "
              f"разрешённых: {', '.join(bad)}. Обещание клиенту нарушено — "
              "чинить прежде всего остального.", ""]

    L += [f"Срабатываний всего: **{total}** · сеансов: "
          f"**{len({e.get('session') for e in entries})}**", "",
          "| правило | срабатываний | сеансов | включалось | языки |",
          "|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda x: (-x["hits"], x["rule"])):
        L.append(f"| {r['rule']} | {r['hits']} | {r['sessions']} | "
                 f"{r['ran']} | {', '.join(r['langs']) or '—'} |")

    L += ["", "## Кандидаты в норму по умолчанию", ""]
    if wide:
        L.append("Правила, срабатывающие БОЛЕЕ ЧЕМ В ОДНОМ сеансе, — то есть "
                 "не особенность одного проекта:")
        L += [f"- **{r['rule']}** — {r['sessions']} сеансов, {r['hits']} "
              f"срабатываний" for r in wide]
    else:
        L.append("Пока нет: журнал ещё не видел двух разных сеансов. "
                 "Вывод о распространённости на одном сеансе — не вывод.")

    L += ["", "## Молчание", ""]
    if quiet:
        L += ["Правило РАБОТАЛО и ни разу не сработало: " + ", ".join(quiet)
              + ".",
              "",
              "Только это и есть вопрос. У него ДВА объяснения, и журнал их "
              "не различает:",
              "",
              "1. правило бесполезно — предмета в живом коде не бывает;",
              "2. правило работает СДЕРЖИВАНИЕМ — запрещённого не пишут, "
              "потому что знают о запрете.",
              "",
              "Различить можно только снятием правила и наблюдением, "
              "появится ли нарушение. Это решение основателя (ст. 7.4), "
              "и орган его не принимает."]
    else:
        L.append("Правил, что работали и промолчали, нет.")

    if unseen:
        L += ["", "## Не наблюдалось", "",
              "Ни разу не включалось ни в одном прогоне: "
              + ", ".join(unseen) + ".",
              "",
              "Это НЕ кандидаты на пересмотр. О них не известно ничего: "
              "правило, которое не запускали, не молчит — его не спрашивали. "
              "Судить по отсутствию улик как по уликам департамент себе не "
              "позволяет. Чтобы вопрос стал вопросом, правило нужно включить "
              "в охват адаптера."]
    return "\n".join(L) + "\n"


def digest(entries):
    """Сводка для добровольной отправки в департамент.

    Отдаётся ТОЛЬКО агрегат: правило → сколько сеансов. Ни времени, ни
    последовательности, ни языка — по ним восстанавливается рабочий день
    человека, а это уже наблюдение за разработчиком, а не за правилом.
    """
    sess = defaultdict(set)
    for e in entries:
        sess[e["rule"]].add(e.get("session", "?"))
    return {"schema": "eyes-presence-digest/1",
            "rules": {r: len(sess.get(r, ())) for r in RULES if sess.get(r)},
            "sessions": len({e.get("session") for e in entries})}


def court():
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    print("СУД · жизнь правила (реестр присутствия)")

    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="eyes-tally-")) / "p.jsonl"

    chk("пустая находка записи не даёт: журнал о правилах, не об обращениях",
        record([], "css", tmp) == 0)
    chk("несуществующий журнал читается как пустой", read(tmp) == [])

    record(["AE1", "AE2"], "css", tmp, session="s1")
    record(["AE1"], "tsx", tmp, session="s2")
    record(["AE1"], "css", tmp, session="s2")
    e = read(tmp)
    chk("записи легли: три правила в двух сеансах", len(e) == 4)

    chk("В ЗАПИСИ НЕТ НИЧЕГО СВЕРХ РАЗРЕШЁННОГО", leaked(e) == [])
    chk("посторонняя запись ловится самопроверкой",
        leaked(e + [{"rule": "AE1", "file": "src/app.tsx"}]) == ["file"])

    rows = {r["rule"]: r for r in life(e)}
    chk("срабатывания считаются", rows["AE1"]["hits"] == 3)
    chk("СЕАНСЫ считаются отдельно от срабатываний: 3 удара, 2 сеанса",
        rows["AE1"]["sessions"] == 2)
    chk("правило одного сеанса не выдаётся за распространённое",
        rows["AE2"]["sessions"] == 1)
    chk("языки собраны", rows["AE1"]["langs"] == ["css", "tsx"])

    chk("молчащее правило ВИДНО, хотя его в журнале нет",
        rows["AE7"]["hits"] == 0 and len(life(e)) == len(RULES))

    # Охват: правило работало и промолчало ≠ правило не запускали.
    record([], "css", tmp, session="s9", scope=["AE1", "AE7"])
    rw = {r["rule"]: r for r in life(read(tmp))}
    chk("охват пишется даже при ЧИСТОМ прогоне: молчание — наблюдение",
        rw["AE7"]["ran"] == 1 and rw["AE7"]["hits"] == 0)
    chk("невключённое правило имеет нулевой охват",
        rw["AE12"]["ran"] == 0)
    t2 = render(life(read(tmp)), read(tmp))
    chk("работавшее и молчавшее правило вынесено в ВОПРОС",
        "## Молчание" in t2 and "AE7" in t2.split("## Молчание")[1]
        .split("## Не наблюдалось")[0])
    chk("невключённое правило вынесено в НЕ НАБЛЮДАЛОСЬ и снято с пересмотра",
        "AE12" in t2.split("## Не наблюдалось")[1]
        and "НЕ кандидаты на пересмотр" in t2)
    chk("охват — это номера правил, посторонних полей не вносит",
        leaked(read(tmp)) == [])

    txt = render(life(e), e)
    chk("свод называет кандидата в норму по числу СЕАНСОВ", "**AE1**" in txt)
    chk("без охвата свод НЕ обвиняет правила: все уходят в «не наблюдалось»",
        "## Не наблюдалось" in txt and "СДЕРЖИВАНИЕМ" not in txt)
    chk("загрязнение журнала кричит в своде",
        "ЖУРНАЛ ЗАГРЯЗНЁН" in render(life(e), e + [{"rule": "AE1",
                                                    "why": "background #fff"}]))

    d = digest(e)
    chk("сводка отдаёт только счёт сеансов на правило",
        d["rules"] == {"AE1": 2, "AE2": 1})
    chk("во внешней сводке НЕТ времени и языка",
        all(k in ("schema", "rules", "sessions") for k in d))

    os.environ["EYES_NO_JOURNAL"] = "1"
    n = record(["AE1"], "css", tmp)
    os.environ.pop("EYES_NO_JOURNAL")
    chk("выключатель работает: при EYES_NO_JOURNAL записи нет", n == 0)

    # Под /dev/null каталога быть не может — файловая система откажет
    # гарантированно, в отличие от «несуществующего пути», который под
    # правами суперпользователя молча создастся.
    chk("невозможность писать не роняет орган",
        record(["AE1"], "css", Path("/dev/null/p.jsonl")) == 0)

    r2 = record(["AE1", "AE1", "AE3"], "tsx", tmp, session="s3")
    chk("приём пачкой кладёт каждое срабатывание", r2 == 3)
    chk("пачка гейта считается ОДНИМ сеансом, а не тремя",
        {x["rule"]: x for x in life(read(tmp))}["AE3"]["sessions"] == 1)

    bad = tmp.parent / "bad.jsonl"
    bad.write_text('{"rule":"AE1","session":"s"}\nкривая строка\n{}\n',
                   encoding="utf-8")
    chk("кривая строка журнала пропускается, целые читаются",
        len(read(bad)) == 1)

    import shutil
    shutil.rmtree(tmp.parent, ignore_errors=True)

    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--digest", action="store_true")
    ap.add_argument("--forget", action="store_true")
    ap.add_argument("--ingest", action="store_true",
                    help="принять номера правил со stdin, по одному в строке")
    ap.add_argument("--lang", default="css")
    ap.add_argument("--scope", default=None,
                    help="какие правила были включены в прогоне, через запятую")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args()

    if a.court:
        return court()
    if a.forget:
        if JOURNAL.exists():
            JOURNAL.unlink()
            print("журнал стёрт:", JOURNAL)
        else:
            print("журнала нет:", JOURNAL)
        return 0

    if a.ingest:
        # Один вызов — один сеанс: пачка находок из прогона гейта есть
        # ОДНО наблюдение над одним проектом, а не сотня независимых.
        rules = [x.strip() for x in sys.stdin.read().splitlines() if x.strip()]
        rules = [r for r in rules if r in RULES]
        sc = [x.strip() for x in (a.scope or "").split(",") if x.strip()]
        n = record(rules, a.lang, session=uuid.uuid4().hex[:12],
                   scope=[x for x in sc if x in RULES])
        print(f"принято срабатываний: {n}")
        return 0

    e = read()
    if a.digest:
        print(json.dumps(digest(e), ensure_ascii=False, indent=2))
        return 0
    if not e:
        print("Журнал пуст:", JOURNAL)
        print("Он наполняется сам, когда сервер присутствия судит фрагменты.")
        return 0
    print(render(life(e), e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
