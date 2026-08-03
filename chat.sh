#!/usr/bin/env bash
# BILLIONS X EYES · ПОДКЛЮЧЕНИЕ В ЧАТЕ, ОДНОЙ СТРОКОЙ.
#
#   curl -fsSL https://raw.githubusercontent.com/billionsx/eyes/main/chat.sh | bash -s <проект>
#
# Ни ключа, ни секрета, ни настройки: департамент публичен и состоит из
# одного python3 без зависимостей. Ставится в песочницу сессии за секунды,
# проверяет сам себя судом и докладывает, чем правит этот проект.
set -euo pipefail

PROJECT="${1:-}"
DIR="${EYES_HOME:-/tmp/eyes}"

if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull --quiet --ff-only 2>/dev/null || true
else
  git clone --quiet --depth 1 https://github.com/billionsx/eyes.git "$DIR"
fi

# Департамент, не прошедший собственный суд, не судит чужой код.
python3 "$DIR/bin/chat.py" --court >/dev/null 2>&1 \
  || { echo "СУД КРАСНЫЙ — департамент себя не подтвердил, не подключаюсь"; exit 1; }

echo "BXE подключён · суд зелёный · $(git -C "$DIR" rev-parse --short HEAD)"
echo

if [ -n "$PROJECT" ]; then
  python3 "$DIR/bin/chat.py" --project "$PROJECT" --brief || exit 1
  echo
  echo "Судить написанное ДО отправки:"
  echo "  python3 $DIR/bin/chat.py --project $PROJECT <файлы>"
  echo "Судить живой прод (доступ к репозиторию не нужен):"
  echo "  python3 $DIR/bin/chat.py --project $PROJECT --live"
else
  python3 "$DIR/bin/eyes.py" projects
fi
