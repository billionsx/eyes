#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · СВОДКА ЗАМЕРА (ст. 46).

Зачем орган. Добыча кадров из App Store отработала дважды и оба раза дала ноль
согласий. Диагноз был невозможен: кадры живут в `/tmp` раннера и исчезают
вместе с ним, а журнал прогона департаменту недоступен. Оставалось гадать —
витринные ли снимки, не тот ли формат, не та ли раскладка.

Гадать нельзя. Орган записывает В РЕЕСТР всю цепь целиком, звено за звеном:

    добыто файлов → сколько из них увидел замерщик → сколько принял →
    что namely намерил

Ноль в конце цепи ничего не говорит. Ноль, у которого видно ЗВЕНО ОБРЫВА,
говорит всё: если файлов 50, а замерщик увидел 0 — дело в поиске файлов; если
увидел 50, а принял 0 — дело в самих кадрах.

Почему отдельным органом, а не куском внутри прогона. Кусок скрипта, вписанный
в шаблон CI, не имеет суда и не проверяется ничем: его первая же ошибка
молчаливо пишет нули, и нули эти неотличимы от честного отсутствия кадров.
Ровно это и произошло 05.08.2026 — сводка сообщила «кадров 0» при пятидесяти
добытых, и отличить сбой сводки от пустой добычи было нечем.

Запуск:
    python3 bin/scansum.py --frames <папка> --scan <замер.json> --out <файл>
    python3 bin/scansum.py --court
"""
import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEN_EXT = (".png", ".jpg", ".jpeg")      # что замерщик берётся читать


def inventory(frames_dir: Path) -> dict:
    """Что лежит на диске ДО замера. Первое звено цепи."""
    if not frames_dir or not frames_dir.is_dir():
        return {"files": 0, "by_ext": {}, "seen_by_scanner": 0, "dirs": 0}
    ext = collections.Counter()
    dirs = set()
    for p in frames_dir.rglob("*"):
        if p.is_file():
            ext[p.suffix.lower() or "<без расширения>"] += 1
            dirs.add(str(p.parent.relative_to(frames_dir)))
    return {"files": sum(ext.values()), "by_ext": dict(ext.most_common()),
            "seen_by_scanner": sum(n for e, n in ext.items() if e in SEEN_EXT),
            "dirs": len(dirs)}


def top(vals, step=0.5, n=6) -> list:
    q = collections.Counter(round(v / step) * step for v in vals)
    return [{"v": v, "n": c} for v, c in q.most_common(n)]


def summarize(frames_dir: Path, scan_path: Path) -> dict:
    inv = inventory(frames_dir)
    try:
        d = json.loads(Path(scan_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        d = []
        inv["scan_error"] = f"{type(e).__name__}: замер не прочитан"
    ok = [x for x in d if x.get("ok")]
    surf = [s for x in ok for s in (x.get("surfaces") or [])]
    out = {
        "цепь": {
            "1_файлов_добыто": inv["files"],
            "2_видит_замерщик": inv["seen_by_scanner"],
            "3_записей_в_замере": len(d),
            "4_принято": len(ok),
            "5_поверхностей": len(surf),
        },
        "по_расширениям": inv["by_ext"],
        "папок": inv["dirs"],
        "экраны_pt": top([x["screen_pt"][0] for x in ok if x.get("screen_pt")], 1),
        "радиусы": top([s["radius_pt"] for s in surf
                        if s.get("radius_pt", 0) and s["radius_pt"] > 0.5]),
        "шаг_строк": top([v for x in ok for v in (x.get("rows_pt") or [])]),
        "нижние_панели": top([v for x in ok for v in (x.get("bottom_bars_pt") or [])]),
        "роли": dict(collections.Counter(s.get("role") for s in surf)),
    }
    if inv.get("scan_error"):
        out["ошибка"] = inv["scan_error"]
    rej = Path(str(scan_path) + ".rejected.json")
    if rej.exists():
        try:
            out["отказы_замерщика"] = json.loads(rej.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    out["звено_обрыва"] = break_link(out["цепь"])
    if out["звено_обрыва"].startswith("замер") and out.get("отказы_замерщика"):
        r = out["отказы_замерщика"].get("reasons") or {}
        if r:
            out["звено_обрыва"] += ". Причины отказа: " + "; ".join(
                f"{k} ×{v}" for k, v in list(r.items())[:3])
    return out


def break_link(chain: dict) -> str:
    """Где цепь оборвалась. Ноль в конце без названного звена бесполезен."""
    if chain["1_файлов_добыто"] == 0:
        return "добыча: файлов на диске нет"
    if chain["2_видит_замерщик"] == 0:
        return ("формат: файлы есть, но ни один не в тех расширениях, которые "
                f"замерщик берётся читать ({', '.join(SEEN_EXT)})")
    if chain["3_записей_в_замере"] == 0:
        return ("замер: файлы видны замерщику, но записей он не оставил — "
                "разбирайся с самим замерщиком, а не с кадрами")
    if chain["4_принято"] == 0:
        return "кадры: замерщик прочитал все и НИ ОДИН не принял"
    if chain["5_поверхностей"] == 0:
        return "поверхности: кадры приняты, но плоских областей в них не нашлось"
    return "цепь цела"


def main(argv=None):
    ap = argparse.ArgumentParser(description="BXE · сводка замера")
    ap.add_argument("--frames", default="")
    ap.add_argument("--scan", default="")
    ap.add_argument("--out", default="registry/screens/SCAN-appstore.json")
    ap.add_argument("--court", action="store_true")
    a = ap.parse_args(argv)
    if a.court:
        return court()
    s = summarize(Path(a.frames) if a.frames else None, Path(a.scan))
    p = Path(a.out) if Path(a.out).is_absolute() else ROOT / a.out
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n",
                 encoding="utf-8")
    for k, v in s["цепь"].items():
        print(f"  {k}: {v}")
    print(f"звено обрыва: {s['звено_обрыва']}")
    return 0


def court() -> int:
    import tempfile
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✓' if cond else '✗'} {name}")

    print("СУД · сводка замера (без сети)")
    d = Path(tempfile.mkdtemp())
    (d / "frames" / "Apple Photos").mkdir(parents=True)
    scan = d / "scan.json"
    scan.write_text("[]", encoding="utf-8")
    s = summarize(d / "frames", scan)
    chk("пусто на диске — звено обрыва названо добычей",
        s["звено_обрыва"].startswith("добыча"))
    (d / "frames" / "Apple Photos" / "01.webp").write_bytes(b"x" * 100)
    s = summarize(d / "frames", scan)
    chk("ломаю → красный: файлы есть, но расширение замерщику незнакомо — "
        "названо ФОРМАТОМ, а не «кадров нет»",
        s["цепь"]["1_файлов_добыто"] == 1
        and s["цепь"]["2_видит_замерщик"] == 0
        and s["звено_обрыва"].startswith("формат"))
    (d / "frames" / "Apple Photos" / "02.jpg").write_bytes(b"x" * 100)
    s = summarize(d / "frames", scan)
    chk("чиню → зелёный: знакомое расширение видно замерщику",
        s["цепь"]["2_видит_замерщик"] == 1
        and s["звено_обрыва"].startswith("замер"))
    scan.write_text(json.dumps([{"ok": False}]), encoding="utf-8")
    s = summarize(d / "frames", scan)
    chk("записи есть, но ни одна не принята — названо КАДРАМИ",
        s["звено_обрыва"].startswith("кадры"))
    scan.write_text(json.dumps([{"ok": True, "screen_pt": [393, 852],
                                 "surfaces": [], "rows_pt": [],
                                 "bottom_bars_pt": []}]), encoding="utf-8")
    s = summarize(d / "frames", scan)
    chk("кадр принят, но поверхностей нет — названо ПОВЕРХНОСТЯМИ",
        s["звено_обрыва"].startswith("поверхности"))
    scan.write_text(json.dumps([{"ok": True, "screen_pt": [393, 852],
                                 "surfaces": [{"role": "card",
                                               "radius_pt": 12.4}],
                                 "rows_pt": [49.0], "bottom_bars_pt": []}]),
                    encoding="utf-8")
    s = summarize(d / "frames", scan)
    chk("цепь цела — и числа записаны, а не только итог",
        s["звено_обрыва"] == "цепь цела" and s["радиусы"][0]["v"] == 12.5
        and s["роли"] == {"card": 1})
    s = summarize(d / "frames", d / "нет.json")
    chk("нечитаемый замер называется ошибкой, а не нулём кадров",
        "ошибка" in s and s["цепь"]["1_файлов_добыто"] == 2)
    print("СУД зелёный" if ok else "СУД КРАСНЫЙ")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
