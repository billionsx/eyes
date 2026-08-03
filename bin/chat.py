#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ДЕПАРТАМЕНТ В ЧАТЕ.

Зачем орган. Код этих проектов рождается НЕ в редакторе и не в pull request —
он рождается в разговоре: агент пишет, пушит в main, площадка собирает. Всё,
что департамент имел до сих пор, стояло ПОСЛЕ этого места: PR-гейт ловит уже
написанное, надзор по коммитам — уже отправленное, монитор — уже отгруженное.
Приговор приходил, когда нарушение стоило рабочего дня, а иногда и прода.

Инструмент, стоящий рядом в момент письма, снимает нарушение до того, как оно
родилось. Здесь департамент встаёт именно туда — и подключается ОДНОЙ СТРОКОЙ,
без секретов, ключей и настройки: репозиторий департамента публичен, а весь
он — чистый python3 без единой зависимости.

Подключение (одна строка в любом чате или в инструкции проекта):

    git clone --depth 1 -q https://github.com/billionsx/eyes.git /tmp/eyes \\
      && python3 /tmp/eyes/bin/chat.py --project ethnomir <файлы>

Приложения:
    chat.py --project <имя> <файлы|папки>   судить написанное ДО отправки
    chat.py --project <имя> --live          судить живой прод, без доступа к репо
    chat.py --project <имя> --brief         чем правят этот проект: правила и база
    chat.py --court                         суд над органом, без сети

Чего орган НЕ делает: не пишет код, не чинит и не советует «как лучше». Он
предъявляет норму с адресом и цель правила. Вкус остаётся человеку (ст. 7.4).
"""
import argparse
import json
import re
import shutil
import sys
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint as lint_mod        # noqa: E402  один закон — одно исполнение
import projects as projects_mod  # noqa: E402
import guide as guide_mod      # noqa: E402

TOKENS = ROOT / "registry" / "standards" / "tokens.json"
UA = "billions-x-eyes"
ASSET = re.compile(r'(?:src|href)\s*=\s*["\']([^"\']+?\.(?:css|js))["\']')


def _tokens():
    return json.loads(TOKENS.read_text(encoding="utf-8"))


def _fetch(url, limit=3000000):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read(limit).decode("utf-8", "replace")
    except (urllib.error.URLError, ValueError, TimeoutError, OSError):
        return None


def judge(adapter: dict, project_root: Path) -> list:
    """Вердикт по дереву. Правила и послабления — из ПАСПОРТА проекта."""
    tok = _tokens()
    out = []
    for mode in ("strict", "report"):
        res = lint_mod.run(ROOT, adapter, tok, mode, project_root)
        for rule, rel, line, msg in res["findings"]:
            out.append({"rule": rule, "path": rel, "line": line, "msg": msg,
                        "mode": mode})
    out.sort(key=lambda f: (f["path"], f["line"], f["rule"]))
    return out


def говорить(findings: list, header: str, limit: int = 40) -> int:
    """Сказать вердикт словами. Молчание НЕ выдаётся за чистоту (ЗКН-Э001):
    ноль находок печатается ровно так же явно, как и находки."""
    print(header)
    if not findings:
        print("  находок нет")
        return 0
    seen = {}
    for f in findings:
        seen.setdefault(f["rule"], 0)
        seen[f["rule"]] += 1
    for f in findings[:limit]:
        print(f"  {f['rule']:5} {f['path']}:{f['line']} — {f['msg']}")
    if len(findings) > limit:
        print(f"  … и ещё {len(findings) - limit}")
    print("\nчем правится:")
    for rule in sorted(seen, key=lambda r: -seen[r]):
        g = guide_mod.GUIDE.get(rule)
        цель = g[1] if isinstance(g, (list, tuple)) and len(g) > 1 else ""
        print(f"  {rule:5} ×{seen[rule]:<4} {цель}")
    return len(findings)


def cmd_files(adapter: dict, targets: list) -> int:
    """Судить то, что написано, ДО отправки. Файлы кладутся во временное
    дерево под глобы паспорта: орган тот же, что стоит в гейте, — иначе
    вердикт в чате и вердикт в CI разошлись бы, и разошлись бы молча."""
    globs = (adapter.get("report") or {}).get("globs") or []
    if not globs:
        print("в паспорте нет глобов — судить нечего")
        return 2
    # Куда лечь фрагменту, чтобы глобы паспорта его увидели.
    bases = [g.split("**")[0].rstrip("/") for g in globs]
    tmp = Path(tempfile.mkdtemp())

    # ОБЩИЙ КОРЕНЬ целей. Нужен для файлов ВНЕ рабочего каталога: без него
    # адрес сворачивался к одному имени, и два маршрута App Router метили
    # в одну точку. Обнаружить столкновение и прерваться — честнее, чем
    # затереть молча, но всё ещё отказ: в App Router КАЖДЫЙ маршрут зовётся
    # page.tsx, и департамент не смог бы судить ни один такой проект.
    # Уникальность адреса должна следовать из ПОСТРОЕНИЯ, а не из проверки.
    def _общий_корень(paths):
        real = []
        for t in paths:
            q = Path(t).resolve()
            real.append(q if q.is_dir() else q.parent)
        if not real:
            return None
        try:
            return Path(os.path.commonpath([str(x) for x in real]))
        except ValueError:            # разные тома — общего корня нет
            return None

    корень = _общий_корень(targets)

    def адрес(f: Path) -> Path:
        """Куда положить файл во временном дереве.

        Подкаталоги сохраняются намеренно. Укладка по одному лишь имени файла
        врала дважды: печатала адрес находки, указывающий на ЧУЖОЙ файл,
        и — хуже — затирала однофамильца. В App Router каждый маршрут
        называется page.tsx, поэтому обход двух маршрутов отчитывался
        за два файла, а судил один: молчание выдавалось за чистоту.
        """
        q = f.resolve()
        rel = None
        for якорь in (Path.cwd().resolve(), корень):
            if якорь is None:
                continue
            try:
                rel = q.relative_to(якорь)
                break
            except ValueError:
                continue
        if rel is None or not rel.parts:
            # Последнее прибежище: путь целиком без ведущей косой. Длинно,
            # зато однозначно — двух файлов по одному абсолютному пути
            # не бывает, и молчаливого затирания не случится никогда.
            rel = Path(*q.parts[1:]) if len(q.parts) > 1 else Path(q.name)
        for base in bases:                       # снять общую часть своего глоба
            частей = Path(base).parts
            if rel.parts[:len(частей)] == частей:
                return tmp / base / Path(*rel.parts[len(частей):])
        return tmp / bases[0] / rel

    # Обратная карта: адрес в зеркале → адрес, который назвал человек.
    # Печатать зеркало значит указывать на файл, которого у клиента нет:
    # он не сможет ни открыть его, ни поправить. Зеркало — механика
    # департамента, а не место работы разработчика.
    обратно = {}

    try:
        n = 0
        for t in targets:
            p = Path(t)
            files = sorted(p.rglob("*")) if p.is_dir() else [p]
            for f in files:
                if not f.is_file() or f.suffix not in (".css", ".tsx", ".ts",
                                                       ".jsx", ".js", ".vue",
                                                       ".swift"):
                    continue
                dst = адрес(f)
                if dst.exists():
                    # Сюда после общего корня попасть уже нельзя: адрес
                    # уникален по построению. Проверка оставлена сторожем —
                    # если однажды правка вернёт схлопывание, департамент
                    # остановится, а не отчитается за непросуженный файл.
                    print(f"два файла метят в один адрес обхода: {f} — "
                          "обход прерван, иначе один был бы пропущен молча")
                    return 2
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(f, dst)
                обратно[str(dst.relative_to(tmp))] = str(f)
                n += 1
        if not n:
            print("файлов под правила паспорта не нашлось — "
                  "пустой обход это промах адреса, а не чистота")
            return 2
        находки = judge(adapter, tmp)
        for f in находки:
            f["path"] = обратно.get(f.get("path"), f.get("path"))
        return говорить(находки,
                        f"BXE · {adapter.get('project')} · обойдено файлов: {n}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_live(adapter: dict) -> int:
    """Судить ЖИВОЙ ПРОД. Доступ к репозиторию не нужен вовсе: собранные
    стили открыты каждому, кто открыл сайт. Приватность репозитория этому
    пути безразлична — департамент смотрит то же, что видит посетитель."""
    pages = adapter.get("live_pages") or ([adapter["prod"]] if adapter.get("prod") else [])
    if not pages:
        print("в паспорте нет ни прода, ни живых страниц")
        return 2
    globs = (adapter.get("report") or {}).get("globs") or ["src/**/*.css"]
    base = globs[0].split("**")[0].rstrip("/")
    tmp = Path(tempfile.mkdtemp())
    try:
        взято = []
        for page in pages:
            html = _fetch(page)
            if not html:
                print(f"  · {page} — не открылась")
                continue
            корень = "/".join(page.split("/")[:3])
            for m in ASSET.finditer(html):
                a = m.group(1)
                if not a.endswith(".css"):
                    continue
                url = a if a.startswith("http") else корень + ("" if a.startswith("/") else "/") + a
                if url in взято:
                    continue
                css = _fetch(url)
                if not css:
                    continue
                взято.append(url)
                dst = tmp / base / (url.rsplit("/", 1)[-1])
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(css, encoding="utf-8")
        if not взято:
            print("собранных стилей на страницах не нашлось — "
                  "сказать нечего, и это сказано вслух")
            return 2
        for u in взято:
            print(f"  взято: {u}")
        return говорить(judge(adapter, tmp),
                        f"\nBXE · {adapter.get('project')} · ЖИВОЙ ПРОД · "
                        f"файлов стилей: {len(взято)}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_brief(adapter: dict) -> int:
    r = (adapter.get("report") or {}).get("rules") or []
    s = (adapter.get("strict") or {}).get("rules") or []
    print(f"BXE · паспорт «{adapter.get('project')}»")
    print(f"  прод: {adapter.get('prod') or '—'}")
    print(f"  где смотрит: {', '.join((adapter.get('report') or {}).get('globs') or []) or '—'}")
    print(f"  говорит (report): {len(r)} правил · {', '.join(r)}")
    print(f"  роняет сборку (strict): {len(s) or 'ни одного — режим советника'}")
    for rule in r:
        g = guide_mod.GUIDE.get(rule)
        если = g[0] if isinstance(g, (list, tuple)) else ""
        print(f"    {rule:5} {если}")
    return 0


def court() -> int:
    ok = True

    def chk(n, c):
        nonlocal ok
        ok = ok and bool(c)
        print(f"  {'✓' if c else '✗'} {n}")

    print("СУД · департамент в чате")
    ad = {"project": "суд", "pt_to_css_px": 1,
          "report": {"globs": ["s/**/*.css"], "rules": ["AE2", "AE11"]},
          "strict": {"globs": [], "rules": []}}
    tmp = Path(tempfile.mkdtemp())
    try:

        # ── коллизия App Router ────────────────────────────────────────────────
        # Дефект найден ВТОРЫМ клиентом (Ethnomir), а не департаментом: два
        # маршрута page.tsx метили в один адрес зеркала, обход отчитывался за
        # два файла и судил один. Молчание выдавалось за чистоту.
        rt = Path(tempfile.mkdtemp(prefix="eyes-router-"))
        (rt / "app" / "steps").mkdir(parents=True)
        (rt / "app" / "way").mkdir(parents=True)
        (rt / "app" / "steps" / "page.tsx").write_text(
            ".a{background:#f2f2f5;}", encoding="utf-8")
        (rt / "app" / "way" / "page.tsx").write_text(
            ".b{background:#123456;}", encoding="utf-8")
        import io as _io
        import contextlib as _ctx
        # Паспорт с глобом на .tsx: маршруты App Router — это tsx, и судить
        # их набором для .css бессмысленно.
        ad_rt = {"project": "суд", "pt_to_css_px": 1,
                 "report": {"globs": ["s/**/*.tsx"], "rules": ["AE1"]},
                 "strict": {"globs": [], "rules": []}}
        буфер = _io.StringIO()
        with _ctx.redirect_stdout(буфер):
            cmd_files(ad_rt, [str(rt / "app" / "steps" / "page.tsx"),
                              str(rt / "app" / "way" / "page.tsx")])
        вывод = буфер.getvalue()
        chk("однофамильцы App Router СУДЯТСЯ оба, а не затирают друг друга",
              вывод.count("AE1") >= 2 and "#F2F2F5" in вывод and "#123456" in вывод)
        chk("обход не прерывается: адрес уникален по построению",
              "обход прерван" not in вывод)
        chk("адрес находки — НАСТОЯЩИЙ путь, а не зеркало департамента",
              "steps/page.tsx" in вывод and "s/app/steps" not in вывод)
        chk("оба маршрута различимы в выводе",
              "steps/page.tsx" in вывод and "way/page.tsx" in вывод)
        shutil.rmtree(rt, ignore_errors=True)

        (tmp / "s").mkdir()
        (tmp / "s" / "a.css").write_text(".x{box-shadow:0 0 4px #000}",
                                         encoding="utf-8")
        f = judge(ad, tmp)
        chk("вердикт в чате даёт ТОТ ЖЕ орган, что и гейт",
            any(x["rule"] == "AE2" for x in f))
        chk("у находки есть адрес: файл и строка",
            all(x["path"] and x["line"] for x in f))
        (tmp / "s" / "a.css").write_text(".x{color:red}", encoding="utf-8")
        chk("чистый код — ноль находок, а не выдуманные",
            judge(ad, tmp) == [])
        chk("чистота ГОВОРИТСЯ вслух, молчанием не подменяется",
            говорить([], "проба") == 0)
        pустой = dict(ad, report={"globs": [], "rules": []})
        chk("паспорт без глобов отказывается судить, а не хвалит",
            cmd_files(pустой, [str(tmp)]) == 2)
        chk("файлов не нашлось — это промах адреса, а не чистота",
            cmd_files(ad, [str(tmp / "нет")]) == 2)
        chk("прода нет в паспорте — живой путь отказывается, не выдумывая",
            cmd_live({"project": "суд", "report": {"globs": ["s/**"]}}) == 2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--project", default="")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--court", action="store_true")
    ap.add_argument("targets", nargs="*")
    a = ap.parse_args()
    if a.court:
        return court()
    ad = projects_mod.pick(ROOT, a.project or None)
    if a.project and ad.get("project") != a.project:
        print(f"паспорта «{a.project}» в департаменте нет. "
              f"Есть: {', '.join(projects_mod.enabled(ROOT))}")
        return 2
    if a.brief:
        return cmd_brief(ad)
    if a.live:
        return 0 if cmd_live(ad) in (0,) else 1
    if not a.targets:
        print(__doc__.strip().split("Приложения:")[1])
        return 2
    cmd_files(ad, a.targets)
    return 0


if __name__ == "__main__":
    sys.exit(main())
