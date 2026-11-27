"""R-IMPACT 變動影響判斷(TC-IMP-01～07；D-015、D-018)。"""
import pytest

from rules.impact import GuideSession, find_impact, notify_affected
from rules.notify import NotificationCenter
from rules.versioning import VersionStore

ROUTE = ("N2_CLINIC", "N2_CLINIC_WAITING", "N2_CORRIDOR", "N2_BLOOD_DRAW")


@pytest.fixture
def store(raw):
    return VersionStore(raw)


def publish(store, patch):
    old = store.static()
    old_combo = store.active
    rid = store.submit_data_change("DEPT1", patch)
    store.approve(rid, "ADMIN1")
    return old, store.static(), old_combo


def session(position, route=ROUTE, **kw):
    args = dict(id="S1", user_id="U1", route_node_ids=route, position=position,
                target_station="ST_BLOOD_DRAW", accessibility_need=False, data_version="v1")
    args.update(kw)
    return GuideSession(**args)


def test_tc_imp_01_walking_closed_segment_affected(store):
    old, new, _ = publish(store, {"edges": {"E19": {"open": False}}})
    imp = find_impact(old, new, session(position=2))  # 正走 E19
    assert imp.affected and imp.current and not imp.later_only


def test_tc_imp_02_already_arrived_not_affected(store):
    old, new, _ = publish(store, {"edges": {"E19": {"open": False}}})
    assert not find_impact(old, new, session(position=3)).affected


def test_tc_imp_03_only_later_segment_affected(store):
    old, new, _ = publish(store, {"edges": {"E19": {"open": False}}})
    imp = find_impact(old, new, session(position=0))  # 正走 E18，E19 在後面
    assert imp.affected and not imp.current and imp.later_only


def test_tc_imp_04_name_typo_not_affected(store):
    old, new, _ = publish(store, {"stations": {"ST_BLOOD_DRAW": {"name": "抽血室"}}})
    assert not find_impact(old, new, session(position=0)).affected


def test_tc_imp_07_target_station_moved(store):
    old, new, _ = publish(store, {"stations": {"ST_BLOOD_DRAW": {"node_id": "N2_REPORT_WAITING"}}})
    imp = find_impact(old, new, session(position=0))
    assert imp.affected and imp.current


def test_accessibility_lost_affects_wheelchair_user_only(store):
    old, new, _ = publish(store, {"edges": {"E17": {"accessible": False}}})
    assert find_impact(old, new, session(position=0, accessibility_need=True)).affected
    assert not find_impact(old, new, session(position=0, accessibility_need=False)).affected


def test_pending_station_removed_is_later_affected(store, raw):
    old, new, _ = publish(store, {"edges": {"E21": {"open": False}}})  # 與路線無關
    assert not find_impact(old, new, session(position=0, pending_stations=("ST_BILLING",))).affected


def test_tc_imp_05_notify_once_per_version(store):
    old, new, _ = publish(store, {"edges": {"E19": {"open": False}}})
    c = NotificationCenter()
    s = session(position=2)
    first = notify_affected(c, [s], old, new, version="v2")
    second = notify_affected(c, [s], old, new, version="v2")
    assert list(first) == ["S1"] and first["S1"].current
    assert len(c.items_for("U1")) == 1
    assert list(second) == ["S1"]  # 仍判定受影響，但不再推送


def test_unaffected_session_gets_no_notification(store):
    old, new, _ = publish(store, {"edges": {"E21": {"open": False}}})
    c = NotificationCenter()
    assert notify_affected(c, [session(position=0)], old, new, version="v2") == {}
    assert c.items_for("U1") == []


def test_tc_imp_06_version_binding(store):
    s = session(position=0)
    s.arrive("v2")
    assert s.data_version == "v2" and s.position == len(ROUTE) - 1  # 抵達目的站


def test_tc_imp_06_unaffected_current_segment_keeps_old_version(store):
    s = session(position=0)
    assert s.data_version == "v1"  # 變更後仍用開始時的版本，直到抵達下一站
