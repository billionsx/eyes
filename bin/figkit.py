#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BXE · КИТ. Величины официальных дизайн-китов Apple — без единого аккаунта.

Основатель: «движок должен сам открывать кит iOS 27 и брать стандарты,
элементы, иконки — без моего аккаунта». Две руки:

РУКА SKETCH (главная, полностью автономная):
  Apple публикует те же киты для Sketch ПРЯМЫМИ ссылками на
  https://developer.apple.com/design/resources/ — а .sketch это zip с JSON.
  Шаги: страница → все ссылки .dmg/.zip/.sketch с iOS/iPadOS в имени →
  скачать → раскрыть (dmg через 7z, sketch как zip) → пройти JSON:
    цвета (fills/sharedSwatches) · текстовые стили (кегль, интерлиньяж,
    кернинг) · радиусы углов · перечень символов и иконок.
  Каждая величина несёт адрес kit:<файл>:<страница>/<имя> — это 🍎 канон
  Apple с адресом, им законно закрываются 🕳 каркаса ios27 (устав ст. 40).

РУКА FIGMA (спит до ключей):
  REST GET /v1/files/<key> при секретах FIGMA_TOKEN(+FIGMA_KIT_KEY) — тот же
  разбор дерева. Community-hub без сессии ключа не отдаёт; MCP требует
  edit-доступ (проверено 23.07.2026, отказ зафиксирован). Рука просыпается,
  как только ключи появляются, — до тех пор честное «спит», не имитация.

Запуск экономный: рука Sketch работает, только если снимок design-resources
изменился с прошлого извлечения (или --force).
"""
import io
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crawler import UA, _robots_ok  # noqa: E402

RES_URL = "https://developer.apple.com/design/resources/"
LINK = re.compile(r'href="([^"]+\.(?:dmg|zip|sketch))"', re.I)
KITWORD = re.compile(r"ios|ipados|tvos|visionos", re.I)
FONTWORD = re.compile(r"^SF-[A-Za-z-]+\.dmg$", re.I)


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


MAX_KIT_BYTES = 700 * 1024 * 1024


def _get(url: str, binary=False, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if not binary:
            return r.read().decode("utf-8", "replace")
        chunks, total = [], 0
        while True:
            c = r.read(1 << 20)
            if not c:
                break
            total += len(c)
            if total > MAX_KIT_BYTES:
                raise RuntimeError(f"кит больше капа {MAX_KIT_BYTES>>20}МБ")
            chunks.append(c)
        return b"".join(chunks)


def _rgba(c: dict) -> str:
    try:
        r, g, b = (round(float(c.get(k, 0)) * 255) for k in ("red", "green", "blue"))
        a = round(float(c.get("alpha", 1)), 3)
        hexv = f"#{r:02X}{g:02X}{b:02X}"
        return hexv if a == 1 else f"rgba({r},{g},{b},{a})"
    except Exception:
        return "?"


def parse_sketch(data: bytes, kit_name: str) -> dict:
    """Детерминированный обход .sketch (zip с JSON) → величины с адресами."""
    colors, texts, radii, symbols = {}, {}, {}, []
    zf = zipfile.ZipFile(io.BytesIO(data))
    doc = json.loads(zf.read("document.json").decode("utf-8", "replace"))
    for sw in ((doc.get("sharedSwatches") or {}).get("objects") or []):
        v = _rgba(sw.get("value") or {})
        colors.setdefault(sw.get("name", "?"), {"value": v, "at": f"kit:{kit_name}:swatch/{sw.get('name','?')}"})
    for ts in ((doc.get("layerTextStyles") or {}).get("objects") or []):
        st = (((ts.get("value") or {}).get("textStyle") or {}).get("encodedAttributes") or {})
        fd = ((st.get("MSAttributedStringFontAttribute") or {}).get("attributes") or {})
        texts.setdefault(ts.get("name", "?"), {
            "font": fd.get("name"), "size_pt": fd.get("size"),
            "kerning": st.get("kerning"),
            "line_pt": ((st.get("paragraphStyle") or {}).get("maximumLineHeight")),
            "at": f"kit:{kit_name}:textstyle/{ts.get('name','?')}"})

    def walk(layer, page):
        cls = layer.get("_class", "")
        nm = layer.get("name", "?")
        if cls in ("symbolMaster",):
            symbols.append(nm)
        fr = layer.get("fixedRadius")
        if cls == "rectangle":
            pts = (layer.get("points") or [])
            rad = fr if fr else (pts[0].get("cornerRadius") if pts else None)
            if rad:
                radii.setdefault(round(float(rad), 1), f"kit:{kit_name}:{page}/{nm}")
        for ch in layer.get("layers") or []:
            walk(ch, page)

    for name in zf.namelist():
        if name.startswith("pages/") and name.endswith(".json"):
            try:
                pg = json.loads(zf.read(name).decode("utf-8", "replace"))
            except Exception:
                continue
            pname = pg.get("name", name)
            for ly in pg.get("layers") or []:
                walk(ly, pname)
    return {"colors": colors, "text_styles": texts,
            "corner_radii": {str(k): v for k, v in sorted(radii.items())},
            "symbols": sorted(set(symbols))}


def _extract_container(blob: bytes, suffix: str, tmp: Path) -> bytes:
    """dmg/zip → байты первого .sketch внутри (7z раскрывает dmg на linux)."""
    if suffix == "sketch":
        return blob
    src = tmp / f"kit.{suffix}"
    src.write_bytes(blob)
    out = tmp / "x"
    out.mkdir(exist_ok=True)
    subprocess.run(["7z", "x", "-y", f"-o{out}", str(src)],
                   capture_output=True, timeout=600)
    sk = sorted(out.rglob("*.sketch"), key=lambda p: -p.stat().st_size)
    if not sk:
        raise RuntimeError("в контейнере нет .sketch")
    return sk[0].read_bytes()


def pick_targets(all_names: list, done: set) -> list:
    """Очередь китов: только контейнеры со Sketch внутри, по одному за прогон."""
    cands = [n for n in all_names if KITWORD.search(n) and "Sketch" in n]
    return sorted(n for n in cands if n not in done)[:1]


def run_sketch_arm(root: Path, force=False, fixtures: Path = None) -> dict:
    reg = root / "registry"
    kdir = reg / "standards" / "kit"
    kdir.mkdir(parents=True, exist_ok=True)
    stf = kdir / "state.json"
    st = json.loads(stf.read_text(encoding="utf-8")) if stf.exists() else {}
    if fixtures is not None:
        links = [("fixture-kit.sketch", (fixtures / "mini-kit.sketch").read_bytes())]
        page_sha = "fixture"
    else:
        snap = reg / "snapshots" / "design-resources.txt"
        page_sha = json.loads((reg / "state" / "watch-state.json").read_text(encoding="utf-8")) \
            .get("design-resources", {}).get("sha", "")
        done = set(st.get("done", []))
        if not force and st.get("page_sha") == page_sha and not pick_targets(st.get("links_seen", []), done):
            return {"status": "без изменений — очередь китов пуста", "kits": st.get("kits", [])}
        if not _robots_ok(RES_URL):
            return {"status": "robots-disallow", "kits": []}
        html = _get(RES_URL)
        all_names = sorted({h.rsplit("/", 1)[-1] for h in LINK.findall(html)})
        links, font_links = [], []
        for href in LINK.findall(html):
            fn = href.rsplit("/", 1)[-1]
            if FONTWORD.match(fn):
                url = href if href.startswith("http") else "https://developer.apple.com" + href
                try:
                    font_links.append((fn, _get(url, binary=True, timeout=900)))
                except Exception as e:
                    font_links.append((fn + "!download", str(e).encode()))
                continue
            if KITWORD.search(fn):
                url = href if href.startswith("http") else "https://developer.apple.com" + href
                name = url.rsplit("/", 1)[-1]
                if name in pick_targets(all_names, done):
                    try:
                        links.append((name, _get(url, binary=True, timeout=900)))
                    except Exception as e:
                        links.append((name + "!download", str(e).encode()))
        if not links:
            return {"status": "очередь китов пуста (все Sketch-киты разобраны)", "kits": st.get("kits", [])}
    kits, arm_errors, fonts = [], [], []
    with tempfile.TemporaryDirectory() as td:
        if fixtures is None and font_links:
            fonts = run_fonts_arm(root, font_links[:3], Path(td))
        for name, blob in links[:1]:
            try:
                if name.endswith("!download"):
                    raise RuntimeError("закачка: " + blob.decode(errors="replace")[:160])
                suffix = name.rsplit(".", 1)[-1].lower()
                sk = _extract_container(blob, suffix, Path(td))
                std = parse_sketch(sk, name)
                slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                (kdir / f"{slug}.json").write_text(json.dumps(std, ensure_ascii=False, indent=1), encoding="utf-8")
                kits.append({"kit": name, "colors": len(std["colors"]), "text_styles": len(std["text_styles"]),
                             "radii": len(std["corner_radii"]), "symbols": len(std["symbols"])})
            except Exception as e:  # рука не убивает движок: ошибка = честная запись
                arm_errors.append(f"{name}: {type(e).__name__}: {e}")
    st = {"page_sha": (page_sha if not arm_errors else st.get("page_sha", "")),
          "done": sorted(set(st.get("done", [])) | {k["kit"] for k in kits}),
          "kits": (st.get("kits", []) + kits), "errors": arm_errors,
          "links_seen": (all_names if fixtures is None else ["fixture"]),
          "fonts": fonts, "ts": _now()}
    stf.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    idx = ["# КИТ · величины официальных китов Apple (рука Sketch, без аккаунтов)",
           "Каждая величина несёт адрес kit:<файл>:<страница>/<имя> — 🍎 канон Apple.", ""]
    for k in kits:
        idx.append(f"- `{k['kit']}` · цветов {k['colors']} · текст-стилей {k['text_styles']}"
                   f" · радиусов {k['radii']} · символов {k['symbols']}")
    idx.append("")
    idx.append("Рука Figma: спит до секретов FIGMA_TOKEN(+FIGMA_KIT_KEY); community-hub без сессии "
               "ключа не отдаёт, MCP требует edit-доступ (отказ зафиксирован 23.07.2026).")
    (kdir / "KIT.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    if fixtures is None:
        with (reg / "state" / "CHANGELOG.md").open("a", encoding="utf-8") as f:
            f.write(f"### {_now()} · кит\n" + "".join(
                f"- {k['kit']}: цветов {k['colors']} · текст-стилей {k['text_styles']} · радиусов {k['radii']} · символов {k['symbols']}\n" for k in kits)
                + "".join(f"- ОШИБКА руки: {e}\n" for e in arm_errors)
                + "".join(f"- шрифты: {x.get('dmg')}: лиц {x.get('faces','—')} · крышка {x.get('cap_sample','—')} {x.get('error','')}\n" for x in fonts)
                + ("- все ссылки страницы: " + " · ".join(all_names) + "\n" if fixtures is None else "") + "\n")
    status = "извлечено" if kits else ("ошибка руки: " + "; ".join(arm_errors) if arm_errors else "пусто")
    return {"status": status, "kits": kits, "errors": arm_errors}


def parse_font_bytes(otf: bytes, at: str) -> dict:
    """Метрики шрифта первоисточника (fonttools): em · крышка · подъёмы."""
    import io as _io
    from fontTools.ttLib import TTFont
    ft = TTFont(_io.BytesIO(otf), fontNumber=0, lazy=True)
    os2, head, hhea = ft["OS/2"], ft["head"], ft["hhea"]
    name = ft["name"].getDebugName(4) or ft["name"].getDebugName(1) or "?"
    upm = head.unitsPerEm
    cap = getattr(os2, "sCapHeight", 0) or 0
    return {"name": name, "unitsPerEm": upm,
            "capHeight": cap, "capHeight_fraction": round(cap / upm, 4) if cap else None,
            "xHeight": getattr(os2, "sxHeight", None),
            "ascender": hhea.ascent, "descender": hhea.descent, "at": at}


def run_fonts_arm(root: Path, links: list, tmp: Path) -> list:
    """SF-семья прямыми dmg с design-resources → метрики каждого лица.
    Величины 🍎-грейд с адресом font:<dmg>:<файл> — фундамент типографики."""
    fdir = root / "registry" / "standards" / "fonts"
    fdir.mkdir(parents=True, exist_ok=True)
    faces_all = []
    for name, blob in links:
        try:
            if name.endswith("!download"):
                raise RuntimeError(blob.decode(errors="replace")[:120])
            src = tmp / name
            src.write_bytes(blob)
            out = tmp / ("f_" + name)
            out.mkdir(exist_ok=True)
            subprocess.run(["7z", "x", "-y", f"-o{out}", str(src)], capture_output=True, timeout=600)
            for depth in range(2):  # dmg → pkg → Payload(cpio): вскрываем вложенные контейнеры
                inner = [p for p in out.rglob("*") if p.is_file() and
                         (p.suffix.lower() == ".pkg" or p.name.startswith("Payload"))]
                if not inner:
                    break
                for i, p in enumerate(inner):
                    sub = out / f"in{depth}_{i}"
                    sub.mkdir(exist_ok=True)
                    subprocess.run(["7z", "x", "-y", f"-o{sub}", str(p)], capture_output=True, timeout=600)
                    p.unlink(missing_ok=True)
            faces = []
            for p in sorted(out.rglob("*.otf")) + sorted(out.rglob("*.ttf")):
                try:
                    faces.append(parse_font_bytes(p.read_bytes(), f"font:{name}:{p.name}"))
                except Exception:
                    pass
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            (fdir / f"{slug}.json").write_text(json.dumps(
                {"dmg": name, "faces": faces}, ensure_ascii=False, indent=1), encoding="utf-8")
            faces_all.append({"dmg": name, "faces": len(faces),
                              "cap_sample": next((x["capHeight_fraction"] for x in faces if x["capHeight_fraction"]), None)})
        except Exception as e:
            faces_all.append({"dmg": name, "error": f"{type(e).__name__}: {e}"[:140]})
    return faces_all


def run_figma_arm(root: Path) -> dict:
    import os
    tok, key = os.environ.get("FIGMA_TOKEN"), os.environ.get("FIGMA_KIT_KEY")
    if not tok or not key:
        return {"status": "спит: нет FIGMA_TOKEN/FIGMA_KIT_KEY"}
    req = urllib.request.Request(f"https://api.figma.com/v1/files/{key}",
                                 headers={"X-Figma-Token": tok, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    styles = d.get("styles") or {}
    comp = d.get("components") or {}
    out = {"name": d.get("name"), "styles": {k: v.get("name") for k, v in styles.items()},
           "components": sorted({v.get("name", "?") for v in comp.values()})}
    kdir = root / "registry" / "standards" / "kit"
    kdir.mkdir(parents=True, exist_ok=True)
    (kdir / "figma-arm.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "извлечено (figma)", "components": len(out["components"]), "styles": len(styles)}


if __name__ == "__main__":
    force = "--force" in sys.argv
    r = run_sketch_arm(Path(__file__).resolve().parents[1], force=force)
    print("кит:", r["status"])
    for k in r.get("kits", []):
        print(f"  {k['kit']}: цветов {k['colors']} · текст-стилей {k['text_styles']} · символов {k['symbols']}")
    f = run_figma_arm(Path(__file__).resolve().parents[1])
    print("figma-рука:", f["status"])
