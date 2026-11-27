"""R-ROUTE 路線檢查(TC-ROUTE-01～08、TC-DATA-01；D-020、D-030)。"""
from rules.route_check import check_route

R_BLOOD = ["N2_CLINIC", "N2_CLINIC_WAITING", "N2_CORRIDOR", "N2_BLOOD_DRAW"]
R_STAIRS = ["N2_CLINIC", "N2_CLINIC_WAITING", "N2_CORRIDOR", "N2_STAIRS", "N1_STAIRS",
            "N1_CORRIDOR_W", "N1_BILLING"]


def codes(r):
    return {e.split(":")[0] for e in r.errors}


def test_tc_route_01_good(static):
    r = check_route(static, R_BLOOD, start="N2_CLINIC", target="N2_BLOOD_DRAW", accessibility_need=False)
    assert r.ok, r.errors
    assert r.total_length_m == 40


def test_tc_route_02_does_not_reach_target(static):
    r = check_route(static, R_BLOOD[:2], start="N2_CLINIC", target="N2_BLOOD_DRAW", accessibility_need=False)
    assert not r.ok and "route.end" in codes(r)


def test_tc_route_03_empty(static):
    r = check_route(static, [], start="N2_CLINIC", target="N2_BLOOD_DRAW", accessibility_need=False)
    assert not r.ok and "route.empty" in codes(r)


def test_wrong_start(static):
    r = check_route(static, R_BLOOD[1:], start="N2_CLINIC", target="N2_BLOOD_DRAW", accessibility_need=False)
    assert not r.ok and "route.start" in codes(r)


def test_tc_route_04_stairs_for_wheelchair(static, patients):
    r = check_route(static, R_STAIRS, start="N2_CLINIC", target="N1_BILLING",
                    accessibility_need=patients["陳志遠"]["accessibility_need"])
    assert not r.ok
    assert {e.split(":")[1] for e in r.errors if e.startswith("route.not_accessible")} == {"E11", "E13", "E15"}


def test_tc_route_05_stairs_ok_without_need(static, patients):
    r = check_route(static, R_STAIRS, start="N2_CLINIC", target="N1_BILLING",
                    accessibility_need=patients["黃宜蓁"]["accessibility_need"])
    assert r.ok, r.errors
    assert r.total_length_m == 65


def test_tc_route_06_skipped_node(static):
    r = check_route(static, ["N2_CLINIC", "N2_CORRIDOR", "N2_BLOOD_DRAW"], start="N2_CLINIC",
                    target="N2_BLOOD_DRAW", accessibility_need=False)
    assert not r.ok and "route.edge_missing" in codes(r)


def test_tc_route_07_closed_edge(raw):
    from rules.static_data import StaticData
    next(e for e in raw["map"]["edges"] if e["id"] == "E19")["open"] = False
    s = StaticData.from_raw(raw, version="v1")
    r = check_route(s, R_BLOOD, start="N2_CLINIC", target="N2_BLOOD_DRAW", accessibility_need=False)
    assert not r.ok and "route.edge_closed:E19" in r.errors


def test_tc_route_08_unknown_node(static):
    r = check_route(static, ["N2_CLINIC", "N9_XXX", "N2_BLOOD_DRAW"], start="N2_CLINIC",
                    target="N2_BLOOD_DRAW", accessibility_need=False)
    assert not r.ok and "route.unknown_node" in codes(r)


def test_tc_data_01_missing_need_treated_as_no_need(static, patients):
    from rules.whitelist import build_llm_patient
    p = {k: v for k, v in patients["陳志遠"].items() if k != "accessibility_need"}
    need = build_llm_patient(p)["accessibility_need"]
    r = check_route(static, R_STAIRS, start="N2_CLINIC", target="N1_BILLING", accessibility_need=need)
    assert r.ok, r.errors


def test_same_input_same_result(static):
    rs = {tuple(check_route(static, R_BLOOD, start="N2_CLINIC", target="N2_BLOOD_DRAW",
                            accessibility_need=False).errors) for _ in range(10)}
    assert len(rs) == 1
