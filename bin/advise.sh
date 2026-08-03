#!/usr/bin/env bash
# BXE · советник + храповик по ВСЕМ подключённым проектам (ст. 57, §7.4).
# Долг каждого правила может только падать. Не забранный код — красный:
# пустой обход не доказательство погашенного долга (ЗКН-Э006).
#
# АТРИБУЦИЯ КРАСНОГО (02.08.2026). Красный департамента и красный клиента —
# разные сигналы, слитые в один код возврата. Покупатель, глядя на значок
# инструмента, видел красное из-за регрессии чужого проекта. Ст. 43 требует
# красного при росте долга и ослаблению не подлежит — поэтому вводится не
# поблажка, а РАЗДЕЛЕНИЕ: кто именно красен и почему.
#   registry/state/CLIENTS.md — построчный вердикт по каждому паспорту.
set -u
cd "$(dirname "$0")/.." || exit 2
rc=0
CL=registry/state/CLIENTS.md
{ echo "# ВЕРДИКТЫ ПО ПАСПОРТАМ"; echo;
  echo "Красный инструмента и красный клиента — разные вещи. Здесь сказано, чей.";
  echo; echo "| паспорт | вердикт | причина |"; echo "|---|---|---|"; } > "$CL"
for f in adapters/*.json; do
  a=$(basename "$f" .json)
  [ "$a" = "default" ] && continue
  python3 -c "import json,sys;sys.exit(0 if json.load(open('$f')).get('enabled',True) else 3)" || continue
  if [ ! -d "_projects/$a" ]; then
    echo "$a: код не забран — советник не судит пустоту (ЗКН-Э006)"
    echo "| $a | 🔴 ИНСТРУМЕНТ | код не забран — обход пустоты запрещён (ЗКН-Э006) |" >> "$CL"
    rc=1
    continue
  fi
  if PROJECT_ROOT="_projects/$a" python3 bin/eyes.py lint --adapter "$a" --mode report \
       --out "registry/state/report-$a.md" \
       --ratchet registry/state/ae-baseline.json > /tmp/lint-"$a".out 2>&1; then
    echo "| $a | 🟢 чисто | долг не вырос |" >> "$CL"
  else
    echo "=== $a: храповик красный ==="
    tail -20 /tmp/lint-"$a".out
    echo "| $a | 🔴 КЛИЕНТ | долг вырос — ст. 43, инструмент исправен |" >> "$CL"
    rc=1
  fi
  [ -f "registry/state/report-$a.md" ] && sed -n '2p' "registry/state/report-$a.md"
done
{ echo; echo "Красный с пометкой КЛИЕНТ означает, что инструмент исправен и";
  echo "поймал регрессию проекта. Красный с пометкой ИНСТРУМЕНТ — что не в";
  echo "порядке сам департамент."; } >> "$CL"
exit $rc
