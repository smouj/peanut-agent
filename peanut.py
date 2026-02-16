"""
🥜 Peanut CLI (PRO)
-------------------
Entrada única para:
- wizard
- gateway (consola)
- web (FastAPI)
- run (ejecución única)

Ejemplos:
    python peanut.py wizard
    python peanut.py gateway
    python peanut.py web
    python peanut.py run "lista los archivos"
"""

from __future__ import annotations

import argparse
import sys

from agent import OllamaAgent


def cmd_wizard(_: argparse.Namespace) -> None:
    from wizard import run_wizard
    run_wizard()


def cmd_gateway(_: argparse.Namespace) -> None:
    import gateway
    gateway.main()


def cmd_web(_: argparse.Namespace) -> None:
    import web_ui
    web_ui.main()


def cmd_run(args: argparse.Namespace) -> None:
    agent = OllamaAgent(model=args.model, temperature=args.temperature, max_iterations=args.max_iterations)
    agent.reset()
    out = agent.run(args.task, verbose=args.verbose)
    print(out)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="peanut", description="🥜 Peanut Agent PRO")
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("wizard", help="Wizard de instalación")
    w.set_defaults(func=cmd_wizard)

    g = sub.add_parser("gateway", help="Gateway UI consola")
    g.set_defaults(func=cmd_gateway)

    web = sub.add_parser("web", help="Gateway UI web (FastAPI)")
    web.set_defaults(func=cmd_web)

    r = sub.add_parser("run", help="Ejecutar una tarea única")
    r.add_argument("task", help="Texto de la tarea")
    r.add_argument("--model", default="qwen2.5:7b")
    r.add_argument("--temperature", type=float, default=0.0)
    r.add_argument("--max-iterations", type=int, default=10)
    r.add_argument("--verbose", action="store_true", help="Ver logs del loop")
    r.set_defaults(func=cmd_run)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    ns = parser.parse_args(argv)
    ns.func(ns)


if __name__ == "__main__":
    main(sys.argv[1:])
