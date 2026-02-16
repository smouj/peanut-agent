# 🥜 QUICKSTART — PEANUT-AGENT PRO

## Opción A: Local (recomendado)

1) Instala dependencias:

```bash
python -m pip install -r requirements.txt
```

2) Ejecuta wizard:

```bash
python wizard.py
```

3) Abre gateway:

- Consola: `python gateway.py`
- Web: `python web_ui.py` → http://127.0.0.1:18789/

## Opción B: Docker Compose

```bash
docker compose up --build
```

- Ollama: http://127.0.0.1:11434
- Gateway: http://127.0.0.1:18789

## Modelos sugeridos
```bash
ollama pull qwen2.5:7b
ollama pull llama3
ollama pull nomic-embed-text
```
