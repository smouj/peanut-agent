# Changelog — 🥜 PEANUT-AGENT PRO

## v0.1 (2026-02-16)
- Añadido: Reflection Loop (`reflection.py`) con esquema Pydantic + fallback heurístico.
- Añadido: Peanut Memory (`memory.py`) RAG local ligero (JSONL + embeddings Ollama).
- Modificado: `agent.py` integrado con memory+reflection y gamificación.
- Añadido: Wizard bonito (`wizard.py`) con instalación limpia y checks.
- Añadido: Gateway consola (`gateway.py`) multi-sesión.
- Añadido: Gateway web (`web_ui.py` + `web/index.html`) con WebSocket.
- Añadido: Dockerfile + docker-compose simplificados para Ollama + gateway.
