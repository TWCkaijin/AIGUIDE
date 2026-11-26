"""A-CLIENT 模型呼叫介面(AC-NFR01.1、AC-NFR01.2；TC-WL-01、TC-AIF-01～04、TC-AIF-06)。

不呼叫真實 API；真實呼叫在階段 7。
"""
import json
import logging

import pytest

from ai.claude_client import (
    MODEL_ID, AiPlanResponse, AiTimeout, AiUnavailable, ClaudePlannerClient, build_request,
)
from ai.fake_client import FakeClock, FakePlannerClient, Step
from rules.plan_pipeline import PipelineSettings, PlanInput
from rules.whitelist import WHITELIST_FIELDS, build_llm_patient


def make_input():
    patient = build_llm_patient({
        "mock_id": "MOCK-AAAAAA", "name": "林曉安", "age": 34, "sex": "女",
        "orders": ["抽血"], "accessibility_need": False, "secret": "x",
    })
    return PlanInput(patient=patient, today_text="看完診後要抽血", candidates=("ST_BLOOD_DRAW",),
                     current_node="N2_CLINIC", floor_map={"nodes": [], "edges": []})


def test_tc_wl_01_request_patient_has_exactly_whitelist_fields():
    req = build_request(make_input(), PipelineSettings(), system_prompt="SYS")
    body = json.loads(req["messages"][0]["content"])
    assert set(body["patient"]) == set(WHITELIST_FIELDS)
    assert "MOCK-AAAAAA" not in req["messages"][0]["content"]


def test_request_uses_haiku_and_settings():
    req = build_request(make_input(), PipelineSettings(), system_prompt="SYS")
    assert req["model"] == MODEL_ID == "claude-haiku-5-5"
    assert req["max_tokens"] == 16000 and req["timeout"] == 30
    assert req["system"] == "SYS"


def test_request_has_no_write_tools():
    req = build_request(make_input(), PipelineSettings(), system_prompt="SYS")
    assert "tools" not in req or all(t.get("read_only") for t in req["tools"])


def test_tc_aif_06_missing_key_logs_error_and_plan_unavailable(caplog):
    with caplog.at_level(logging.ERROR):
        client = ClaudePlannerClient(api_key=None, system_prompt="SYS")
    assert any("ANTHROPIC_API_KEY" in r.message for r in caplog.records)
    with pytest.raises(AiUnavailable):
        client.plan(make_input(), timeout_seconds=30, max_tokens=16000)


def test_key_comes_from_environment_not_arguments_default(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert ClaudePlannerClient.from_env(system_prompt="SYS").has_key is True
    monkeypatch.delenv("ANTHROPIC_API_KEY")
    assert ClaudePlannerClient.from_env(system_prompt="SYS").has_key is False


# ---- 假客戶端 ----

def test_fake_returns_steps_in_order_and_records_calls():
    ok = AiPlanResponse(data={"a": 1}, stop_reason="end_turn")
    fake = FakePlannerClient([ok, AiTimeout("t")])
    assert fake.plan(make_input(), timeout_seconds=30, max_tokens=10) is ok
    with pytest.raises(AiTimeout):
        fake.plan(make_input(), timeout_seconds=30, max_tokens=10)
    assert len(fake.calls) == 2


def test_fake_advances_clock():
    clock = FakeClock()
    fake = FakePlannerClient([Step(AiPlanResponse(data={}, stop_reason="end_turn"), elapsed=29)], clock=clock)
    fake.plan(make_input(), timeout_seconds=30, max_tokens=10)
    assert clock.now() == 29


def test_fake_runs_out_of_steps():
    fake = FakePlannerClient([])
    with pytest.raises(AssertionError):
        fake.plan(make_input(), timeout_seconds=30, max_tokens=10)


def test_ai_timeout_is_ai_error_but_not_unavailable():
    assert not issubclass(AiTimeout, AiUnavailable)
