"""
🥜 Peanut Wizard (PRO)
----------------------
Wizard interactivo "bonito" para preparar el entorno:
- Verifica dependencias Python y las instala si faltan.
- Verifica Ollama, conexión al servidor y modelos.
- Pregunta por instalación limpia (borra ~/.peanut-agent).
- Integración opcional PicoClaw (descarga/uso).

Ejecutar:
    python wizard.py
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

import requests
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

DEFAULT_OLLAMA_URL = "http://localhost:11434"
STATE_DIR = Path.home() / ".peanut-agent"

ASCII_TITLE = r"""
 ____                  _             _        _             _
|  _ \ _ __ ___   __ _| |_ ___  _ __| |__    / \   __ _  __| | ___ _ __
| |_) | '__/ _ \ / _` | __/ _ \| '__| '_ \  / _ \ / _` |/ _` |/ _ \ '__|
|  __/| | | (_) | (_| | || (_) | |  | |_) |/ ___ \ (_| | (_| |  __/ |
|_|   |_|  \___/ \__,_|\__\___/|_|  |_.__/ /_/   \_\__,_|\__,_|\___|_|

                       🥜 PEANUT-AGENT • PRO v0.1
""".strip("\n")


def _run(cmd: List[str], *, cwd: Optional[Path] = None) -> Tuple[int, str]:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def _ollama_reachable(ollama_url: str, timeout_s: int = 2) -> bool:
    try:
        r = requests.get(f"{ollama_url}/api/tags", timeout=timeout_s)
        return r.status_code == 200
    except Exception:
        return False


def _ensure_python_deps(console: Console, requirements_path: Path) -> None:
    console.print("\n[bold]🔧 Dependencias Python[/bold]")
    missing = []
    for pkg in ["requests", "pydantic", "rich", "fastapi", "uvicorn", "websockets"]:
        try:
            __import__(pkg)
        except Exception:
            missing.append(pkg)

    if not missing:
        console.print("[green]✅ Dependencias Python OK[/green]")
        return

    console.print(f"[yellow]⚠️ Faltan paquetes:[/yellow] {', '.join(missing)}")
    if not requirements_path.exists():
        console.print("[red]❌ No encuentro requirements.txt[/red]")
        return

    if Confirm.ask("¿Instalar dependencias ahora con pip?", default=True):
        rc, out = _run([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])
        if rc != 0:
            console.print("[red]❌ Falló pip install[/red]")
            console.print(out)
            raise SystemExit(1)
        console.print("[green]✅ Dependencias instaladas[/green]")
    else:
        console.print("[yellow]⏭️ Saltando instalación. Puede fallar la ejecución.[/yellow]")


def _clean_install(console: Console) -> None:
    console.print("\n[bold]🧼 Instalación limpia[/bold]")
    if STATE_DIR.exists():
        console.print(f"[yellow]Detectado estado previo en:[/yellow] {STATE_DIR}")
        if Confirm.ask("¿Quieres borrar datos existentes antes de continuar?", default=False):
            confirm = Prompt.ask("Escribe BORRAR para confirmar", default="")
            if confirm.strip().upper() != "BORRAR":
                console.print("[red]Cancelado. No se borró nada.[/red]")
                return
            shutil.rmtree(STATE_DIR, ignore_errors=True)
            console.print("[green]✅ Datos borrados.[/green]")
    else:
        console.print("[green]✅ No hay datos previos.[/green]")


def _ensure_ollama(console: Console, ollama_url: str) -> None:
    console.print("\n[bold]🧠 Ollama[/bold]")
    has_bin = shutil.which("ollama") is not None
    reachable = _ollama_reachable(ollama_url)

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Chequeo")
    table.add_column("Estado")
    table.add_row("Binario `ollama`", "✅" if has_bin else "❌")
    table.add_row(f"Servidor ({ollama_url})", "✅" if reachable else "❌")
    console.print(table)

    if not has_bin:
        console.print("[yellow]ℹ️ No encuentro `ollama` en PATH.[/yellow]")
        if platform.system().lower() in ["linux", "darwin"]:
            if Confirm.ask("¿Intentar instalar Ollama ahora? (usa scripts/install_ollama.sh)", default=True):
                script = Path(__file__).parent / "scripts" / "install_ollama.sh"
                if not script.exists():
                    console.print("[red]❌ No encuentro scripts/install_ollama.sh[/red]")
                    raise SystemExit(1)
                script.chmod(0o755)
                rc, out = _run(["bash", str(script)])
                console.print(out)
                if rc != 0:
                    raise SystemExit(1)
        else:
            console.print("[yellow]➡️ En Windows, ejecuta scripts/install_ollama.ps1 o descarga desde ollama.com/download[/yellow]")

    # Rechequeo
    if not _ollama_reachable(ollama_url):
        console.print("[yellow]⚠️ No puedo conectar con el servidor de Ollama.[/yellow]")
        console.print("Sugerencias:")
        console.print("- Ejecuta: [bold]ollama serve[/bold]")
        console.print("- Si estás en Linux con systemd: [bold]sudo systemctl status ollama[/bold]")
        console.print("- Verifica puerto 11434")
    else:
        console.print("[green]✅ Ollama accesible.[/green]")


def _pull_models(console: Console, models: List[str]) -> None:
    console.print("\n[bold]📦 Modelos recomendados[/bold]")
    console.print("Se descargarán SOLO si aceptas (esto puede tardar).")
    console.print(f"[cyan]Lista:[/cyan] {', '.join(models)}")
    if not shutil.which("ollama"):
        console.print("[yellow]⚠️ `ollama` no está disponible; salto el pull.[/yellow]")
        return
    if not Confirm.ask("¿Quieres hacer `ollama pull` ahora?", default=False):
        console.print("[yellow]⏭️ Saltando descarga de modelos.[/yellow]")
        return

    for m in models:
        console.print(f"\n[bold]⬇️  ollama pull {m}[/bold]")
        rc, out = _run(["ollama", "pull", m])
        if rc != 0:
            console.print("[red]❌ Falló pull[/red]")
            console.print(out)
        else:
            console.print("[green]✅ OK[/green]")


def run_wizard() -> None:
    console = Console()

    console.print(Panel.fit(ASCII_TITLE, border_style="yellow", padding=(1, 2)))
    console.print("[bold]Wizard de instalación y gateway — listo para producción local.[/bold]\n")

    # Paso 0: info
    info = Table(box=box.SIMPLE, show_header=False)
    info.add_row("OS", f"{platform.system()} {platform.release()}")
    info.add_row("Python", sys.version.split()[0])
    info.add_row("Home", str(Path.home()))
    console.print(info)

    # Paso 1: clean install
    _clean_install(console)

    # Paso 2: deps
    _ensure_python_deps(console, Path(__file__).parent / "requirements.txt")

    # Paso 3: Ollama
    ollama_url = Prompt.ask("URL de Ollama", default=DEFAULT_OLLAMA_URL).strip()
    _ensure_ollama(console, ollama_url)

    # Paso 4: modelos (ligero por defecto)
    models = ["qwen2.5:7b", "llama3", "nomic-embed-text"]
    _pull_models(console, models)

    console.print("\n[green]✅ Wizard completado.[/green]")
    console.print("Siguiente:")
    console.print("- Gateway consola: [bold]python gateway.py[/bold]")
    console.print("- Gateway web:    [bold]python web_ui.py[/bold]")


if __name__ == "__main__":
    run_wizard()
