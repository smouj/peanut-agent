# 🧙 Wizard

Ejecuta:

```bash
python wizard.py
```

Hace:
1) Ofrece **instalación limpia** (borrar `~/.peanut-agent`)
2) Comprueba dependencias Python y ejecuta `pip install -r requirements.txt`
3) Verifica Ollama:
   - binario en PATH
   - servidor accesible en `http://localhost:11434`
4) Descarga opcional de modelos con `ollama pull`

Si no encuentra Ollama:
- Linux/macOS: usa `scripts/install_ollama.sh`
- Windows: muestra instrucciones y `scripts/install_ollama.ps1`
