# 🆘 Troubleshooting

## Ollama no responde
- Inicia: `ollama serve`
- Linux (systemd): `sudo systemctl status ollama`
- Verifica puerto: 11434

## No carga la web (18789)
- ¿Puerto ocupado? Cambia `APP_PORT` en `web_ui.py`
- Firewall: permite tráfico local

## Tool calling raro / JSON sucio
- Baja la temperatura (ya es 0.0 por defecto)
- Reduce herramientas (TOOLS_SCHEMA) si el modelo se lía
- Revisa logs del agente con `--verbose`

## Memoria demasiado grande
- `memory.jsonl` es append-only. Puedes borrarlo si quieres reset:
  `rm ~/.peanut-agent/memory.jsonl`
