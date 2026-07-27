#!/usr/bin/env bash
# BXE · советник + храповик по ВСЕМ подключённым проектам (ст. 57, §7.4).
# Долг каждого правила может только падать. Не забранный код — красный:
# пустой обход не доказательство погашенного долга (ЗКН-Х001).
set -u
cd "$(dirname "$0")/.." || exit 2
rc=0
for f in adapters/*.json; do
  a=$(basename "$f" .json)
  [ "$a" = "default" ] && continue
  python3 -c "import json,sys;sys.exit(0 if json.load(open('$f')).get('enabled',True) else 3)" || continue
  if [ ! -d "_projects/$a" ]; then
    echo "$a: код не забран — советник не судит пустоту (ЗКН-Х001)"
    rc=1
    continue
  fi
  if PROJECT_ROOT="_projects/$a" python3 bin/eyes.py lint --adapter "$a" --mode report \
       --out "registry/state/report-$a.md" \
       --ratchet registry/state/ae-baseline.json > /tmp/lint-"$a".out 2>&1; then
    :
  else
    echo "=== $a: храповик красный ==="
    tail -20 /tmp/lint-"$a".out
    rc=1
  fi
  [ -f "registry/state/report-$a.md" ] && sed -n '2p' "registry/state/report-$a.md"
done
exit $rc
