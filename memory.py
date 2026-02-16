"""
🥜 Peanut Memory (RAG Local Ligero)
----------------------------------
Memoria de "éxitos pasados" con embeddings locales (Ollama) + fallback sin dependencias.

- Almacenamiento: JSONL (append-only) en ~/.peanut-agent/memory.jsonl
- Similaridad: cosine similarity
- Embeddings: Ollama /api/embeddings (por defecto: nomic-embed-text)
- Fallback: embedding hash determinista (cuando no hay Ollama embeddings)

Objetivo: mantenerlo MUY ligero y fácil de portar/offline.
"""

from __future__ import annotations

import json
import math
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    """Una memoria de éxito pasada."""
    id: str
    ts: float = Field(default_factory=lambda: time.time())
    task: str
    tool_name: str
    tool_args: Dict[str, Any]
    tool_result_preview: str = ""
    embedding: List[float]


@dataclass(frozen=True)
class OllamaClient:
    ollama_url: str = "http://localhost:11434"
    timeout_s: int = 60

    def embeddings(self, model: str, prompt: str) -> List[float]:
        payload = {"model": model, "prompt": prompt}
        resp = requests.post(f"{self.ollama_url}/api/embeddings", json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()
        emb = data.get("embedding")
        if not isinstance(emb, list) or not emb:
            raise ValueError("Embeddings vacíos")
        return [float(x) for x in emb]


def _tokenize(text: str) -> List[str]:
    text = text.lower()
    # tokens simples, offline-friendly
    return re.findall(r"[a-z0-9_áéíóúñü]+", text, flags=re.IGNORECASE)


def _hash_embedding(text: str, dim: int = 128) -> List[float]:
    """Embedding determinista por hashing (fallback sin Ollama)."""
    import hashlib

    vec = [0.0] * dim
    toks = _tokenize(text)
    if not toks:
        return vec
    for t in toks[:512]:
        h = hashlib.sha256(t.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "little") % dim
        sign = 1.0 if (h[4] % 2 == 0) else -1.0
        vec[idx] += sign
    # normalizar
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    denom = math.sqrt(na) * math.sqrt(nb)
    if denom == 0.0:
        return -1.0
    return dot / denom


def _quantize(vec: List[float], decimals: int = 4) -> List[float]:
    """Reduce tamaño en disco (aprox) redondeando."""
    return [round(float(x), decimals) for x in vec]


class PeanutMemory:
    """
    Memoria local del agente.

    Uso:
        mem = PeanutMemory()
        mem.add_memory(task, {"tool": ..., "args": ..., "result": ...})
        examples = mem.retrieve_memory(task)
    """

    def __init__(
        self,
        *,
        storage_dir: Optional[str] = None,
        ollama_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
        max_entries: int = 500,
    ) -> None:
        self.storage_dir = Path(storage_dir or (Path.home() / ".peanut-agent"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.storage_dir / "memory.jsonl"
        self.ollama_url = ollama_url
        self.embedding_model = embedding_model
        self.max_entries = max_entries

        self._cache: List[MemoryEntry] = []
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._cache = []
        if self.memory_file.exists():
            with self.memory_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = MemoryEntry.model_validate(data)
                        self._cache.append(entry)
                    except Exception:
                        continue
        # Mantener solo las más recientes
        self._cache.sort(key=lambda e: e.ts, reverse=True)
        self._cache = self._cache[: self.max_entries]
        self._loaded = True

    def _embed(self, text: str) -> List[float]:
        # Intentar Ollama embeddings
        try:
            client = OllamaClient(ollama_url=self.ollama_url, timeout_s=60)
            vec = client.embeddings(self.embedding_model, text)
            return _quantize(vec)
        except Exception:
            return _hash_embedding(text)

    def add_memory(self, task: str, successful_tool_call: Dict[str, Any]) -> None:
        """
        Guarda una memoria de un tool call exitoso.

        successful_tool_call esperado:
            {
                "tool_name": str,
                "tool_args": dict,
                "tool_result": Any (opcional)
            }
        """
        self._load()

        tool_name = str(successful_tool_call.get("tool_name", "")).strip() or "unknown"
        tool_args = successful_tool_call.get("tool_args")
        if not isinstance(tool_args, dict):
            tool_args = {}

        tool_result = successful_tool_call.get("tool_result")
        try:
            preview = json.dumps(tool_result, ensure_ascii=False)[:600]
        except Exception:
            preview = str(tool_result)[:600]

        emb = self._embed(task)

        entry = MemoryEntry(
            id=f"mem_{int(time.time() * 1000)}",
            task=task,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result_preview=preview,
            embedding=emb,
        )

        # append-only (seguro)
        with self.memory_file.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json(ensure_ascii=False) + "\n")

        # actualizar cache
        self._cache.insert(0, entry)
        self._cache = self._cache[: self.max_entries]

    def retrieve_memory(self, current_task: str, *, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Recupera ejemplos de tareas similares.

        Returns:
            Lista de ejemplos: [{"task": ..., "tool_name": ..., "tool_args": ...}, ...]
        """
        self._load()
        if not self._cache:
            return []

        q = self._embed(current_task)
        scored: List[Tuple[float, MemoryEntry]] = []
        for entry in self._cache:
            score = _cosine(q, entry.embedding)
            scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        best = [e for s, e in scored[: max(1, int(top_k))] if s > 0.10]  # umbral suave
        out: List[Dict[str, Any]] = []
        for e in best:
            out.append({
                "task": e.task,
                "tool_name": e.tool_name,
                "tool_args": e.tool_args,
                "tool_result_preview": e.tool_result_preview,
            })
        return out
