"""R-NOTIFY 站內通知(TC-ORD-01／02、TC-IMP-05；D-013、D-015)。"""
from rules.notify import SCHEDULE_UPDATED_TEXT, NotificationCenter


def test_schedule_updated_text_fixed_and_without_order_names():
    c = NotificationCenter()
    n = c.send_schedule_updated("U1")
    assert n.text == SCHEDULE_UPDATED_TEXT == "今日行程已更新，請確認下一站"
    assert "抽血" not in n.text and "X 光" not in n.text
    assert c.items_for("U1") == [n]


def test_only_target_user_receives():
    c = NotificationCenter()
    c.send_schedule_updated("U1")
    assert c.items_for("U2") == []


def test_tc_imp_05_route_change_once_per_session_and_version():
    c = NotificationCenter()
    assert c.send_route_changed("U1", "S1", "v2") is not None
    assert c.send_route_changed("U1", "S1", "v2") is None
    assert len(c.items_for("U1")) == 1


def test_route_change_new_version_or_session_notifies_again():
    c = NotificationCenter()
    c.send_route_changed("U1", "S1", "v2")
    assert c.send_route_changed("U1", "S1", "v3") is not None
    assert c.send_route_changed("U1", "S2", "v2") is not None
    assert len(c.items_for("U1")) == 3
