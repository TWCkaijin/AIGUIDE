"""階段 4 測試的共用夾具：讀取 mock_data_draft/(D-037)；資料夾不存在時略過並註明原因。"""
import copy
import json
from pathlib import Path

import pytest

from rules.static_data import StaticData, load_raw

MOCK_DIR = Path(__file__).resolve().parents[3] / "mock_data_draft"
SKIP_REASON = "mock_data_draft/ 不存在(D-037：草稿只在本機，其他人的環境略過這些測試)"


@pytest.fixture(scope="session")
def raw_data():
    if not MOCK_DIR.is_dir():
        pytest.skip(SKIP_REASON)
    return load_raw(MOCK_DIR)


@pytest.fixture
def raw(raw_data):
    return copy.deepcopy(raw_data)


@pytest.fixture
def static(raw_data):
    return StaticData.from_raw(copy.deepcopy(raw_data), version="v1")


@pytest.fixture(scope="session")
def patients():
    if not MOCK_DIR.is_dir():
        pytest.skip(SKIP_REASON)
    data = json.loads((MOCK_DIR / "patients.json").read_text(encoding="utf-8"))
    return {p["name"]: p for p in data["patients"]}
