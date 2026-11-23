#!/usr/bin/env bash
set -eu

cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --name lottery-analyzer \
  launcher.py

echo "Executável criado em: $(pwd)/dist/lottery-analyzer"
