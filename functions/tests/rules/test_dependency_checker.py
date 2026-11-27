"""R-DEP 依賴檢查，及與 R-ROUTE 組成的規則檢查者(TC-EX-01、TC-CAND-05／06)。"""
from ai.claude_client import AiPlanResponse  # noqa: F401  (確認規則層測試可同時載入 AI 層)
from rules.dependency_check import check_dependencies
from rules.plan_pipeline import CheckVerdict
from rules.rule_checker import make_rule_checker

REG, CONSULT = "STEP_REGISTRATION", "STEP_CONSULT"


def test_tc_ex_01_blood_draw_after_consult_ok(static):
    v = check_dependencies(static, "ST_BLOOD_DRAW", orders=["EXAM_BLOOD"], completed={REG, CONSULT})
    assert v.ok, v.reason


def test_tc_ex_01_pharmacy_before_billing_rejected(static):
    v = check_dependencies(static, "ST_PHARMACY", orders=["EXAM_BLOOD"], completed={REG, CONSULT})
    assert not v.ok and v.reason.startswith("dep.requires_not_done")
    assert "STEP_BILLING" in v.reason


def test_tc_cand_06_pharmacy_after_billing_ok(static):
    v = check_dependencies(static, "ST_PHARMACY", orders=[], completed={REG, CONSULT, "STEP_BILLING"})
    assert v.ok


def test_station_without_pending_step_rejected(static):
    v = check_dependencies(static, "ST_RADIOLOGY", orders=[], completed={REG, CONSULT})  # 沒有 X 光醫囑
    assert not v.ok and v.reason.startswith("dep.no_pending_step")


def test_already_done_step_rejected(static):
    v = check_dependencies(static, "ST_BILLING", orders=[], completed={REG, CONSULT, "STEP_BILLING"})
    assert not v.ok


def test_unknown_station_rejected(static):
    assert not check_dependencies(static, "ST_NOWHERE", orders=[], completed=set()).ok


GOOD = {
    "next_station_id": "ST_BLOOD_DRAW",
    "route_node_ids": ["N2_CLINIC", "N2_CLINIC_WAITING", "N2_CORRIDOR", "N2_BLOOD_DRAW"],
    "explanation": "x", "walk_minutes_estimate": 2, "total_minutes_estimate": None,
    "out_of_scope": False, "suggest_help": False,
}


def checker(static, **kw):
    args = dict(patient_orders=["EXAM_BLOOD"], completed={REG, CONSULT}, current_node="N2_CLINIC",
                accessibility_need=False)
    args.update(kw)
    return make_rule_checker(static, **args)


def test_rule_checker_passes_good_output(static):
    v = checker(static)(GOOD)
    assert isinstance(v, CheckVerdict) and v.ok, v.reason


def test_rule_checker_rejects_bad_route(static):
    bad = dict(GOOD, route_node_ids=["N2_CLINIC", "N2_CORRIDOR", "N2_BLOOD_DRAW"])
    v = checker(static)(bad)
    assert not v.ok and v.reason.startswith("route.")


def test_rule_checker_rejects_dependency_violation(static):
    bad = dict(GOOD, next_station_id="ST_PHARMACY", route_node_ids=["N2_CLINIC", "N2_CORRIDOR"])
    v = checker(static)(bad)
    assert not v.ok


def test_rule_checker_dependency_only(static):
    # 路線沒問題但依賴不符：reason 為 dep.*
    out = dict(GOOD, next_station_id="ST_RADIOLOGY")
    out["route_node_ids"] = ["N2_CLINIC", "N2_CLINIC_WAITING", "N2_CORRIDOR", "N2_ELEVATOR", "N1_ELEVATOR",
                             "N1_CORRIDOR_E", "N1_RADIOLOGY"]
    v = checker(static)(out)
    assert not v.ok and v.reason.startswith("dep.")
