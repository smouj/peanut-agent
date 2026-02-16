import tempfile
from pathlib import Path

from memory import PeanutMemory

def test_memory_add_and_retrieve():
    with tempfile.TemporaryDirectory() as d:
        mem = PeanutMemory(storage_dir=d, ollama_url="http://127.0.0.1:1")  # fuerza fallback hash
        mem.add_memory("listar archivos", {"tool_name": "list_directory", "tool_args": {"path": "."}, "tool_result": {"files": []}})
        res = mem.retrieve_memory("listar archivos del proyecto", top_k=2)
        assert isinstance(res, list)
        assert len(res) >= 1
        assert res[0]["tool_name"] == "list_directory"

if __name__ == "__main__":
    test_memory_add_and_retrieve()
    print("OK")
