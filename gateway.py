"""
    🥜 Peanut Gateway (Consola)
    ---------------------------
    UI de consola para hablar con uno o varios agentes.

    - Comandos:
/help          ayuda
/new <name>    crea sesión
/switch <name> cambia sesión
/list          lista sesiones
/reset         resetea historial de la sesión actual
/peanuts       muestra contador
/exit          salir
    """

    from __future__ import annotations

    import shlex
    from dataclasses import dataclass
    from typing import Dict, Optional

    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table

    from agent import OllamaAgent


    ASCII = r"""
     ____                  _            _                         _
    |  _ \ _ __ ___   __ _| |_ ___     / \   _ __   ___ _ __   __| |
    | |_) | '__/ _ \ / _` | __/ _ \   / _ \ | '_ \ / _ \ '_ \ / _` |
    |  __/| | | (_) | (_| | || (_) | / ___ \| |_) |  __/ | | | (_| |
    |_|   |_|  \___/ \__,_|\__\___/ /_/   \_\ .__/ \___|_| |_|\__,_|
                                             |_|
                         🥜 Gateway UI (PRO) — multi-sesión
    """.strip("\n")


    @dataclass
    class Session:
        name: str
        agent: OllamaAgent


    def _help(console: Console) -> None:
        console.print(Panel(
            "[bold]/help[/bold] ayuda\n"
            "[bold]/new <name>[/bold] crear sesión\n"
            "[bold]/switch <name>[/bold] cambiar sesión\n"
            "[bold]/list[/bold] listar sesiones\n"
            "[bold]/reset[/bold] reset historial sesión actual\n"
            "[bold]/peanuts[/bold] ver contador\n"
            "[bold]/exit[/bold] salir\n",
            title="Comandos",
            border_style="yellow",
        ))


    def main() -> None:
        console = Console()
        console.print(Panel.fit(ASCII, border_style="yellow"))

        sessions: Dict[str, Session] = {}
        current: Optional[str] = None

        def ensure_default() -> None:
            nonlocal current
            if current is None:
                name = "main"
                sessions[name] = Session(name=name, agent=OllamaAgent(model="qwen2.5:7b", temperature=0.0))
                current = name

        ensure_default()
        _help(console)

        while True:
            ensure_default()
            assert current is not None
            sess = sessions[current]

            try:
                raw = Prompt.ask(f"[bold yellow]{sess.name}[/bold yellow] 👤 Tú").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n👋 Hasta luego.")
                break

            if not raw:
                continue

            if raw.startswith("/"):
                parts = shlex.split(raw)
                cmd = parts[0].lower()

                if cmd in ["/exit", "/quit"]:
                    console.print("👋 Hasta luego.")
                    break
                if cmd == "/help":
                    _help(console)
                    continue
                if cmd == "/list":
                    t = Table(title="Sesiones", show_header=True, header_style="bold")
                    t.add_column("Nombre")
                    t.add_column("Actual")
                    t.add_column("Peanuts")
                    for name, s in sessions.items():
                        t.add_row(name, "✅" if name == current else "", str(s.agent.peanuts))
                    console.print(t)
                    continue
                if cmd == "/new":
                    if len(parts) < 2:
                        console.print("[red]Uso: /new <name>[/red]")
                        continue
                    name = parts[1]
                    if name in sessions:
                        console.print("[yellow]Ya existe esa sesión.[/yellow]")
                        continue
                    sessions[name] = Session(name=name, agent=OllamaAgent(model="qwen2.5:7b", temperature=0.0))
                    current = name
                    console.print(f"[green]✅ Sesión creada y activada:[/green] {name}")
                    continue
                if cmd == "/switch":
                    if len(parts) < 2:
                        console.print("[red]Uso: /switch <name>[/red]")
                        continue
                    name = parts[1]
                    if name not in sessions:
                        console.print("[red]No existe esa sesión.[/red]")
                        continue
                    current = name
                    console.print(f"[green]✅ Sesión activa:[/green] {name}")
                    continue
                if cmd == "/reset":
                    sess.agent.reset()
                    console.print("[green]✅ Historial reseteado.[/green]")
                    continue
                if cmd == "/peanuts":
                    console.print(f"🥜 Peanuts: [bold]{sess.agent.peanuts}[/bold]")
                    continue

                console.print("[red]Comando desconocido. Usa /help[/red]")
                continue

            # Mensaje normal
            console.print(Panel("⏳ Pensando…", border_style="cyan"))
            resp = sess.agent.chat(raw, verbose=False)
            console.print(Panel(resp, title=f"🤖 {sess.name}", border_style="green"))


    if __name__ == "__main__":
        main()
