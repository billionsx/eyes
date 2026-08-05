#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · ДОБЫТЧИК КАДРОВ (ст. 46).

Зачем орган. База iOS 27 держит 52 дыры. Замер по имеющимся 195 кадрам исчерпан
честно: что снималось — снято. Дальше нужны кадры других классов (сетки,
сгруппированные списки, слоистые карточки, пустые состояния), и департамент
просил их у основателя. Просьба неверна дважды.

Во-первых, она перекладывает работу на того, кто нанял департамент. Во-вторых,
она не нужна: **Apple сама публикует снимки своих экранов** — на страницах
своих приложений в App Store. Это открытый источник, отдающий настоящие кадры
настоящей операционной системы, и он не требует ни телефона, ни чужого времени.

Проверено отдельно и записано: путь через документацию для этих дыр НЕ
РАБОТАЕТ. Свидетельство (`bin/attest.py --tokens .../tokens.next.json`) на
живой библиотеке из 27 599 норм дало «НЕТ ЗАМЕРА» по радиусу карточки, высоте
таб-бара и длительностям движения: свод Apple этих чисел не называет. Текст —
не источник геометрии, и это не мнение, а результат прогона.

Что делает орган. Идёт по объявленным страницам приложений Apple в App Store,
достаёт адреса снимков экрана из разметки страницы, забирает их и кладёт в
кадротеку под именем приложения. Дальше работает обычный конвейер:
`bin/geoscan.py` → `bin/geofill.py`.

Правила, которые орган соблюдает:
  · только приложения САМОЙ Apple. Чужой интерфейс не есть операционная
    система, и мерить по нему норму нельзя;
  · сырьё сохраняется как есть (урок У1: пока сырьё не хранится, любая правка
    измерителя гонит заново к источнику);
  · отпечаток sha256 каждого кадра пишется в паспорт добычи. Кадр без
    отпечатка нельзя предъявить как улику;
  · размер и формат проверяются: файл, который не открывается как картинка,
    отвергается вслух, а не молча (ЗКН-Э001).

Сеть нужна только этому органу и только в CI: у Apple открытый доступ, ключей
не требуется.

Запуск:
    python3 bin/frames.py --out /tmp/frames-new       — добыча
    python3 bin/frames.py --list                      — что объявлено
    python3 bin/frames.py --court                     — суд, без сети
"""
import argparse
import gzip
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawler import UA  # noqa: E402

PASSPORT = ROOT / "registry" / "screens" / "HARVEST.json"

# Приложения САМОЙ Apple в App Store. Каждый адрес объявлен, а не собран
# обходом: департамент обязан знать, чей интерфейс он мерит.
# Классы кадров рядом с адресом — чтобы видеть, какие дыры каким приложением
# закрываются, и не тянуть лишнее.
APPS = (
    ("Apple Settings", "https://apps.apple.com/us/app/id1541084045",
     "сгруппированные списки"),
    ("Apple Photos", "https://apps.apple.com/us/app/photos/id1584215428",
     "сетки плиток"),
    ("Apple Home", "https://apps.apple.com/us/app/home/id1110145103",
     "сетки плиток, пустые состояния"),
    ("Apple Wallet", "https://apps.apple.com/us/app/apple-wallet/id1160481993",
     "слоистые карточки"),
    ("Apple Music", "https://apps.apple.com/us/app/apple-music/id1108187390",
     "слоистые карточки, нижняя панель"),
    ("Apple Books", "https://apps.apple.com/us/app/apple-books/id364709193",
     "сетки, нижняя панель"),
    ("Apple Podcasts", "https://apps.apple.com/us/app/apple-podcasts/id525463029",
     "списки, нижняя панель"),
    ("Apple Reminders", "https://apps.apple.com/us/app/reminders/id1108187841",
     "сгруппированные списки, пустые состояния"),
)

# Снимки экрана в разметке App Store лежат в источниках изображений. Берётся
# самый крупный доступный размод: мелкий кадр даёт мелкие числа, а число,
# снятое с уменьшенной картинки, — не замер, а догадка.
# Хвост адреса у App Store — `<ширина>x<высота><буквы>.<формат>`: бывает
# `300x0w.webp`, `1200x630wa.png`, `460x0bb.jpg`. Буквы между размером и точкой
# ОБЯЗАТЕЛЬНО допускаются: первая редакция сита их не знала, ловила ноль кадров
# и молчала об этом — суд поймал на месте.
IMG = re.compile(r'https://is\d+-ssl\.mzstatic\.com/image/thumb/[^\s"\'<>]+?'
                 r'/\d+x\d+[a-z]*\.(?:png|jpe?g|webp)', re.I)
BIG = re.compile(r"/(\d+)x(\d+)([a-z]*)\.(png|jpe?g|webp)$", re.I)
MIN_BYTES = 20_000          # ниже — это иконка или заглушка, а не кадр экрана


CORPUS = ROOT / "registry" / "corpus" / "appstore-pages"


def corpus_put(url: str, html: str) -> bool:
    """Сохранить сырую страницу App Store. Урок У1 свода уроков.

    Урок куплен трижды: жатвой 29.07, атласом 02.08 и стражем App Store. Пока
    сырьё не хранится, любая правка сита требует снова идти к источнику — и
    первая же правка этого органа (буквенный хвост адреса, который сито не
    знало) потребовала бы ровно этого. Суд департамента поймал нарушение до
    первого прогона: свод уроков исполняется машиной, а не памятью.
    """
    try:
        CORPUS.mkdir(parents=True, exist_ok=True)
        f = CORPUS / (hashlib.sha256(url.encode()).hexdigest()[:12] + ".html.gz")
        # Детерминированно (У6): mtime=0, иначе одинаковое содержимое даёт
        # разные байты и долька конфликтует на пустом месте.
        with open(f, "wb") as raw, gzip.GzipFile(filename="", mode="wb",
                                                 fileobj=raw, mtime=0) as fh:
            fh.write(html.encode("utf-8"))
        return True
    except (OSError, ValueError):
        return False


def remill(limit: int = 12) -> dict:
    """Перемолоть сохранённые страницы текущим ситом. Без сети."""
    out = {}
    if not CORPUS.is_dir():
        return out
    for f in sorted(CORPUS.glob("*.html.gz")):
        with gzip.open(f, "rt", encoding="utf-8") as fh:
            out[f.name] = shots(fh.read(), limit)
    return out


def fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def upscale(url: str, width: int = 1170) -> str:
    """Поднять запрошенный размер кадра до ширины настоящего экрана.

    App Store отдаёт превью в том размере, который стоит в адресе. Оставить как
    есть значило бы мерить уменьшенную картинку: 393pt экрана при 3× это
    1179px, и всякий размер ниже даёт числа, которых на экране нет.
    """
    m = BIG.search(url)
    if not m:
        return url
    w, h = int(m.group(1)), int(m.group(2))
    if w >= width or w == 0:
        return url
    k = width / w
    return (url[:m.start()]
            + f"/{width}x{int(round(h * k))}{m.group(3) or ''}.{m.group(4)}")


def shots(html: str, limit: int = 12) -> list:
    """Адреса снимков экрана со страницы приложения, крупнейшие и без повторов."""
    seen, out = set(), []
    for u in IMG.findall(html):
        big = upscale(u)
        # ХОСТ — ЗЕРКАЛО, А НЕ ЛИЧНОСТЬ КАДРА. App Store отдаёт один и тот же
        # снимок с is1-ssl, is5-ssl и прочих: считать хост частью имени значит
        # добыть один кадр столько раз, сколько у Apple зеркал, и раздуть
        # совокупность повторами. Совокупность из копий одного кадра даёт
        # ложное согласие — худший вид ошибки для замера.
        key = re.sub(r"^https://is\d+-ssl\.mzstatic\.com", "",
                     re.sub(r"/\d+x\d+[a-z]*\.\w+$", "", big))
        if key in seen:
            continue
        seen.add(key)
        out.append(big)
        if len(out) >= limit:
            break
    return out


def looks_like_image(b: bytes) -> bool:
    """Настоящая ли это картинка. Проверка по подписи файла, а не по имени."""
    return (b[:8] == b"\x89PNG\r\n\x1a\n" or b[:2] == b"\xff\xd8"
            or b[:4] == b"RIFF" and b[8:12] == b"WEBP")


def harvest(out_dir: Path, apps=APPS, limit: int = 12) -> dict:
    """Добыть кадры. Возврат: паспорт добычи с отпечатками."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
           "apps": [], "frames": 0, "rejected": 0}
    for name, url, classes in apps:
        entry = {"app": name, "page": url, "classes": classes,
                 "frames": [], "error": ""}
        try:
            html = fetch(url).decode("utf-8", errors="replace")
            corpus_put(url, html)
        except Exception as e:                                  # noqa: BLE001
            entry["error"] = f"страница недоступна: {type(e).__name__}"
            rec["apps"].append(entry)
            continue
        urls = shots(html, limit)
        if not urls:
            entry["error"] = ("снимков в разметке не найдено — разметка App "
                              "Store изменилась, сито требует правки")
        d = out_dir / "apple_apps" / name
        d.mkdir(parents=True, exist_ok=True)
        for i, u in enumerate(urls, 1):
            try:
                b = fetch(u)
            except Exception as e:                             # noqa: BLE001
                entry["frames"].append({"n": i, "error": type(e).__name__})
                rec["rejected"] += 1
                continue
            if len(b) < MIN_BYTES or not looks_like_image(b):
                entry["frames"].append(
                    {"n": i, "error": f"не кадр экрана: {len(b)} байт"})
                rec["rejected"] += 1
                continue
            ext = ".png" if b[:8] == b"\x89PNG\r\n\x1a\n" else ".jpg"
            f = d / f"{i:02d}{ext}"
            f.write_bytes(b)
            entry["frames"].append({"n": i, "file": str(f.relative_to(out_dir)),
                                    "bytes": len(b),
                                    "sha256": hashlib.sha256(b).hexdigest()})
            rec["frames"] += 1
        rec["apps"].append(entry)
    return rec


def court() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    print("СУД · добытчик кадров (ст. 46, без сети)")
    chk("объявлены только приложения САМОЙ Apple",
        all(n.startswith("Apple ") for n, _, _ in APPS))
    chk("у каждого приложения назван класс кадров, который оно закрывает",
        all(c.strip() for _, _, c in APPS))
    html = ('<img src="https://is1-ssl.mzstatic.com/image/thumb/abc/def/'
            '300x0w.png">'
            '<img src="https://is5-ssl.mzstatic.com/image/thumb/abc/def/'
            '600x0w.png">'
            '<img src="https://is2-ssl.mzstatic.com/image/thumb/xyz/'
            '460x0bb.jpg">')
    got = shots(html)
    chk("повторы одного кадра в разных размерах не удваиваются", len(got) == 2)
    chk("сито знает буквенный хвост адреса (300x0w, 460x0bb): кадры "
        "находятся, а не молча теряются",
        len(shots('<img src="https://is1-ssl.mzstatic.com/image/thumb/q/w/'
                  '300x0w.webp">')) == 1)
    chk("ломаю → красный: мелкий размер поднимается до ширины экрана "
        "(1170), иначе замер идёт по уменьшенной картинке",
        all("/1170x" in u for u in got))
    chk("чиню → зелёный: уже крупный кадр не трогается",
        upscale("https://is1-ssl.mzstatic.com/image/thumb/a/b/2000x1000w.png")
        .endswith("2000x1000w.png"))
    chk("подпись файла проверяется, а не имя: PNG принят, текст отвергнут",
        looks_like_image(b"\x89PNG\r\n\x1a\n" + b"x" * 40)
        and not looks_like_image(b"<html>not an image"))
    chk("JPEG опознаётся по подписи", looks_like_image(b"\xff\xd8\xff\xe0"))
    chk("порог размера объявлен числом, а не на глаз", MIN_BYTES >= 20_000)
    import tempfile as _t
    _keep = globals()["CORPUS"]
    globals()["CORPUS"] = Path(_t.mkdtemp()) / "c"
    try:
        chk("У1: сырьё страницы сохраняется — правка сита не гонит к Apple",
            corpus_put("https://apps.apple.com/x", html)
            and list(remill().values())[0] == shots(html))
        chk("перемол идёт БЕЗ сети: читается только корпус", len(remill()) == 1)
    finally:
        globals()["CORPUS"] = _keep
    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="BXE · добытчик кадров")
    ap.add_argument("--out", default="")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--court", action="store_true")
    ap.add_argument("--remill", action="store_true",
                    help="перемолоть сохранённые страницы, без сети (У1)")
    a = ap.parse_args(argv)
    if a.court:
        return court()
    if a.remill:
        r = remill(a.limit)
        for name, urls in r.items():
            print(f"  {name}: кадров {len(urls)}")
        print(f"страниц в корпусе: {len(r)} · сеть не тронута")
        return 0 if r else 1
    if a.list or not a.out:
        for n, u, c in APPS:
            print(f"  {n:<18} {c:<38} {u}")
        print(f"  всего приложений: {len(APPS)} · кадров до "
              f"{len(APPS) * a.limit}")
        return 0
    rec = harvest(Path(a.out).resolve(), limit=a.limit)
    PASSPORT.parent.mkdir(parents=True, exist_ok=True)
    PASSPORT.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    bad = [e for e in rec["apps"] if e["error"]]
    print(f"добыто кадров: {rec['frames']} · отвергнуто: {rec['rejected']} "
          f"· приложений с ошибкой: {len(bad)}")
    for e in bad:
        print(f"  ✗ {e['app']}: {e['error']}")
    return 0 if rec["frames"] else 1


if __name__ == "__main__":
    sys.exit(main())
