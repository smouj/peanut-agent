# 🥜 Arquitectura — PEANUT-AGENT PRO v0.1

## Objetivo
Hacer que modelos pequeños (7B) se comporten “como grandes” en automatización, **no** por magia del modelo, sino por arquitectura:
- herramientas bien descritas y seguras,
- validación estricta,
- auto-corrección (reflection),
- memoria de éxitos pasados (RAG local).

## Componentes

### 1) Agent Core (`agent.py`)
- Mantiene historial de mensajes
- Llama a Ollama `/api/chat` con `TOOLS_SCHEMA`
- Ejecuta herramientas mediante `ToolExecutor`
- Post-procesa con Reflection Loop
- Persiste y consulta Peanut Memory
- Gamificación (`~/.peanut-agent/state.json`)

### 2) Tools (`tools.py`)
- Allowlist de comandos shell
- Prevención de path traversal en `read_file/write_file/list_directory`
- Timeouts defensivos

### 3) Reflection Loop (`reflection.py`)
- Modelo Pydantic `PeanutReflection`
- Llama a Ollama para auditar tool outputs
- Si el JSON sale “sucio”, intenta extraer/validar; si no, fallback heurístico

### 4) Memory RAG (`memory.py`)
- JSONL append-only (`~/.peanut-agent/memory.jsonl`)
- Embeddings vía `/api/embeddings` (default `nomic-embed-text`)
- Fallback sin dependencias: embedding por hashing determinista
- Recupera `top_k` ejemplos por similitud coseno

### 5) Gateways
- Consola: `gateway.py` (Rich, multi-sesión)
- Web: `web_ui.py` (FastAPI + WebSocket) con `web/index.html`

## Flujo de ejecución

1) Usuario envía tarea
2) `retrieve_memory(task)` -> ejemplos
3) Se construye System Prompt con “Consejos del pasado”
4) Ollama sugiere tool calls
5) Se ejecuta herramienta
6) Reflection audita
   - si falla: reintento con improved_input (hasta 3)
   - si éxito: sumar peanut + guardar memoria

## Principios de diseño
- **Local-first**: todo corre en local, sin servicios externos obligatorios
- **Robustez**: tolerancia a JSON imperfecto
- **Seguridad**: herramientas minimalistas y con guardas
