from reflection import reflect_on_result

def test_reflection_fallback_error():
    r = reflect_on_result("shell", "listar archivos", {"error": "something went wrong"}, model="qwen2.5:7b")
    assert r.success is False
    assert r.peanuts_earned == 0
    assert r.next_action in ("retry", "finalize")

if __name__ == "__main__":
    test_reflection_fallback_error()
    print("OK")
