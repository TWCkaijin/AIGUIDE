"""R-WL 白名單(FR-07、FR-22；D-006、D-030)。"""
import copy

from rules.whitelist import WHITELIST_FIELDS, build_llm_patient

PATIENT = {
    "mock_id": "MOCK-AAAAAA",
    "name": "林曉安",
    "age": 34,
    "sex": "女",
    "orders": ["EXAM_BLOOD"],
    "accessibility_need": False,
    "_scenario": "測試用情境說明",
}


def test_whitelist_fields_are_exactly_d006():
    # D-006：只有姓名、年齡、性別、醫囑、無障礙需求
    assert set(WHITELIST_FIELDS) == {"name", "age", "sex", "orders", "accessibility_need"}


def test_tc_wl_01_only_five_fields_sent():
    out = build_llm_patient(PATIENT)
    assert set(out) == set(WHITELIST_FIELDS)
    assert out["name"] == "林曉安" and out["orders"] == ["EXAM_BLOOD"]


def test_tc_wl_02_mock_id_and_scenario_dropped():
    out = build_llm_patient(PATIENT)
    assert "mock_id" not in out and "_scenario" not in out


def test_tc_wl_03_empty_orders_kept():
    p = dict(PATIENT, orders=[])
    assert build_llm_patient(p)["orders"] == []


def test_tc_wl_04_unknown_field_dropped():
    p = dict(PATIENT, phone="0900000000")
    assert "phone" not in build_llm_patient(p)


def test_tc_data_01_missing_accessibility_treated_as_no_need():
    # D-030：缺少無障礙需求時視為「無需求」
    p = {k: v for k, v in PATIENT.items() if k != "accessibility_need"}
    assert build_llm_patient(p)["accessibility_need"] is False


def test_input_not_mutated():
    # P2：AI 相關處理不得改動原始輸入
    original = copy.deepcopy(PATIENT)
    out = build_llm_patient(PATIENT)
    out["orders"].append("X")
    assert PATIENT == original
