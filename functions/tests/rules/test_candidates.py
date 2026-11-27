"""R-CAND 下一站候選(TC-CAND-01～07、TC-EX-01 第 1、4 步)。"""
import pytest

from rules.candidates import next_candidates
from rules.static_data import MissingStaticData, StaticData

REG, CONSULT = "STEP_REGISTRATION", "STEP_CONSULT"


def names(static, cand):
    return {static.station_names[s] for s in cand.stations}


def test_tc_cand_01_no_orders(static, patients):
    c = next_candidates(static, orders=patients["黃宜蓁"]["orders"], completed={REG, CONSULT})
    assert names(static, c) == {"批價櫃檯"}


def test_tc_cand_02_empty_progress(static, patients):
    c = next_candidates(static, orders=patients["林曉安"]["orders"], completed=set())
    assert names(static, c) == {"掛號報到櫃檯"}


def test_tc_cand_03_only_blood_order(static):
    c = next_candidates(static, orders=["EXAM_BLOOD"], completed={REG, CONSULT})
    assert names(static, c) == {"抽血站", "批價櫃檯"}


def test_tc_cand_04_two_orders(static, patients):
    c = next_candidates(static, orders=patients["張建宏"]["orders"], completed={REG, CONSULT})
    assert names(static, c) == {"抽血站", "放射檢查站", "批價櫃檯"}


def test_tc_cand_05_pharmacy_needs_billing(static):
    c = next_candidates(static, orders=[], completed={REG, CONSULT})
    assert "ST_PHARMACY" not in c.stations


def test_tc_cand_06_pharmacy_after_billing(static):
    c = next_candidates(static, orders=[], completed={REG, CONSULT, "STEP_BILLING"})
    assert c.stations == frozenset({"ST_PHARMACY"})


def test_tc_cand_07_consistent_ten_times(static):
    results = {next_candidates(static, orders=["EXAM_BLOOD"], completed={REG, CONSULT}) for _ in range(10)}
    assert len(results) == 1


def test_tc_ex_01_step1_candidates_exclude_pharmacy(static, patients):
    c = next_candidates(static, orders=patients["林曉安"]["orders"], completed={REG, CONSULT})
    assert c.stations == frozenset({"ST_BLOOD_DRAW", "ST_BILLING"})
    assert c.steps == ("STEP_BILLING", "STEP_BLOOD_DRAW")  # 排序固定


def test_tc_ex_01_step4_after_blood_draw(static):
    c = next_candidates(static, orders=["EXAM_BLOOD"], completed={REG, CONSULT, "STEP_BLOOD_DRAW"})
    assert c.stations == frozenset({"ST_REPORT_WAITING", "ST_BILLING"})
    assert "ST_PHARMACY" not in c.stations


def test_all_done_no_candidates(static):
    done = {s.id for s in static.steps}
    assert next_candidates(static, orders=["EXAM_BLOOD", "EXAM_CXR"], completed=done).stations == frozenset()


def test_unknown_when_rule_rejected(raw):
    raw["flow"]["steps"][0]["when"] = "weekday:mon"
    with pytest.raises(ValueError):
        next_candidates(StaticData.from_raw(raw, version="v1"), orders=[], completed=set())


def test_tc_data_04_missing_table_raises(raw):
    raw["flow"] = None
    with pytest.raises(MissingStaticData):
        next_candidates(StaticData.from_raw(raw, version="v1"), orders=[], completed=set())
