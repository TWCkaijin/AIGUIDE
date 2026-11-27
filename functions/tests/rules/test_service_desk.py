"""R-DESK 服務台備援(TC-DESK-01～09、TC-SCOPE-01；D-017)。"""
import copy

from rules.service_desk import choose_desk, make_desk_fallback
from rules.static_data import StaticData


def test_tc_desk_01_clinic_picks_2f(static):
    c = choose_desk(static, "N2_CLINIC", accessibility_need=False)
    assert c.desk_id == "SD_2F" and c.length_m == 25
    f = make_desk_fallback(static, "N2_CLINIC", accessibility_need=False)("retries_exhausted")
    assert f.text == "目前無法確認下一站，請前往二樓服務台，由現場人員協助。"
    assert f.route_node_ids[0] == "N2_CLINIC" and f.route_node_ids[-1] == "N2_SERVICE_DESK"


def _with_e16_length(raw, n):
    next(e for e in raw["map"]["edges"] if e["id"] == "E16")["length_m"] = n
    return raw


def test_tc_desk_02_equal_distance_prefers_primary(raw):
    s = StaticData.from_raw(_with_e16_length(raw, 45), version="v1")  # 兩處都是 65 m
    c = choose_desk(s, "N2_CLINIC", accessibility_need=False)
    assert c.length_m == 65 and c.desk_id == "SD_1F"


def test_tc_desk_03_equal_and_no_primary_uses_id_order(raw):
    raw = _with_e16_length(raw, 45)
    for st in raw["stations"]["stations"]:
        if st["role"] == "service_desk":
            st["primary"] = False
    c = choose_desk(StaticData.from_raw(raw, version="v1"), "N2_CLINIC", accessibility_need=False)
    assert c.desk_id == "SD_1F"


def test_tc_desk_04_radiology_picks_1f(static):
    c = choose_desk(static, "N1_RADIOLOGY", accessibility_need=False)
    assert c.desk_id == "SD_1F" and c.length_m == 45


def test_tc_desk_05_accessible_only(static, patients):
    c = choose_desk(static, "N1_BILLING", accessibility_need=patients["陳志遠"]["accessibility_need"])
    assert c.desk_id == "SD_1F" and c.length_m == 30


def test_tc_desk_05b_non_accessible_counts_stairs(static):
    # 不需無障礙時 SD_2F 為 50 m(對照表)
    from rules.service_desk import desk_distances
    d = desk_distances(static, "N1_BILLING", accessibility_need=False)
    assert d == {"SD_1F": 30, "SD_2F": 50}
    d = desk_distances(static, "N1_BILLING", accessibility_need=True)
    assert d == {"SD_1F": 30, "SD_2F": 70}


def test_tc_desk_06_unknown_start_asks_user_to_choose(static):
    f = make_desk_fallback(static, None, accessibility_need=False)("retries_exhausted")
    assert f.needs_start_selection is True and f.route_node_ids is None


def test_tc_desk_07_start_still_unknown_asks_nearby_staff(static):
    f = make_desk_fallback(static, None, accessibility_need=False, start_selection_declined=True)("retries_exhausted")
    assert f.text == "請詢問附近院內人員" and f.needs_start_selection is False


def test_tc_desk_08_closed_edge_picks_other(raw):
    next(e for e in raw["map"]["edges"] if e["id"] == "E16")["open"] = False
    c = choose_desk(StaticData.from_raw(raw, version="v1"), "N2_CLINIC", accessibility_need=False)
    assert c.desk_id == "SD_1F" and c.length_m == 65


def test_tc_desk_09_consistent(static):
    rs = {tuple(vars(choose_desk(static, "N2_CLINIC", accessibility_need=False)).items()) for _ in range(10)}
    assert len(rs) == 1


def test_no_reachable_desk_asks_nearby_staff(raw):
    for e in raw["map"]["edges"]:
        e["open"] = False
    f = make_desk_fallback(StaticData.from_raw(raw, version="v1"), "N2_CLINIC", accessibility_need=False)("retries_exhausted")
    assert f.text == "請詢問附近院內人員" and f.route_node_ids is None


def test_ai_unavailable_text_and_route(static):
    f = make_desk_fallback(static, "N2_CLINIC", accessibility_need=False)("ai_unavailable")
    assert f.text == "目前無法自動規劃，請向服務台詢問" and f.route_node_ids


def test_tc_scope_01_out_of_scope_text(static):
    f = make_desk_fallback(static, "N2_CLINIC", accessibility_need=False)("out_of_scope")
    assert f.text == "這個問題請向二樓服務台詢問，現場人員會協助轉介。"
    assert f.route_node_ids[-1] == "N2_SERVICE_DESK"


def test_does_not_mutate_static(static):
    before = copy.deepcopy(static.edges)
    choose_desk(static, "N2_CLINIC", accessibility_need=False)
    assert static.edges == before
