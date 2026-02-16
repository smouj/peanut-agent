# 🧠 Reflection + Memory

## Reflection Loop
El objetivo es que el agente pueda **auto-corregirse** sin que tú intervengas.

**Entrada:**
- tool_name
- user_input (tarea)
- tool_output

**Salida (Pydantic `PeanutReflection`):**
- success: bool
- analysis: str
- peanuts_earned: 0|1
- next_action: retry|finalize
- improved_input: str|null (idealmente JSON)

Si el modelo devuelve texto extra o JSON inválido:
- se intenta extraer el primer objeto JSON,
- si falla, se usa fallback heurístico.

## Peanut Memory (RAG local)
Guarda éxitos reales:
- task
- tool_name
- tool_args
- tool_result_preview
- embedding

Recupera `top_k=2` ejemplos y los inyecta en el system prompt como:
`🥜 CONSEJOS DEL PASADO: [...]`

### Embeddings
- Primario: Ollama `/api/embeddings` con `nomic-embed-text`
- Fallback: embedding por hashing determinista (sin dependencias)
