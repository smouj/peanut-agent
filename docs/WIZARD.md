# 🧙 Wizard

El wizard es el **punto de entrada recomendado** para instalar y preparar PEANUT-AGENT en local.

## Ejecutar

```bash
python wizard.py
```

## Qué hace

1) **(Por defecto) crea y usa `.venv/`**
- Si no estás en un virtualenv, el wizard propone crear `.venv/` en la raíz del repo.
- Instala dependencias dentro del venv y se re‑ejecuta automáticamente con UI completa.

2) **Ofrece instalación limpia**
- Si detecta estado previo en `~/.peanut-agent`, te pregunta si quieres borrarlo.

3) **Verifica Ollama**
- Detecta si existe el binario `ollama`.
- Comprueba si el servidor responde en `http://localhost:11434` (o el `--ollama-url` que indiques).

4) **Modelos recomendados (opcional)**
- Sugiere: `qwen2.5:7b`, `llama3`, `nomic-embed-text`.
- Puede ejecutar `ollama pull` si lo apruebas.

## Opciones útiles

- `--yes` → acepta valores por defecto y reduce preguntas.
- `--clean` → fuerza instalación limpia (borra `~/.peanut-agent`).
- `--no-pull` → no descarga modelos.
- `--ollama-url http://host:11434` → usa otra URL de Ollama.
- `--no-venv` → evita `.venv/` (no recomendado).

## Si no encuentra Ollama

- Linux/macOS: puede usar `scripts/install_ollama.sh`.
- Windows: sugiere `scripts/install_ollama.ps1` o instalar desde la web oficial.
