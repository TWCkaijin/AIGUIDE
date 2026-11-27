"""R-VERSION 版本與審核(TC-VER-02～04、TC-REV-01～09、TC-SET-01～08；D-009、D-016、D-018、D-027、D-028)。

角色與權限(誰有資格審核)在階段 6 的 R-RBAC 測試；這裡只測流程與「不能審核自己送的」。
"""
import pytest

from rules.versioning import (
    ConsistencyError, ModelSettings, NotPending, ProtectedSetting, ReasonRequired, SelfApprovalError,
    VersionCombo, VersionStore,
)


@pytest.fixture
def store(raw):
    return VersionStore(raw)


CLOSE_E19 = {"edges": {"E19": {"open": False}}}


def test_initial_combo(store):
    assert store.active == VersionCombo("v1", "s1")


# ---- 資料版本(部門／路段) ----

def test_tc_rev_01_approve_publishes_new_version(store):
    rid = store.submit_data_change("DEPT1", CLOSE_E19)
    combo = store.approve(rid, "ADMIN1")
    assert combo == VersionCombo("v2", "s1") and store.active == combo


def test_tc_ver_02_before_after_each_consistent(store):
    before = [store.static().edge_between("N2_CORRIDOR", "N2_BLOOD_DRAW").open for _ in range(3)]
    rid = store.submit_data_change("DEPT1", CLOSE_E19)
    store.approve(rid, "ADMIN1")
    after = [store.static().edge_between("N2_CORRIDOR", "N2_BLOOD_DRAW").open for _ in range(3)]
    assert before == [True] * 3 and after == [False] * 3
    # 舊版本仍可查，內容不變
    old = store.static(VersionCombo("v1", "s1"))
    assert old.edge_between("N2_CORRIDOR", "N2_BLOOD_DRAW").open is True


def test_tc_ver_03_pending_not_effective(store):
    store.submit_data_change("DEPT1", CLOSE_E19)
    assert store.active.data_version == "v1"
    assert store.static().edge_between("N2_CORRIDOR", "N2_BLOOD_DRAW").open is True


def test_tc_rev_02_self_approval_rejected(store):
    rid = store.submit_data_change("ADMIN1", CLOSE_E19)
    with pytest.raises(SelfApprovalError):
        store.approve(rid, "ADMIN1")
    assert store.active.data_version == "v1"


def test_tc_rev_03_reject_needs_reason(store):
    rid = store.submit_data_change("DEPT1", CLOSE_E19)
    for reason in ("", "   "):
        with pytest.raises(ReasonRequired):
            store.reject(rid, "ADMIN1", reason)
    assert store.requests[rid].status == "pending"


def test_tc_rev_04_05_07_pending_forever_no_reminders(store):
    rid = store.submit_data_change("DEPT1", CLOSE_E19, at=0)
    assert store.requests[rid].status == "pending"
    assert store.active.data_version == "v1"
    assert [e["type"] for e in store.events] == ["submitted"]  # 不論多久、審核人員在不在，都沒有提醒


def test_tc_rev_06_immediate_approval_effective(store):
    rid = store.submit_data_change("DEPT1", CLOSE_E19, at=0)
    store.approve(rid, "ADMIN1", at=1)
    assert store.active.data_version == "v2"


def test_tc_rev_08_reject_notifies_submitter_and_resubmit(store):
    rid = store.submit_data_change("DEPT1", CLOSE_E19)
    store.reject(rid, "ADMIN1", "路段編號寫錯")
    assert store.requests[rid].status == "rejected"
    assert store.notices == [{"to": "DEPT1", "request": rid, "reason": "路段編號寫錯"}]
    assert store.active.data_version == "v1"
    store.resubmit(rid, "DEPT1", {"edges": {"E19": {"open": False, "accessible": False}}})
    r = store.requests[rid]
    assert r.status == "pending"
    assert [h["action"] for h in r.history] == ["submitted", "rejected", "resubmitted"]


def test_only_pending_can_be_approved(store):
    rid = store.submit_data_change("DEPT1", CLOSE_E19)
    store.approve(rid, "ADMIN1")
    with pytest.raises(NotPending):
        store.approve(rid, "ADMIN2")


def test_resubmit_only_by_submitter_and_only_when_rejected(store):
    rid = store.submit_data_change("DEPT1", CLOSE_E19)
    with pytest.raises(NotPending):
        store.resubmit(rid, "DEPT1", CLOSE_E19)
    store.reject(rid, "ADMIN1", "x")
    with pytest.raises(PermissionError):
        store.resubmit(rid, "OTHER", CLOSE_E19)


def test_tc_rev_09_removing_station_used_by_flow_blocked(store):
    rid = store.submit_data_change("DEPT1", {"stations": {"ST_BLOOD_DRAW": None}})
    with pytest.raises(ConsistencyError):
        store.approve(rid, "ADMIN1")
    assert store.active == VersionCombo("v1", "s1")


def test_unknown_edge_in_patch_rejected_at_submit(store):
    with pytest.raises(ValueError):
        store.submit_data_change("DEPT1", {"edges": {"E99": {"open": False}}})


def test_station_rename_keeps_node(store):
    rid = store.submit_data_change("DEPT1", {"stations": {"ST_BLOOD_DRAW": {"name": "抽血室"}}})
    store.approve(rid, "ADMIN1")
    s = store.static()
    assert s.station_names["ST_BLOOD_DRAW"] == "抽血室" and s.station_nodes["ST_BLOOD_DRAW"] == "N2_BLOOD_DRAW"


# ---- 模型設定 ----

def test_tc_set_05_defaults():
    m = ModelSettings()
    assert (m.call_timeout_seconds, m.max_tokens, m.total_wait_cap_seconds) == (30, 16000, 60)
    assert (m.checker_mode, m.retry_limit, m.model) == ("rules", 3, "claude-haiku-5-5")
    p = m.to_pipeline_settings()
    assert (p.call_timeout_seconds, p.max_tokens, p.total_wait_cap_seconds) == (30, 16000, 60)


def test_tc_set_01_publish_and_keep_old(store):
    rid = store.submit_settings_change("ADMIN1", {"retry_limit": 2})
    combo = store.approve(rid, "ADMIN2")
    assert combo == VersionCombo("v1", "s2")
    assert store.active_settings().retry_limit == 2
    assert store.settings_versions["s1"].retry_limit == 3


def test_tc_set_02_self_approval_rejected(store):
    rid = store.submit_settings_change("ADMIN1", {"retry_limit": 2})
    with pytest.raises(SelfApprovalError):
        store.approve(rid, "ADMIN1")


def test_tc_set_03_pending_keeps_old_settings(store):
    store.submit_settings_change("ADMIN1", {"checker_mode": "both"})
    assert store.active_settings().checker_mode == "rules"


@pytest.mark.parametrize("name", ["route_check", "whitelist", "scope_permission"])
def test_tc_set_04_protected_cannot_be_disabled(store, name):
    with pytest.raises(ProtectedSetting):
        store.submit_settings_change("ADMIN1", {name: False})
    with pytest.raises(ProtectedSetting):
        store.submit_settings_change("ADMIN1", {"tools": {name: False}})


@pytest.mark.parametrize("changes", [
    {"checker_mode": "neither"}, {"retry_limit": 4}, {"retry_limit": -1}, {"model": ""},
    {"call_timeout_seconds": 0}, {"unknown_field": 1}, {"prompts": {"mystery": "x"}},
])
def test_tc_set_06_invalid_changes_rejected(store, changes):
    with pytest.raises(ValueError):
        store.submit_settings_change("ADMIN1", changes)


def test_tc_set_07_tools_registered_only(store):
    rid = store.submit_settings_change("ADMIN1", {"tools": {"mock_queue": False}})
    store.approve(rid, "ADMIN2")
    assert store.active_settings().tools["mock_queue"] is False
    with pytest.raises(ValueError):
        store.submit_settings_change("ADMIN1", {"tools": {"delete_everything": True}})


def test_tc_set_08_all_versions_kept(store):
    for n in (2, 1, 0):
        rid = store.submit_settings_change("ADMIN1", {"retry_limit": n})
        store.approve(rid, "ADMIN2")
    assert [store.settings_versions[k].retry_limit for k in ("s1", "s2", "s3", "s4")] == [3, 2, 1, 0]


def test_flow_table_belongs_to_settings_version(store, raw):
    new_flow = {"steps": [s for s in raw["flow"]["steps"] if s["id"] != "STEP_PHARMACY"]}
    rid = store.submit_settings_change("ADMIN1", {"flow": new_flow})
    store.approve(rid, "ADMIN2")
    assert "STEP_PHARMACY" not in {s.id for s in store.static().steps}
    assert "STEP_PHARMACY" in {s.id for s in store.static(VersionCombo("v1", "s1")).steps}


def test_flow_referencing_missing_station_rejected(store):
    bad = {"steps": [{"id": "S", "name": "x", "station": "ST_NOWHERE", "requires": [], "when": "always"}]}
    rid = store.submit_settings_change("ADMIN1", {"flow": bad})
    with pytest.raises(ConsistencyError):
        store.approve(rid, "ADMIN2")


def test_tc_ver_04_plan_record_carries_both_versions(store):
    rec = store.plan_record(plan_input_digest="abc")
    assert rec == {"data_version": "v1", "settings_version": "s1", "plan_input_digest": "abc"}
