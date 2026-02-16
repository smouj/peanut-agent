import pytest

from agentlow.agent import OllamaAgent
from agentlow.tools import ToolExecutor


@pytest.fixture
def agent(tmp_path, monkeypatch):
    """Agente en modo unit-test.

    En CI normalmente NO hay un servidor Ollama ejecutándose.
    Para que los tests sean deterministas y no dependan de red/servicios,
    mockeamos la llamada a Ollama devolviendo un "echo" del prompt.
    """

    a = OllamaAgent(
        model="qwen2.5:7b",
        work_dir=str(tmp_path),
        temperature=0.0,
    )

    def _fake_call_ollama(messages, tools=None):
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = str(m.get("content", ""))
                break

        original = last_user.split("\n\n", 1)[1] if "\n\n" in last_user else last_user
        return {"message": {"content": f"Echo: {original}"}}

    monkeypatch.setattr(a, "_call_ollama", _fake_call_ollama)
    return a


def test_agent_init(agent):
    assert agent.model == "qwen2.5:7b"
    assert len(agent.messages) == 0


def test_tool_executor(tmp_path):
    executor = ToolExecutor(work_dir=str(tmp_path))
    write_result = executor.execute_tool("write_file", {"path": "test.txt", "content": "Hello"})
    assert write_result["success"]
    read_result = executor.execute_tool("read_file", {"path": "test.txt"})
    assert read_result["content"] == "Hello"


def test_agent_run_simple(agent):
    response = agent.run("Echo test", verbose=False)
    assert "test" in response.lower()


def test_cache(agent):
    # Si luego implementas caché real, este test sigue válido
    # mientras el modelo/mock sea determinista.
    first = agent.run("Lista archivos", verbose=False)
    second = agent.run("Lista archivos", verbose=False)
    assert first == second
