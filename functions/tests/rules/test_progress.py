"""R-PROGRESS 就醫進度(TC-ORD-01、02、04～06、TC-PROG-01、02、TC-DATA-02、06、08、09)。"""
import pytest

from rules.candidates import next_candidates
from rules.notify import NotificationCenter
from rules.progress import EmptyTodayText, NoExamSelected, UnknownExam, Visit, push_orders

REGISTERED = frozenset({"EXAM_BLOOD", "EXAM_CXR"})
REG, CONSULT = "STEP_REGISTRATION", "STEP_CONSULT"


def visit(orders=()):
    return Visit(patient_id="MOCK-VZ2MR3", user_id="U1", orders=orders, registered_exams=REGISTERED)


def test_tc_ord_01_push_notifies_and_adds_candidate(static):
    v, c = visit(), NotificationCenter()
    v.complete_step(REG, 1)
    v.complete_step(CONSULT, 2)
    assert "ST_BLOOD_DRAW" not in next_candidates(static, orders=v.orders, completed=v.completed).stations
    assert push_orders(v, ["EXAM_BLOOD"], notifier=c) is True
    assert "ST_BLOOD_DRAW" in next_candidates(static, orders=v.orders, completed=v.completed).stations
    assert [n.text for n in c.items_for("U1")] == ["今日行程已更新，請確認下一站"]


def test_tc_ord_02_two_orders_one_notification():
    v, c = visit(), NotificationCenter()
    push_orders(v, ["EXAM_BLOOD", "EXAM_CXR"], notifier=c)
    assert set(v.orders) == {"EXAM_BLOOD", "EXAM_CXR"}
    assert len(c.items_for("U1")) == 1


def test_tc_ord_04_nothing_selected_rejected():
    v, c = visit(), NotificationCenter()
    with pytest.raises(NoExamSelected):
        push_orders(v, [], notifier=c)
    assert v.orders == () and c.items_for("U1") == []


def test_tc_ord_05_unregistered_exam_rejected_nothing_changes():
    v, c = visit(), NotificationCenter()
    with pytest.raises(UnknownExam):
        push_orders(v, ["EXAM_BLOOD", "EXAM_MRI"], notifier=c)
    assert v.orders == () and c.items_for("U1") == []


def test_tc_ord_06_existing_order_no_change_no_notification():
    v, c = visit(("EXAM_BLOOD",)), NotificationCenter()
    assert push_orders(v, ["EXAM_BLOOD"], notifier=c) is False
    assert c.items_for("U1") == []


def test_tc_prog_01_complete_step_requests_replan():
    v = visit()
    r = v.complete_step(REG, 10)
    assert r.changed and r.needs_replan
    assert REG in v.completed


def test_tc_prog_02_duplicate_step_recorded_once_earliest_kept():
    v = visit()
    v.complete_step(REG, 10)
    r = v.complete_step(REG, 5)
    assert not r.changed and not r.needs_replan
    assert v.log == [(REG, 5)]


@pytest.mark.parametrize("text", ["", "   ", "\n\t "])
def test_tc_data_02_06_blank_today_text_rejected(text):
    with pytest.raises(EmptyTodayText):
        visit().set_today_text(text)


def test_tc_data_09_text_is_trimmed():
    v = visit()
    assert v.set_today_text(" 抽血 ") == "抽血" and v.today_text == "抽血"


def test_tc_data_08_complete_step_keeps_today_text():
    v = visit()
    v.set_today_text("抽血")
    v.complete_step(REG, 1)
    assert v.today_text == "抽血"


def test_blank_text_does_not_overwrite_previous():
    v = visit()
    v.set_today_text("抽血")
    with pytest.raises(EmptyTodayText):
        v.set_today_text("  ")
    assert v.today_text == "抽血"
