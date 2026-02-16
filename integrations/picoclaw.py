"""
🧩 PicoClaw Integration (ligera)
--------------------------------
PicoClaw suele referirse a frameworks/implementaciones ultraligeras para agentes.
Aquí dejamos un "adaptador" mínimo para:

- Detectar binario/CLI si existe
- Ejecutar comandos básicos (status/help)
- Proveer hooks para conectar PicoClaw como backend de agentes en el futuro

Nota:
- No descarga dependencias pesadas por defecto.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class PicoClaw:
    """Wrapper mínimo para un CLI `picoclaw` si está instalado."""
    executable: str = "picoclaw"

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def run(self, args: list[str], timeout_s: int = 20) -> Tuple[int, str]:
        if not self.available():
            return 127, "picoclaw no encontrado en PATH"
        p = subprocess.run([self.executable, *args], capture_output=True, text=True, timeout=timeout_s)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out.strip()

    def status(self) -> str:
        rc, out = self.run(["--help"])
        if rc == 0:
            return "✅ PicoClaw disponible"
        return f"⚠️ PicoClaw: {out}"


def install_hint() -> str:
    return (
        "PicoClaw es opcional. Si quieres integrarlo:\n"
        "- Instálalo según el repo/guía que estés usando.\n"
        "- Asegura que el binario `picoclaw` esté en PATH.\n"
        "- Luego podrás activar el backend PicoClaw desde el wizard (próxima iteración).\n"
    )
