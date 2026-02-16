Write-Host "🥜 Peanut Agent — Instalador de Ollama (Windows)" -ForegroundColor Yellow
Write-Host "------------------------------------------------" -ForegroundColor Yellow

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
  Write-Host "✅ Ollama ya está instalado." -ForegroundColor Green
  try { ollama --version } catch {}
  exit 0
}

Write-Host "ℹ️  Ollama en Windows se instala desde el instalador oficial." -ForegroundColor Cyan
Write-Host "➡️  Abre: https://ollama.com/download" -ForegroundColor Cyan
Write-Host "Luego reinicia tu terminal y ejecuta: ollama --version" -ForegroundColor Cyan
