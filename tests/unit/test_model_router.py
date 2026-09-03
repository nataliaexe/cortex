from core.model_router import ModelRouter


def test_routes_fast_coding_and_reasoning_profiles():
    router = ModelRouter({"llm": {"models": {}}})
    assert router.select("qual o status?").profile == "fast"
    assert router.select("refatore este código Python").profile == "coding"
    assert router.select("faça um planejamento complexo de arquitetura").profile == "reasoning"
