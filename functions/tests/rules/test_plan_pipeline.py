"""R-ORCH 規劃流程控制(design.md 第 3、4、6 節；D-008、D-011、D-017、D-021、D-029)。

AI 客戶端、檢查者、服務台備援全部用假的注入；R-ROUTE、R-DEP、R-DESK 在階段 4 才實作。
"""
import copy

import pytest

from ai.claude_client import AiPlanResponse, AiTimeout, AiUnavailable
from ai.fake_client import FakeClock, FakePlannerClient, Step
from rules.output_guard import GuardContext
from rules.plan_pipeline import CheckUnavailable, CheckVerdict, PipelineSettings, PlanInput, run_plan

CTX = GuardContext(
    candidates=frozenset({"ST_BLOOD_DRAW", "ST_BILLING"}),
    current_node="N2_CLINIC",
    station_nodes={"ST_BLOOD_DRAW": "N2_BLOOD_DRAW", "ST_BILLING": "N1_BILLING", "ST_PHARMACY": "N1_PHARMACY"},
    node_names={
        "N2_CLINIC": "門診區", "N2_CLINIC_WAITING": "門診候診區", "N2_CORRIDOR": "二樓中央走廊",
        "N2_BLOOD_DRAW": "抽血站", "N1_BILLING": "批價櫃檯", "N1_PHARMACY": "藥局",
    },
)

GOOD = {
    "next_station_id": "ST_BLOOD_DRAW",
    "route_node_ids": ["N2_CLINIC", "N2_CLINIC_WAITING", "N2_CORRIDOR", "N2_BLOOD_DRAW"],
    "explanation": "請從門診區經門診候診區與二樓中央走廊前往抽血站。",
    "walk_minutes_estimate": 2,
    "total_minutes_estimate": None,
    "out_of_scope": False,
    "suggest_help": False,
}
BAD = dict(GOOD, next_station_id="ST_PHARMACY", route_node_ids=["N2_CLINIC", "N1_PHARMACY"],
           explanation="請前往藥局。")  # 下一站不在候選內(TC-EX-01)


def good():
    return AiPlanResponse(data=copy.deepcopy(GOOD), stop_reason="end_turn")


def bad():
    return AiPlanResponse(data=copy.deepcopy(BAD), stop_reason="end_turn")


def make_input():
    return PlanInput(
        patient={"name": "林曉安", "age": 34, "sex": "女", "orders": ["抽血"], "accessibility_need": False},
        today_text="看完診後要抽血",
        candidates=("ST_BLOOD_DRAW", "ST_BILLING"),
        current_node="N2_CLINIC",
        floor_map={"nodes": ["N2_CLINIC", "N2_BLOOD_DRAW"], "edges": []},
    )


class Spy:
    """記錄被呼叫次數的假檢查者。"""
    def __init__(self, verdict=None, error=None):
        self.verdict, self.error, self.calls = verdict or CheckVerdict(True), error, 0

    def __call__(self, output):
        self.calls += 1
        if self.error:
            raise self.error
        return self.verdict


def desk(kind):
    return {"kind": kind}


def run(steps, *, mode="rules", retry_limit=3, rules=None, agent=None, clock=None, plan_input=None, **kw):
    clock = clock or FakeClock()
    client = FakePlannerClient(steps, clock=clock)
    rules = rules or Spy()
    agent = agent or Spy()
    result = run_plan(
        plan_input or make_input(),
        client=client, guard_ctx=CTX,
        settings=PipelineSettings(checker_mode=mode, retry_limit=retry_limit),
        rule_checker=rules, agent_checker=agent, desk_fallback=desk, clock=clock.now, **kw,
    )
    return result, client, rules, agent


# ---- 重試(TC-RETRY-01～06) ----

def test_tc_retry_01_second_call_ok():
    r, client, *_ = run([bad(), good()])
    assert r.status == "published" and len(client.calls) == 2
    assert r.output["next_station_id"] == "ST_BLOOD_DRAW"


def test_tc_retry_02_fourth_call_ok_not_desk():
    r, client, *_ = run([bad(), bad(), bad(), good()])
    assert r.status == "published" and len(client.calls) == 4


def test_tc_retry_03_all_four_bad_goes_to_desk():
    r, client, *_ = run([bad(), bad(), bad(), bad(), good()])
    assert r.status == "fallback" and len(client.calls) == 4
    assert r.fallback == {"kind": "retries_exhausted"}


def test_tc_retry_04_limit_zero_goes_to_desk_after_one_call():
    r, client, *_ = run([bad(), good()], retry_limit=0)
    assert r.status == "fallback" and len(client.calls) == 1


@pytest.mark.parametrize("n", [4, -1])
def test_tc_retry_05_06_limit_out_of_range_rejected(n):
    with pytest.raises(ValueError):
        PipelineSettings(retry_limit=n)


@pytest.mark.parametrize("n", [0, 1, 2, 3])
def test_retry_limit_range_accepted(n):
    assert PipelineSettings(retry_limit=n).retry_limit == n


def test_settings_defaults():
    s = PipelineSettings()
    assert (s.checker_mode, s.retry_limit, s.call_timeout_seconds, s.total_wait_cap_seconds, s.max_tokens) == \
        ("rules", 3, 30, 60, 16000)  # D-008、D-011、D-029


def test_invalid_checker_mode_rejected():
    with pytest.raises(ValueError):
        PipelineSettings(checker_mode="both_ways")


def test_attempt_records_kept():
    r, *_ = run([bad(), good()])
    assert [a["outcome"] for a in r.attempts] == ["rejected", "published"]
    assert r.attempts[0]["failed_by"] == "guard"


# ---- 檢查者模式(TC-CHK-01～04、TC-GUARD-05) ----

def test_tc_chk_01_default_mode_is_rules_only():
    r, _, rules, agent = run([good()])
    assert r.status == "published" and rules.calls == 1 and agent.calls == 0


def test_tc_chk_02_both_agent_rejects_then_retry():
    agent = Spy(CheckVerdict(False, "agent says no"))
    r, client, rules, agent = run([good(), good()], mode="both", retry_limit=1, agent=agent)
    assert r.status == "fallback" and len(client.calls) == 2
    assert r.attempts[0]["failed_by"] == "agent"
    assert rules.calls == 2 and agent.calls == 2


def test_tc_chk_03_both_rules_reject_agent_not_called():
    rules = Spy(CheckVerdict(False, "route blocked"))
    r, _, rules, agent = run([good()], mode="both", retry_limit=0, rules=rules)
    assert r.status == "fallback" and agent.calls == 0
    assert r.attempts[0]["failed_by"] == "rules"


def test_both_pass_publishes():
    r, _, rules, agent = run([good()], mode="both")
    assert r.status == "published" and rules.calls == 1 and agent.calls == 1


def test_agent_only_mode_does_not_call_rules():
    r, _, rules, agent = run([good()], mode="agent")
    assert r.status == "published" and rules.calls == 0 and agent.calls == 1


def test_tc_chk_04_agent_result_unavailable_not_published():
    agent = Spy(error=CheckUnavailable("timeout"))
    r, _, _, agent = run([good()], mode="agent", retry_limit=0, agent=agent)
    assert r.status == "fallback" and r.output is None
    assert r.attempts[0]["failed_by"] == "agent_unavailable"


@pytest.mark.parametrize("mode", ["rules", "agent", "both"])
def test_tc_guard_05_guard_runs_in_every_mode(mode):
    r, *_ = run([bad()], mode=mode, retry_limit=0)
    assert r.status == "fallback"
    assert r.attempts[0]["failed_by"] == "guard"


# ---- AI 失敗(TC-AIF-01～04、07～09) ----

def test_tc_aif_01_unreachable_goes_to_desk_without_retry():
    r, client, *_ = run([AiUnavailable("down"), good()])
    assert r.status == "fallback" and r.fallback == {"kind": "ai_unavailable"}
    assert len(client.calls) == 1


def test_tc_aif_02_refusal_goes_to_desk():
    refusal = AiPlanResponse(data={}, stop_reason="refusal")
    r, client, *_ = run([refusal, good()])
    assert r.status == "fallback" and r.fallback == {"kind": "ai_unavailable"}
    assert len(client.calls) == 1


def test_tc_aif_03_max_tokens_counts_as_retry():
    cut = AiPlanResponse(data=copy.deepcopy(GOOD), stop_reason="max_tokens")
    r, client, *_ = run([cut, good()])
    assert r.status == "published" and len(client.calls) == 2
    assert r.attempts[0]["failed_by"] == "guard"


def test_tc_aif_04_timeout_counts_as_retry():
    r, client, *_ = run([AiTimeout("30s"), good()])
    assert r.status == "published" and len(client.calls) == 2
    assert r.attempts[0]["outcome"] == "timeout"


def test_timeout_on_every_attempt_goes_to_desk():
    r, client, *_ = run([AiTimeout("x")] * 5)
    assert r.status == "fallback" and len(client.calls) == 4
    assert r.fallback == {"kind": "retries_exhausted"}


def test_tc_aif_07_59_seconds_still_calls_again():
    r, client, *_ = run([Step(bad(), elapsed=59), good()])
    assert r.status == "published" and len(client.calls) == 2


def test_tc_aif_08_60_seconds_stops_and_goes_to_desk():
    r, client, *_ = run([Step(bad(), elapsed=60), good()])
    assert r.status == "fallback" and len(client.calls) == 1
    assert r.fallback == {"kind": "retries_exhausted"}


def test_tc_aif_09_29_second_call_ok():
    r, *_ = run([Step(good(), elapsed=29)])
    assert r.status == "published"


def test_client_receives_timeout_and_max_tokens():
    _, client, *_ = run([good()])
    assert client.calls[0]["timeout_seconds"] == 30 and client.calls[0]["max_tokens"] == 16000


# ---- 其他 ----

def test_out_of_scope_not_checked_by_checkers():
    oos = AiPlanResponse(data=dict(GOOD, out_of_scope=True, route_node_ids=[], explanation=""),
                         stop_reason="end_turn")
    r, _, rules, agent = run([oos], mode="both")
    assert r.status == "out_of_scope" and rules.calls == 0 and agent.calls == 0


def test_tc_bad_05_input_changed_during_call_is_system_error():
    plan_input = make_input()

    def tamper(inp):
        inp.patient["orders"].append("偷偷加的醫囑")
        return good()

    r, *_ = run([tamper], plan_input=plan_input)
    assert r.status == "system_error" and r.output is None
    assert r.fallback == {"kind": "ai_unavailable"}


def test_tc_prop_n6_input_unchanged_after_normal_run():
    plan_input = make_input()
    before = plan_input.digest()
    run([bad(), good()], plan_input=plan_input)
    assert plan_input.digest() == before


def test_digest_depends_on_content():
    a, b = make_input(), make_input()
    assert a.digest() == b.digest()
    b.patient["age"] = 35
    assert a.digest() != b.digest()
