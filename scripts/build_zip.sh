#!/usr/bin/env bash
set -e
OUT="concurse-ai.zip"
echo "Gerando $OUT ..."
zip -r "$OUT" . -x ".git/*" ".venv/*" "node_modules/*" "__pycache__/*"
echo "OK -> $OUT"