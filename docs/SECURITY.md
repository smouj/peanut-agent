# 🔒 Seguridad

PEANUT-AGENT PRO aplica un enfoque “deny by default”.

## Shell allowlist
En `tools.py` solo se permiten comandos de lectura y diagnóstico.
Se bloquean explícitamente:
- `rm`, `sudo`, `chmod`, `chown`, `dd`, `mkfs`, etc.

> Consejo: reduce aún más la allowlist si lo vas a exponer como servicio.

## Prevención de Path Traversal
En `read_file/write_file/list_directory`:
- se resuelven paths,
- se verifica que estén dentro de `work_dir`,
- si no, se rechaza.

## Timeouts
- Shell: 30s
- Docker: 60s
- HTTP: 30s
- Ollama chat: 120s (agente), 60s (reflexión)

## Modo Gateway Web
`web_ui.py` escucha por defecto en `0.0.0.0:18789` para facilitar Docker/VPS,
pero en local puedes cambiar a `127.0.0.1` si quieres cerrarlo.

## Recomendaciones para VPS
- reverse proxy con auth
- TLS
- IP allowlist / VPN (Tailscale/WireGuard)
- no ejecutes el agente con permisos root
