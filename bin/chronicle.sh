#!/usr/bin/env bash
# BXE · хроника: коммит состояния в репозиторий (основной канал наблюдаемости).
# Использование: bin/chronicle.sh "сообщение" путь [путь...]
# Пустой дифф — не ошибка. Пуш с ретраями: чужой прогон мог опередить.
set -u
cd "$(dirname "$0")/.." || exit 2
MSG="${1:?нужно сообщение}"
shift
# Драйвер слияния складов: столкновение по адресу решается объединением.
# Без него `-X theirs` молча выбрасывал страницы другого писателя — для
# журнала терпимо, для склада знаний это потеря добытого.
git config merge.corpusunion.name "объединение склада по адресу"
git config merge.corpusunion.driver "python3 bin/corpus_merge.py %O %A %B"
git config user.name "eyes"
git config user.email "ceo@billionsx.com"
git add "$@" 2>/dev/null || true
if git diff --cached --quiet; then
  echo "изменений нет — хроника чиста"
  exit 0
fi
git commit -q -m "$MSG"
for i in 1 2 3 4 5 6; do
  if git push -q; then
    echo "хроника записана: $(git rev-parse --short HEAD)"
    exit 0
  fi
  git pull --rebase -X theirs -q || git rebase --abort || true
  sleep 4
done
git push
