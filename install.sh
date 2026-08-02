#!/usr/bin/env bash
# BXE · установка в одну команду.
#   curl -fsSL https://raw.githubusercontent.com/billionsx/eyes/main/install.sh | bash
# Ставит департамент в ~/.billionsx-eyes и печатает готовый блок для mcp.json.
set -euo pipefail

DIR="${EYES_HOME:-$HOME/.billionsx-eyes}"

command -v git >/dev/null || { echo "нужен git"; exit 1; }
command -v python3 >/dev/null || { echo "нужен python3"; exit 1; }

if [ -d "$DIR/.git" ]; then
  echo "· обновляю $DIR"
  git -C "$DIR" pull --quiet --ff-only
else
  echo "· ставлю в $DIR"
  git clone --quiet --depth 1 https://github.com/billionsx/eyes.git "$DIR"
fi

echo "· проверяю исправность"
python3 "$DIR/bin/mcp.py" --court >/dev/null || { echo "СУД КРАСНЫЙ — не ставлю"; exit 1; }
echo "  суд зелёный"

cat <<JSON

Готово. Добавь в mcp.json своего редактора:

{
  "mcpServers": {
    "eyes": {
      "command": "python3",
      "args": ["$DIR/bin/mcp.py"]
    }
  }
}

Перезапусти редактор и скажи агенту:
  «просканируй проект через eyes»
JSON
