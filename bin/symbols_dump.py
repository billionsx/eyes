#!/usr/bin/env python3
"""BXE · опись SF Symbols из установленного приложения (ст. 49.1)."""
import plistlib, sys, json, pathlib
d = plistlib.load(open(sys.argv[1], 'rb'))
syms = sorted((d.get("symbols") or {}).keys())
out = pathlib.Path("registry/standards/symbols/sf-symbols-names.json")
out.write_text(json.dumps({"count": len(syms), "at": "app:SF Symbols/name_availability.plist",
                           "names": syms}, ensure_ascii=False), encoding="utf-8")
print("символов выгружено:", len(syms))
