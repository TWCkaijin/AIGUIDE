"""R-METRIC 成效指標(FR-25；D-014)。"""
from fractions import Fraction

from rules.metrics import indicator_b, segment_stats, target_a_met, target_b_met

# 指標 B 的必要步驟與前置條件(取自 test-cases.md 2.17 人工推算範例)
REQUIRED = {
    "掛號報到": [],
    "看診": ["掛號報到"],
    "抽血": ["看診"],
    "批價": ["看診"],
    "領藥": ["批價"],
}


def test_tc_met_01_example_60_percent():
    logs = [("掛號報到", 1), ("看診", 2), ("抽血", 3), ("領藥", 5)]
    r = indicator_b(REQUIRED, logs, cancelled=set())
    assert (r.numerator, r.denominator) == (3, 5)
    assert r.rate_percent == Fraction(60)
    assert r.missing_log_count == 1


def test_tc_met_02_no_required_steps_not_counted():
    r = indicator_b({}, [], cancelled=set())
    assert r.rate_percent is None


def test_tc_met_03_cancelled_step_removed_from_denominator():
    logs = [("掛號報到", 1), ("看診", 2), ("批價", 3), ("領藥", 4)]
    r = indicator_b(REQUIRED, logs, cancelled={"抽血"})
    assert (r.numerator, r.denominator) == (4, 4)
    assert r.missing_log_count == 0


def test_tc_met_04_duplicate_log_counted_once():
    logs = [("掛號報到", 1), ("掛號報到", 1.5), ("看診", 2)]
    r = indicator_b({"掛號報到": [], "看診": ["掛號報到"]}, logs, cancelled=set())
    assert (r.numerator, r.denominator) == (2, 2)


def test_wrong_order_counts_as_incorrect():
    # 領藥先於批價登錄：順序不符，留在分母
    logs = [("掛號報到", 1), ("看診", 2), ("抽血", 3), ("領藥", 4), ("批價", 5)]
    r = indicator_b(REQUIRED, logs, cancelled=set())
    assert (r.numerator, r.denominator) == (4, 5)


SEG = ("ST_CLINIC", "ST_BLOOD_DRAW")


def test_tc_met_05_segment_average():
    stats = segment_stats([
        {"segment": SEG, "start": 0, "end": 120},
        {"segment": SEG, "start": 1000, "end": 1180},
    ])
    s = stats[SEG]
    assert s.valid_count == 2 and s.average_seconds == Fraction(150)


def test_tc_met_06_aborted_not_in_average():
    stats = segment_stats([
        {"segment": SEG, "start": 0, "end": 120},
        {"segment": SEG, "start": 500, "end": None},
    ])
    s = stats[SEG]
    assert s.valid_count == 1 and s.average_seconds == Fraction(120)
    assert s.aborted_count == 1


def test_segments_counted_separately():
    other = ("ST_BILLING", "ST_PHARMACY")
    stats = segment_stats([
        {"segment": SEG, "start": 0, "end": 100},
        {"segment": other, "start": 0, "end": 40},
    ])
    assert stats[SEG].average_seconds == 100 and stats[other].average_seconds == 40


def test_tc_met_07_reduction_exactly_10_percent_met():
    assert target_a_met(baseline_seconds=200, trial_seconds=180) is True


def test_tc_met_08_reduction_9_5_percent_not_met():
    assert target_a_met(baseline_seconds=200, trial_seconds=181) is False


def test_tc_met_09_b_exactly_95_met():
    assert target_b_met(rate_percent=95.0, baseline_percent=90) is True


def test_tc_met_10_b_94_9_not_met():
    assert target_b_met(rate_percent=94.9, baseline_percent=90) is False


def test_tc_met_11_b_below_baseline_not_met():
    assert target_b_met(rate_percent=96, baseline_percent=97) is False
