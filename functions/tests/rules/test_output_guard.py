"""R-GUARD 輸出檢查(design.md 第 4 節；D-020、D-021、D-022)。

測試夾具取自 test-cases.md TC-EX-01 的一部分(林曉安，目前位置門診區)。
"""
import json

import pytest

from rules.output_guard import GuardContext, check_plan_output

CTX = GuardContext(
    candidates=frozenset({"ST_BLOOD_DRAW", "ST_BILLING"}),
    current_node="N2_CLINIC",
    station_nodes={
        "ST_BLOOD_DRAW": "N2_BLOOD_DRAW",
        "ST_BILLING": "N1_BILLING",
        "ST_PHARMACY": "N1_PHARMACY",
    },
    node_names={
        "N2_CLINIC": "門診區",
        "N2_CLINIC_WAITING": "門診候診區",
        "N2_CORRIDOR": "二樓中央走廊",
        "N2_BLOOD_DRAW": "抽血站",
        "N1_BILLING": "批價櫃檯",
        "N1_PHARMACY": "藥局",
    },
    forbidden_strings=("MOCK-AAAAAA",),
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


def run(output=None, stop_reason="end_turn", **changes):
    data = dict(GOOD if output is None else output)
    data.update(changes)
    return check_plan_output(data, stop_reason=stop_reason, ctx=CTX)


def codes(result):
    return {e.split(":")[0] for e in result.errors}


# ---- 一般 ----

def test_tc_guard_01_good_output_passes():
    r = run()
    assert r.ok, r.errors


def test_good_output_as_json_string_passes():
    r = check_plan_output(json.dumps(GOOD, ensure_ascii=False), stop_reason="end_turn", ctx=CTX)
    assert r.ok, r.errors


# ---- 格式(TC-PROP-F1～F6) ----

def test_tc_bad_04_unparsable_json():
    r = check_plan_output("{not json", stop_reason="end_turn", ctx=CTX)
    assert not r.ok and "format.invalid_json" in codes(r)


def test_tc_guard_02_missing_next_station():
    data = {k: v for k, v in GOOD.items() if k != "next_station_id"}
    r = run(output=data)
    assert not r.ok and "format.missing_field" in codes(r)


def test_extra_field_rejected():
    r = run(diagnosis="感冒")
    assert not r.ok and "format.extra_field" in codes(r)


def test_tc_guard_03_two_stations_rejected():
    r = run(next_station_id=["ST_BLOOD_DRAW", "ST_BILLING"])
    assert not r.ok and "format.type" in codes(r)


@pytest.mark.parametrize("field,value", [
    ("route_node_ids", "N2_CLINIC"),
    ("explanation", 123),
    ("walk_minutes_estimate", "2"),
    ("total_minutes_estimate", True),
    ("out_of_scope", "false"),
    ("suggest_help", 0),
])
def test_field_types(field, value):
    r = run(**{field: value})
    assert not r.ok and "format.type" in codes(r)


@pytest.mark.parametrize("value", [None, 0, -3, 2.5])
def test_time_estimate_number_or_null_passes_guard(value):
    # D-026：0 或負數不算不合格，只在畫面上改顯示「暫無估計」
    assert run(walk_minutes_estimate=value).ok


@pytest.mark.parametrize("reason", ["refusal", "max_tokens"])
def test_tc_aif_02_03_bad_stop_reason(reason):
    r = run(stop_reason=reason)
    assert not r.ok and "format.stop_reason" in codes(r)


# ---- 一定要有(TC-PROP-M1～M3) ----

def test_tc_guard_04_next_station_not_candidate():
    # TC-EX-01：候選 {抽血、批價}，AI 選了藥局
    r = run(next_station_id="ST_PHARMACY",
            route_node_ids=["N2_CLINIC", "N1_PHARMACY"],
            explanation="請前往藥局。")
    assert not r.ok and "must.next_station_not_candidate" in codes(r)


def test_tc_route_02_route_does_not_reach_station():
    r = run(route_node_ids=["N2_CLINIC", "N2_CLINIC_WAITING"],
            explanation="請前往門診候診區。")
    assert not r.ok and "must.route_end" in codes(r)


def test_tc_route_03_empty_route():
    r = run(route_node_ids=[])
    assert not r.ok and "must.route_start" in codes(r)


def test_route_must_start_at_current_node():
    r = run(route_node_ids=["N2_CORRIDOR", "N2_BLOOD_DRAW"],
            explanation="請從二樓中央走廊前往抽血站。")
    assert not r.ok and "must.route_start" in codes(r)


@pytest.mark.parametrize("text", ["", "   "])
def test_empty_explanation(text):
    r = run(explanation=text)
    assert not r.ok and "must.explanation_empty" in codes(r)


# ---- 一定不能有(TC-PROP-N1～N4) ----

def test_tc_route_08_unknown_node():
    r = run(route_node_ids=["N2_CLINIC", "N9_XXX", "N2_BLOOD_DRAW"])
    assert not r.ok and "not.unknown_node" in codes(r)


def test_explanation_mentions_station_not_in_route():
    r = run(explanation="請前往抽血站，之後再去藥局。")
    assert not r.ok and "not.station_name_outside_route" in codes(r)


def test_explanation_may_mention_route_nodes():
    assert run(explanation="經過二樓中央走廊到抽血站。").ok


def test_forbidden_patient_string():
    r = run(explanation="MOCK-AAAAAA 請前往抽血站。")
    assert not r.ok and "not.forbidden_string" in codes(r)


# ---- 超出範圍(TC-SCOPE-03) ----

def test_tc_scope_03_out_of_scope_skips_guidance_checks():
    r = run(out_of_scope=True, next_station_id="ST_PHARMACY",
            route_node_ids=[], explanation="")
    assert r.ok, r.errors
    assert r.out_of_scope is True


def test_out_of_scope_still_checks_format():
    r = run(out_of_scope=True, explanation=None)
    assert not r.ok and "format.type" in codes(r)
