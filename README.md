# 🥜 PEANUT-AGENT — PRO v0.1

**Agente autónomo local-first** optimizado para modelos pequeños (7B) en **Ollama**, con:

- ✅ **Tool Calling** (JSON) con **allowlist + anti-path-traversal**
- ✅ **Reflection Loop** (auto-corrección de tool args, hasta 3 reintentos)
- ✅ **Peanut Memory (RAG local)**: aprende de éxitos pasados (embeddings locales)
- ✅ **Gateway UI**:
  - **Consola** (Rich) multi-sesión
  - **Web** (FastAPI + WebSocket) estilo terminal

> Filosofía: **Local • Offline-friendly • Seguro • Modular**.

---

## 🚀 Quickstart (lo más rápido)

### 1) Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

### 2) Ejecutar el Wizard

```bash
python wizard.py
```

El wizard:
- detecta si falta Ollama y te guía a instalarlo,
- ofrece **instalación limpia** (borrar `~/.peanut-agent`),
- sugiere modelos recomendados (`qwen2.5:7b`, `llama3`, `nomic-embed-text`).

### 3) Abrir un Gateway

**Gateway consola (multi-sesión):**
```bash
python gateway.py
```

**Gateway web (estilo terminal):**
```bash
python web_ui.py
# abre: http://127.0.0.1:18789/
```

---

## 🧠 Cómo funciona

### Tool Calling seguro
La ejecución de herramientas vive en `tools.py`:
- Allowlist de comandos (sin `rm`, `sudo`, etc.)
- Protección contra **path traversal**
- Timeouts defensivos

### Reflection Loop
Después de cada tool call:
1. Se ejecuta la herramienta
2. `reflection.reflect_on_result()` audita el output
3. Si falla, sugiere **improved_input** (idealmente JSON) y se reintenta (máx 3)

### Peanut Memory (RAG local)
Antes de actuar:
- `memory.retrieve_memory(task)` busca tareas similares (top 2)
- Se inyectan ejemplos reales en el System Prompt:
  - `🥜 CONSEJOS DEL PASADO: [...]`

Cuando hay éxito:
- `memory.add_memory(task, tool_call)` guarda (task + tool + args + embedding)

---

## 🥜 Gamificación (Modo Experto)
Se guarda en `~/.peanut-agent/state.json`

- `peanuts <= 10`: Modo Normal
- `peanuts > 10`: **MODO EXPERTO** (system prompt más “afilado”)

---

## 📦 Estructura

```
.
├─ agent.py              # Agente principal (tools + reflection + memory)
├─ tools.py              # Ejecutores de herramientas (seguridad)
├─ reflection.py         # Reflection Loop (Pydantic + Ollama)
├─ memory.py             # RAG local ligero (JSONL + embeddings)
├─ wizard.py             # Wizard bonito (Rich)
├─ gateway.py            # Gateway consola multi-sesión (Rich)
├─ web_ui.py             # Gateway web (FastAPI + WS) puerto 18789
├─ web/
│  └─ index.html         # UI terminal web
├─ integrations/
│  └─ picoclaw.py        # Integración opcional (ligera)
└─ docs/
   ├─ ARCHITECTURE.md
   ├─ SECURITY.md
   ├─ REFLECTION_MEMORY.md
   ├─ WIZARD.md
   └─ TROUBLESHOOTING.md
```

---

## 🔒 Seguridad

Lee: `docs/SECURITY.md`

Resumen:
- allowlist estricta para shell
- bloqueos contra comandos destructivos
- prevención de paths fuera de `work_dir`

---

## 🧩 PicoClaw (opcional)
Hay un adaptador mínimo en `integrations/picoclaw.py`.

Por defecto **no descarga nada pesado**. Se integra cuando tengas el binario/CLI disponible.

---

## 🆘 Soporte rápido

- ¿Ollama no responde? Ejecuta `ollama serve` o revisa el servicio.
- ¿No aparece el puerto 18789? Revisa firewall/puertos en uso.
- ¿Modelos? `ollama list` y `ollama pull qwen2.5:7b`

Más en `docs/TROUBLESHOOTING.md`.

---

## Licencia
MIT — ver `LICENSE`.
