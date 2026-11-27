"""R-STATIC 靜態資料(TC-VER-01、TC-DATA-04)。"""
import pytest

from rules.static_data import MissingStaticData, StaticData


def test_tc_ver_01_same_answer_every_time(static):
    answers = {static.station_nodes["ST_BLOOD_DRAW"] for _ in range(10)}
    assert answers == {"N2_BLOOD_DRAW"}


def test_version_recorded(static):
    assert static.version == "v1"


def test_lookups(static):
    assert static.node_names["N2_BLOOD_DRAW"] == "抽血站"
    assert static.station_names["ST_BLOOD_DRAW"] == "抽血站"
    assert {d.id for d in static.service_desks} == {"SD_1F", "SD_2F"}
    assert next(d for d in static.service_desks if d.id == "SD_1F").primary is True
    assert static.edge_between("N2_CLINIC", "N2_CLINIC_WAITING").id == "E18"
    assert static.edge_between("N2_CLINIC_WAITING", "N2_CLINIC").id == "E18"  # 無方向
    assert static.edge_between("N2_CLINIC", "N2_CORRIDOR") is None


def test_tc_data_04_missing_dependency_table(raw):
    raw["flow"] = None
    s = StaticData.from_raw(raw, version="v1")
    with pytest.raises(MissingStaticData):
        s.require_steps()
