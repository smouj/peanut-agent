"""
🥜 Peanut Gateway (Web)
-----------------------
FastAPI + WebSocket UI para hablar con múltiples agentes.

Ejecutar:
    python web_ui.py

Luego abre:
    http://127.0.0.1:18789/
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from agent import OllamaAgent


APP_PORT = 18789
STATIC_INDEX = Path(__file__).parent / "web" / "index.html"


class NewSessionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)


class ResetRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=40)


def _sanitize_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^a-zA-Z0-9_\-\.]", "-", name)
    return name[:40] or "main"


@dataclass
class Session:
    name: str
    agent: OllamaAgent


app = FastAPI(title="Peanut Gateway PRO", version="0.1")

sessions: Dict[str, Session] = {}
current_session: str = "main"


def get_or_create(name: str) -> Session:
    global current_session
    name = _sanitize_name(name)
    if name not in sessions:
        sessions[name] = Session(name=name, agent=OllamaAgent(model="qwen2.5:7b", temperature=0.0))
    current_session = name
    return sessions[name]


# Crear default
get_or_create("main")


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    if STATIC_INDEX.exists():
        return HTMLResponse(STATIC_INDEX.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Peanut Gateway</h1><p>Falta web/index.html</p>")


@app.get("/api/sessions")
async def list_sessions() -> dict:
    return {"sessions": sorted(sessions.keys()), "current": current_session}


@app.post("/api/new")
async def new_session(req: NewSessionRequest) -> dict:
    s = get_or_create(req.name)
    return {"ok": True, "name": s.name}


@app.post("/api/reset")
async def reset_session(req: ResetRequest) -> dict:
    name = _sanitize_name(req.name)
    if name in sessions:
        sessions[name].agent.reset()
        return {"ok": True}
    return {"ok": False, "error": "Sesión no encontrada"}


@app.websocket("/ws/{session_name}")
async def ws_chat(websocket: WebSocket, session_name: str) -> None:
    await websocket.accept()
    sess = get_or_create(session_name)

    await websocket.send_text(json.dumps({"type": "sys", "message": f"Sesión activa: {sess.name}"}))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                msg = str(data.get("message", "")).strip()
            except Exception:
                msg = raw.strip()

            if not msg:
                continue

            # Ejecutar (no verboso)
            reply = sess.agent.chat(msg, verbose=False)
            await websocket.send_text(json.dumps({
                "type": "reply",
                "reply": reply,
                "peanuts": sess.agent.peanuts,
            }, ensure_ascii=False))

    except WebSocketDisconnect:
        return


def main() -> None:
    import uvicorn
    uvicorn.run("web_ui:app", host="0.0.0.0", port=APP_PORT, reload=False)


if __name__ == "__main__":
    main()
