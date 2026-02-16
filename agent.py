"""
🥜 Peanut Agent - PRO v0.1
--------------------------
Agente local con Ollama + Tool Calling + Reflection Loop + Peanut Memory (RAG local).

Puntos clave:
- Tool calling con allowlist y protección de paths (tools.py)
- Reflection Loop: auto-corrección de tool args (reflection.py)
- Memory RAG: recuperación de éxitos pasados e inyección en prompt (memory.py)
- Gamificación: contador de cacahuetes persistente (>=10 activa "Modo Experto")
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from tools import ToolExecutor, TOOLS_SCHEMA
from reflection import reflect_on_result
from memory import PeanutMemory


@dataclass
class PeanutState:
    """Estado persistente mínimo (peanuts)."""
    storage_dir: Path

    def __post_init__(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.storage_dir / "state.json"

    def load_peanuts(self) -> int:
        try:
            if not self.state_file.exists():
                return 0
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            val = int(data.get("peanuts", 0))
            return max(0, val)
        except Exception:
            return 0

    def save_peanuts(self, peanuts: int) -> None:
        peanuts = max(0, int(peanuts))
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"peanuts": peanuts}, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.state_file)


class OllamaAgent:
    """Agente que usa Ollama con tool calling + memoria + reflexión."""

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434"),
        work_dir: Optional[str] = None,
        temperature: float = 0.0,
        max_iterations: int = 10,
        enable_reflection: bool = True,
        enable_memory: bool = True,
        max_tool_retries: int = 3,
        peanut_home: Optional[str] = None,
        embedding_model: str = "nomic-embed-text",
    ) -> None:
        self.model = model
        self.ollama_url = ollama_url
        self.executor = ToolExecutor(work_dir)
        self.temperature = float(temperature)
        self.max_iterations = int(max_iterations)
        self.enable_reflection = bool(enable_reflection)
        self.enable_memory = bool(enable_memory)
        self.max_tool_retries = max(1, int(max_tool_retries))

        self.peanut_dir = Path(peanut_home or (Path.home() / ".peanut-agent"))
        self.state = PeanutState(self.peanut_dir)
        self.peanuts = self.state.load_peanuts()

        self.memory = PeanutMemory(
            storage_dir=str(self.peanut_dir),
            ollama_url=self.ollama_url,
            embedding_model=embedding_model,
        )

        # Historial de conversación (se conserva en chat())
        self.messages: List[Dict[str, Any]] = []

    def _call_ollama(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        if tools:
            payload["tools"] = tools

        try:
            response = requests.post(f"{self.ollama_url}/api/chat", json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Error llamando a Ollama: {str(e)}"}

    def _get_enriched_context(self) -> str:
        """Contexto enriquecido defensivo."""
        parts = [
            f"📂 Directorio actual: {self.executor.work_dir}",
            f"👤 Usuario: {os.getenv('USER', os.getenv('USERNAME', 'unknown'))}",
        ]

        # Archivos visibles
        try:
            files = list(self.executor.work_dir.iterdir())[:12]
            if files:
                parts.append("📄 Archivos visibles: " + ", ".join([f.name for f in files]))
        except Exception:
            pass

        # Git status si existe
        try:
            result = subprocess.run(
                ["git", "status", "-s"],
                cwd=str(self.executor.work_dir),
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                parts.append("🔀 Git: " + result.stdout.strip()[:140])
        except Exception:
            pass

        return "\n".join(parts)

    def _build_system_prompt(self, memories: List[Dict[str, Any]]) -> str:
        mode = "MODO EXPERTO" if self.peanuts > 10 else "MODO NORMAL"
        tips = ""
        if memories:
            pretty = json.dumps(memories, ensure_ascii=False, indent=2)[:2000]
            tips = f"\n\n🥜 CONSEJOS DEL PASADO (ejemplos reales):\n{pretty}\n"

        return (
            f"Eres 🥜Peanut Agent PRO. {mode}.\n"
            "Objetivo: completar tareas de automatización usando herramientas.\n"
            "Reglas:\n"
            "- Si usas herramientas, pide SOLO las necesarias.\n"
            "- Mantén JSON limpio en tool args.\n"
            "- Respeta la seguridad: no intentes comandos destructivos ni paths fuera del work_dir.\n"
            "- Cuando hayas terminado, responde con una salida final clara.\n"
            f"{tips}"
        )

    def _ensure_system_message(self, content: str) -> None:
        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0]["content"] = content
            return
        self.messages.insert(0, {"role": "system", "content": content})

    def _try_json(self, s: str) -> Optional[Dict[str, Any]]:
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                return obj
        except Exception:
            return None
        return None

    def _reflect_and_maybe_retry(
        self,
        *,
        tool_name: str,
        task: str,
        tool_args: Dict[str, Any],
        tool_result: Any,
        verbose: bool,
    ) -> Any:
        """
        Ejecuta reflexión y reintentos automáticos (hasta max_tool_retries).
        Devuelve el resultado final (posiblemente mejorado).
        """
        if not self.enable_reflection:
            return tool_result

        reflection = reflect_on_result(
            tool_name=tool_name,
            user_input=task,
            tool_output=tool_result,
            model=self.model,
            ollama_url=self.ollama_url,
            temperature=0.0,
            timeout_s=60,
        )

        if verbose:
            status = "✅" if reflection.success else "❌"
            print(f"   🥜 Reflection {status}: {reflection.analysis}")

        if reflection.success:
            self.peanuts += int(reflection.peanuts_earned)
            self.state.save_peanuts(self.peanuts)

            if self.enable_memory:
                self.memory.add_memory(
                    task,
                    {
                        "tool_name": tool_name,
                        "tool_args": tool_args,
                        "tool_result": tool_result,
                    },
                )
            return tool_result

        improved = (reflection.improved_input or "").strip()
        if not improved:
            return tool_result

        current_result = tool_result
        for attempt in range(1, self.max_tool_retries + 1):
            improved_args = self._try_json(improved)
            if improved_args is None:
                if verbose:
                    print("   ⚠️ improved_input no es JSON válido; no se puede reintentar automáticamente.")
                return current_result

            if verbose:
                print(f"   🔁 Reintento {attempt}/{self.max_tool_retries} con args mejorados…")

            new_result = self.executor.execute_tool(tool_name, improved_args)

            reflection2 = reflect_on_result(
                tool_name=tool_name,
                user_input=task,
                tool_output=new_result,
                model=self.model,
                ollama_url=self.ollama_url,
                temperature=0.0,
                timeout_s=60,
            )

            if verbose:
                status = "✅" if reflection2.success else "❌"
                print(f"   🥜 Reflection {status}: {reflection2.analysis}")

            if reflection2.success:
                self.peanuts += int(reflection2.peanuts_earned)
                self.state.save_peanuts(self.peanuts)

                if self.enable_memory:
                    self.memory.add_memory(
                        task,
                        {
                            "tool_name": tool_name,
                            "tool_args": improved_args,
                            "tool_result": new_result,
                        },
                    )
                return new_result

            improved = (reflection2.improved_input or "").strip()
            current_result = new_result
            if not improved:
                return current_result

        return current_result

    def run(self, user_input: str, verbose: bool = True) -> str:
        """Ejecuta una tarea (no resetea historial; usa reset() si quieres limpio)."""

        memories: List[Dict[str, Any]] = []
        if self.enable_memory:
            try:
                memories = self.memory.retrieve_memory(user_input, top_k=2)
            except Exception:
                memories = []

        self._ensure_system_message(self._build_system_prompt(memories))

        context = self._get_enriched_context()
        enhanced_input = f"{context}\n\n{user_input}"

        self.messages.append({"role": "user", "content": enhanced_input})

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1

            if verbose:
                print(f"\n{'=' * 72}")
                print(f"🔄 Iteración {iteration}/{self.max_iterations} | 🥜 Peanuts: {self.peanuts}")
                print(f"{'=' * 72}")

            response = self._call_ollama(self.messages, TOOLS_SCHEMA)

            if "error" in response:
                return f"❌ Error: {response['error']}"

            message = response.get("message", {}) or {}

            if not message.get("tool_calls"):
                final_content = message.get("content", "") or ""
                self.messages.append({"role": "assistant", "content": final_content})

                if verbose:
                    print("\n✅ Respuesta final:\n" + final_content)

                return final_content

            tool_calls = message.get("tool_calls", []) or []
            if verbose:
                print(f"\n🔧 Herramientas solicitadas: {len(tool_calls)}")

            self.messages.append({
                "role": "assistant",
                "content": message.get("content", "") or "",
                "tool_calls": tool_calls,
            })

            for tool_call in tool_calls:
                fn = ((tool_call.get("function") or {}).get("name") or "").strip()
                arg_str = (tool_call.get("function") or {}).get("arguments") or ""

                if not fn:
                    result = {"error": "Tool call sin nombre de función"}
                    self.messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})
                    continue

                try:
                    args = json.loads(arg_str) if isinstance(arg_str, str) else (arg_str or {})
                    if not isinstance(args, dict):
                        raise ValueError("Arguments no es objeto JSON")
                except Exception as e:
                    if verbose:
                        print(f"⚠️  JSON inválido en {fn}: {e}")
                    result = {"error": f"JSON inválido: {str(e)}. Devuelve SOLO JSON válido para arguments."}
                    self.messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})
                    continue

                if verbose:
                    print(f"\n▶️  Ejecutando: {fn}")
                    print(f"   Args: {json.dumps(args, ensure_ascii=False)[:180]}")

                result = self.executor.execute_tool(fn, args)

                if verbose:
                    preview = json.dumps(result, ensure_ascii=False)[:260]
                    print(f"   ✓ Resultado: {preview}")

                final_result = self._reflect_and_maybe_retry(
                    tool_name=fn,
                    task=user_input,
                    tool_args=args,
                    tool_result=result,
                    verbose=verbose,
                )

                self.messages.append({"role": "tool", "content": json.dumps(final_result, ensure_ascii=False)})

        return f"⚠️ Se alcanzó el límite de {self.max_iterations} iteraciones sin respuesta final."

    def chat(self, user_input: str, verbose: bool = False) -> str:
        """Modo chat (mantiene historial)."""
        return self.run(user_input, verbose=verbose)

    def reset(self) -> None:
        """Reinicia el historial (mantiene peanuts y memoria en disco)."""
        self.messages = []

    def get_history(self) -> List[Dict[str, Any]]:
        """Devuelve historial de mensajes."""
        return self.messages


def main() -> None:
    print("🥜 Peanut Agent PRO — Gateway consola rápido")
    print("=" * 72)
    print("Tip: Ejecuta el wizard primero:  python wizard.py")
    print("=" * 72)

    agent = OllamaAgent(model="qwen2.5:7b", temperature=0.0, max_iterations=10)

    agent.reset()
    while True:
        try:
            user_input = input("\n👤 Tú: ").strip()
            if user_input.lower() in ["salir", "exit", "quit", "/exit"]:
                print("👋 ¡Hasta luego!")
                break
            if not user_input:
                continue
            response = agent.chat(user_input, verbose=False)
            print(f"\n🤖 Agente: {response}")
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break


if __name__ == "__main__":
    main()
