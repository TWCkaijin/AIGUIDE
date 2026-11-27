"""R-QUEUE 模擬叫號與時間欄位顯示規則(TC-TIME-01～04、06、TC-DATA-03、TC-DATA-10；D-007、D-026、D-034)。"""
import pytest

from rules.queue_mock import MockQueue, format_estimate

DATA = {
    "ST_BLOOD_DRAW": {"wait_minutes": 12, "current_number": "A035"},
    "ST_BILLING": {"wait_minutes": 8},               # 只缺 (c)
}


def test_full_data_labelled_as_mock():
    d = MockQueue(DATA).display("ST_BLOOD_DRAW")
    assert (d.wait_text, d.number_text) == ("12", "A035")
    assert d.source_label == "模擬叫號資料"


def test_tc_data_03_station_without_data():
    d = MockQueue(DATA).display("ST_PHARMACY")
    assert (d.wait_text, d.number_text) == ("暫無資料", "暫無資料")


def test_tc_data_10_only_c_missing():
    d = MockQueue(DATA).display("ST_BILLING")
    assert (d.wait_text, d.number_text) == ("8", "暫無資料")


def test_zero_minutes_is_data_not_missing():
    d = MockQueue({"S": {"wait_minutes": 0, "current_number": "A001"}}).display("S")
    assert d.wait_text == "0"


def test_tc_time_03_ai_failed_queue_still_shown():
    assert format_estimate(None).text == "暫無估計"
    assert MockQueue(DATA).display("ST_BLOOD_DRAW").wait_text == "12"


def test_tc_time_01_estimate_tagged():
    e = format_estimate(2)
    assert e.text == "2" and e.tag == "AI 估計（原型示意）"


def test_tc_time_02_null_shows_no_estimate_without_tag():
    e = format_estimate(None)
    assert e.text == "暫無估計" and e.tag is None


@pytest.mark.parametrize("v", [0, -3])
def test_tc_time_04_zero_or_negative_shows_no_estimate(v):
    e = format_estimate(v)
    assert e.text == "暫無估計" and e.tag is None


def test_tc_time_06_one_shown_no_upper_limit():
    assert format_estimate(1).text == "1"
    assert format_estimate(100000).text == "100000"


def test_float_estimate_kept():
    assert format_estimate(2.5).text == "2.5"
