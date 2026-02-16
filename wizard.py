"""
🥜 Peanut Wizard (PRO)
----------------------

Wizard interactivo "bonito" para preparar el entorno de PEANUT-AGENT.

Objetivo:
- Instalación en 1 comando (después de clonar el repo).
- Aislado por defecto: crea y usa un entorno virtual local .venv/
- Seguridad: NO ejecuta comandos destructivos; solo instala dependencias del proyecto,
  guía instalación de Ollama y ofrece limpieza de estado.

Ejecutar:
    python wizard.py

Atajos:
    python wizard.py --yes        # Aceptar valores por defecto (menos preguntas)
    python wizard.py --clean      # Forzar instalación limpia (borrar ~/.peanut-agent)
    python wizard.py --no-pull    # No hacer "ollama pull" de modelos
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

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
    """Ejecuta un comando y devuelve (returncode, stdout+stderr)."""
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out.strip()


def _is_venv() -> bool:
    """True si el proceso corre dentro de un virtualenv."""
    return sys.prefix != sys.base_prefix


def _venv_python(venv_dir: Path) -> Path:
    if platform.system().lower().startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _print_plain(title: str, lines: List[str]) -> None:
    print("\n" + title)
    print("-" * max(10, len(title)))
    for ln in lines:
        print(ln)


def _create_or_update_venv(project_root: Path, venv_dir: Path, requirements_path: Path) -> None:
    """Crea .venv e instala dependencias dentro del venv."""
    if not requirements_path.exists():
        raise SystemExit(f"No encuentro requirements.txt en: {requirements_path}")

    if not venv_dir.exists():
        _print_plain(
            "🧪 Creando entorno virtual",
            [f"Ruta: {venv_dir}", "Esto es local al proyecto y no toca tu sistema."],
        )
        rc, out = _run([sys.executable, "-m", "venv", str(venv_dir)])
        if rc != 0:
            raise SystemExit(f"Falló crear venv:\n{out}")

    vpy = _venv_python(venv_dir)
    if not vpy.exists():
        raise SystemExit(f"No encuentro el Python del venv: {vpy}")

    _print_plain("📦 Instalando dependencias", ["Actualizando pip…"])
    rc, out = _run([str(vpy), "-m", "pip", "install", "--upgrade", "pip"])
    if rc != 0:
        raise SystemExit(f"Falló actualizar pip:\n{out}")

    _print_plain("📦 Instalando dependencias", [f"pip install -r {requirements_path.name}"])
    rc, out = _run([str(vpy), "-m", "pip", "install", "-r", str(requirements_path)])
    if rc != 0:
        raise SystemExit(f"Falló instalar dependencias:\n{out}")


def _reexec_in_venv(project_root: Path, venv_dir: Path, argv: List[str]) -> None:
    """Re-ejecuta este wizard dentro del venv para usar Rich/requests con UI completa."""
    vpy = _venv_python(venv_dir)
    if not vpy.exists():
        raise SystemExit(f"No encuentro el Python del venv: {vpy}")

    # Evitar bucle infinito: añadimos flag interno.
    new_argv = [str(vpy), str(project_root / "wizard.py"), "--_in-venv"] + argv
    rc = subprocess.call(new_argv)
    raise SystemExit(rc)


def _ask_yes_no(question: str, default: bool) -> bool:
    """Pregunta simple (sin Rich) para fase bootstrap."""
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        ans = input(f"{question} {suffix}: ").strip().lower()
    except EOFError:
        return default
    if not ans:
        return default
    return ans in {"y", "yes", "s", "si", "sí"}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True)

    p.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="URL de Ollama (default: http://localhost:11434)")
    p.add_argument("--clean", action="store_true", help="Forzar instalación limpia (borra ~/.peanut-agent)")
    p.add_argument("--yes", action="store_true", help="Aceptar valores por defecto y reducir preguntas")
    p.add_argument("--no-venv", action="store_true", help="No crear/usar .venv (no recomendado)")
    p.add_argument("--no-pull", action="store_true", help="No ejecutar ollama pull de modelos")

    # Flag interno para evitar re-ejecución infinita.
    p.add_argument("--_in-venv", action="store_true", help=argparse.SUPPRESS)

    return p.parse_args()


def _ollama_reachable(requests_mod, ollama_url: str, timeout_s: int = 2) -> bool:
    try:
        r = requests_mod.get(f"{ollama_url}/api/tags", timeout=timeout_s)
        return r.status_code == 200
    except Exception:
        return False


def run_wizard() -> None:
    args = _parse_args()
    project_root = Path(__file__).resolve().parent
    venv_dir = project_root / ".venv"
    requirements_path = project_root / "requirements.txt"

    # --- Bootstrap: venv + deps (solo stdlib aquí) ---
    if not args._in_venv and not args.no_venv and not _is_venv():
        if args.yes:
            create = True
        else:
            create = _ask_yes_no("¿Crear/usar entorno virtual local .venv y auto-instalar dependencias?", True)

        if create:
            _create_or_update_venv(project_root, venv_dir, requirements_path)
            # Re-ejecutar dentro del venv para UI completa
            passthrough = []
            for raw in sys.argv[1:]:
                if raw == "--_in-venv":
                    continue
                passthrough.append(raw)
            _reexec_in_venv(project_root, venv_dir, passthrough)
        else:
            _print_plain(
                "⚠️ Instalación sin .venv",
                [
                    "Continuarás usando tu Python del sistema.",
                    "Si faltan paquetes, ejecuta: python -m pip install -r requirements.txt",
                ],
            )

    # --- UI completa (requiere deps) ---
    try:
        import requests  # type: ignore
        from rich import box  # type: ignore
        from rich.console import Console  # type: ignore
        from rich.panel import Panel  # type: ignore
        from rich.prompt import Confirm, Prompt  # type: ignore
        from rich.table import Table  # type: ignore
    except Exception as e:
        _print_plain(
            "❌ Dependencias faltantes",
            [
                f"Error importando UI/deps: {e}",
                "Solución rápida:",
                "  python -m pip install -r requirements.txt",
                "O ejecuta el wizard sin --no-venv para auto-instalar en .venv.",
            ],
        )
        raise SystemExit(1)

    console = Console()
    console.print(Panel.fit(ASCII_TITLE, border_style="yellow", padding=(1, 2)))
    console.print("[bold]Wizard de instalación y gateway — listo para producción local.[/bold]\n")

    # Info
    info = Table(box=box.SIMPLE, show_header=False)
    info.add_row("OS", f"{platform.system()} {platform.release()}")
    info.add_row("Python", sys.version.split()[0])
    info.add_row("Root", str(project_root))
    info.add_row("Venv", "✅ .venv" if _is_venv() else "⚠️ sistema")
    info.add_row("State", str(STATE_DIR))
    console.print(info)

    # Paso 1: instalación limpia
    console.print("\n[bold]🧼 Instalación limpia[/bold]")
    if args.clean:
        do_clean = True
    else:
        do_clean = False
        if STATE_DIR.exists():
            console.print(f"[yellow]Detectado estado previo en:[/yellow] {STATE_DIR}")
            do_clean = Confirm.ask("¿Quieres borrar datos existentes antes de continuar?", default=False)

    if do_clean and STATE_DIR.exists():
        confirm = "BORRAR" if args.yes else Prompt.ask("Escribe BORRAR para confirmar", default="")
        if confirm.strip().upper() != "BORRAR":
            console.print("[red]Cancelado. No se borró nada.[/red]")
        else:
            shutil.rmtree(STATE_DIR, ignore_errors=True)
            console.print("[green]✅ Datos borrados.[/green]")
    elif not STATE_DIR.exists():
        console.print("[green]✅ No hay datos previos.[/green]")

    # Paso 2: Ollama
    console.print("\n[bold]🧠 Ollama[/bold]")
    ollama_url = args.ollama_url.strip()
    has_bin = shutil.which("ollama") is not None
    reachable = _ollama_reachable(requests, ollama_url)

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Chequeo")
    table.add_column("Estado")
    table.add_row("Binario `ollama`", "✅" if has_bin else "❌")
    table.add_row(f"Servidor ({ollama_url})", "✅" if reachable else "❌")
    console.print(table)

    if not has_bin:
        console.print("[yellow]ℹ️ No encuentro `ollama` en PATH.[/yellow]")
        sysname = platform.system().lower()
        if sysname in ["linux", "darwin"]:
            auto_install = True if args.yes else Confirm.ask(
                "¿Intentar instalar Ollama ahora? (usa scripts/install_ollama.sh)",
                default=True,
            )
            if auto_install:
                script = project_root / "scripts" / "install_ollama.sh"
                if not script.exists():
                    console.print("[red]❌ No encuentro scripts/install_ollama.sh[/red]")
                    raise SystemExit(1)
                script.chmod(0o755)
                rc, out = _run(["bash", str(script)], cwd=project_root)
                if out:
                    console.print(out)
                if rc != 0:
                    raise SystemExit(1)
        else:
            console.print(
                "[yellow]➡️ En Windows, ejecuta scripts/install_ollama.ps1 o instala desde ollama.com/download[/yellow]"
            )

    # Rechequeo conectividad
    if not _ollama_reachable(requests, ollama_url):
        console.print("[yellow]⚠️ No puedo conectar con el servidor de Ollama.[/yellow]")
        console.print("Sugerencias:")
        console.print("- Ejecuta: [bold]ollama serve[/bold]")
        console.print("- Verifica el puerto 11434")
    else:
        console.print("[green]✅ Ollama accesible.[/green]")

    # Paso 3: modelos (ligero)
    console.print("\n[bold]📦 Modelos recomendados[/bold]")
    models = ["qwen2.5:7b", "llama3", "nomic-embed-text"]
    console.print(f"[cyan]Lista:[/cyan] {', '.join(models)}")

    if args.no_pull:
        console.print("[yellow]⏭️ Saltando descarga de modelos (--no-pull).[/yellow]")
    else:
        if shutil.which("ollama") is None:
            console.print("[yellow]⚠️ `ollama` no está disponible; salto el pull.[/yellow]")
        else:
            do_pull = True if args.yes else Confirm.ask("¿Quieres hacer `ollama pull` ahora?", default=False)
            if do_pull:
                for m in models:
                    console.print(f"\n[bold]⬇️  ollama pull {m}[/bold]")
                    rc, out = _run(["ollama", "pull", m], cwd=project_root)
                    if rc != 0:
                        console.print("[red]❌ Falló pull[/red]")
                        if out:
                            console.print(out)
                    else:
                        console.print("[green]✅ OK[/green]")
            else:
                console.print("[yellow]⏭️ Saltando descarga de modelos.[/yellow]")

    console.print("\n[green]✅ Wizard completado.[/green]")
    console.print("Siguiente:")
    console.print("- Gateway consola: [bold]python gateway.py[/bold]")
    console.print("- Gateway web:    [bold]python web_ui.py[/bold]")


if __name__ == "__main__":
    run_wizard()
