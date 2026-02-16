#!/usr/bin/env bash
set -euo pipefail

echo "🥜 Peanut Agent — Instalador de Ollama (Linux/macOS)"
echo "---------------------------------------------------"

if command -v ollama >/dev/null 2>&1; then
  echo "✅ Ollama ya está instalado: $(ollama --version 2>/dev/null || true)"
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "❌ Falta curl. Instálalo y reintenta."
  exit 1
fi

echo "⬇️  Descargando e instalando Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo "✅ Instalación completada."
echo "ℹ️  Inicia el servicio (si aplica):"
echo "   - Linux (systemd): sudo systemctl enable --now ollama"
echo "   - macOS: abre la app Ollama"
