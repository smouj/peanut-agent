#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# -----------------------------
# UTF-8 output (evita mojibake)
# -----------------------------
try {
    # Mejora textos con acentos en la consola
    chcp 65001 | Out-Null
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $OutputEncoding = [Console]::OutputEncoding
} catch {}

function Write-Info([string]$msg)  { Write-Host $msg -ForegroundColor Cyan }
function Write-Ok([string]$msg)    { Write-Host $msg -ForegroundColor Green }
function Write-Warn([string]$msg)  { Write-Host $msg -ForegroundColor Yellow }
function Write-Err([string]$msg)   { Write-Host $msg -ForegroundColor Red }

function Get-RepoRoot {
    return Split-Path -Parent $MyInvocation.MyCommand.Path
}

function Command-Exists([string]$name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    return $null -ne $cmd
}

function Resolve-Python {
    # Preferimos python.exe si existe; si no, usamos py (launcher de Windows)
    if (Command-Exists "python") { return @{ kind="python"; cmd="python" } }
    if (Command-Exists "py")     { return @{ kind="py"; cmd="py" } }
    return $null
}

function Ensure-Python {
    $py = Resolve-Python
    if ($null -ne $py) {
        if ($py.kind -eq "py") {
            $ver = & $py.cmd --version 2>$null
            Write-Ok "✅ Python detectado vía launcher: $ver"
        } else {
            $ver = & $py.cmd --version 2>$null
            Write-Ok "✅ Python detectado: $ver"
        }
        return $py
    }

    Write-Warn "⚠️ No se encontró Python (ni 'python' ni 'py')."

    if (Command-Exists "winget") {
        Write-Info "🧰 winget detectado. Intentando instalar Python 3.11..."
        try {
            winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
        } catch {
            Write-Warn "No pude instalar Python con winget automáticamente."
            Write-Warn "Error: $($_.Exception.Message)"
        }
    } else {
        Write-Info "Instala Python desde python.org marcando 'Add python.exe to PATH'."
    }

    Write-Info "🔁 Reintentando detección..."
    $py = Resolve-Python
    if ($null -eq $py) {
        Write-Err "❌ Sigue sin detectarse Python."
        Write-Info "Si te aparece el mensaje de Microsoft Store con 'python':"
        Write-Info "  Configuración → Aplicaciones → Configuración avanzada → Alias de ejecución"
        Write-Info "  Desactiva: python.exe y python3.exe"
        exit 1
    }

    return $py
}

function Confirm-CleanInstall([string]$StateDir) {
    Write-Warn "¿Quieres instalación limpia?"
    Write-Info  "Esto borrará: $StateDir"
    $choice = Read-Host "Escribe SI para borrar, o Enter para conservar"
    return ($choice -eq "SI")
}

function Remove-StateDir([string]$StateDir) {
    if (Test-Path $StateDir) {
        Write-Warn "🧹 Borrando estado: $StateDir"
        Remove-Item -Recurse -Force $StateDir
        Write-Ok "✅ Estado borrado."
    } else {
        Write-Ok "ℹ️ No había estado previo en $StateDir"
    }
}

function Ensure-Venv([hashtable]$Py, [string]$RepoRoot) {
    $venvPath = Join-Path $RepoRoot ".venv"

    if (-not (Test-Path $venvPath)) {
        Write-Info "🐍 Creando entorno virtual .venv ..."

        if ($Py.kind -eq "py") {
            # Usa la versión por defecto del launcher (en tu caso 3.13.0).
            # Si instalas 3.11, puedes cambiarlo por: & $Py.cmd -3.11 -m venv $venvPath
            & $Py.cmd -m venv $venvPath
        } else {
            & $Py.cmd -m venv $venvPath
        }

        Write-Ok "✅ .venv creado."
    } else {
        Write-Ok "✅ .venv ya existe."
    }

    $venvPython = Join-Path $venvPath "Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Write-Err "❌ No se encontró python dentro de .venv: $venvPython"
        exit 1
    }

    return $venvPython
}

function Install-Requirements([string]$VenvPython, [string]$RepoRoot) {
    Write-Info "⬆️ Actualizando pip/setuptools/wheel..."
    & $VenvPython -m pip install --upgrade pip setuptools wheel | Out-Host

    $req = Join-Path $RepoRoot "requirements.txt"
    if (-not (Test-Path $req)) {
        Write-Warn "⚠️ No existe requirements.txt en la raíz. Saltando instalación de dependencias."
        return
    }

    Write-Info "📦 Instalando dependencias desde requirements.txt..."
    & $VenvPython -m pip install -r $req | Out-Host
    Write-Ok "✅ Dependencias instaladas."
}

function Run-Wizard([string]$VenvPython, [string]$RepoRoot) {
    $wizard = Join-Path $RepoRoot "wizard.py"
    if (-not (Test-Path $wizard)) {
        Write-Err "❌ No se encontró wizard.py en la raíz del repo."
        exit 1
    }

    Write-Info "🧙 Lanzando Wizard..."
    & $VenvPython $wizard
}

# -----------------------------
# MAIN
# -----------------------------
Write-Host ""
Write-Host "🥜 PEANUT-AGENT — PRO Installer" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

$repoRoot = Get-RepoRoot
Set-Location $repoRoot

$py = Ensure-Python

$stateDir = Join-Path $HOME ".peanut-agent"
if (Confirm-CleanInstall -StateDir $stateDir) {
    Remove-StateDir -StateDir $stateDir
} else {
    Write-Ok "ℹ️ Instalación NO limpia: se conserva $stateDir"
}

$venvPython = Ensure-Venv -Py $py -RepoRoot $repoRoot
Install-Requirements -VenvPython $venvPython -RepoRoot $repoRoot
Run-Wizard -VenvPython $venvPython -RepoRoot $repoRoot

Write-Ok "✅ Instalación finalizada."
