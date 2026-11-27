"""R-QUEUE：模擬叫號資料與時間欄位的顯示規則(FR-15、FR-16；D-007、D-026、D-034)。

(b) 預計等候時間、(c) 目前叫號是模擬資料；缺哪項就顯示「暫無資料」，不由 AI 補值。
(a)、(d) 是 AI 估計：沒有值、0 或負數都顯示「暫無估計」；大於 0 就顯示並附標示，不設上限。
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

NO_DATA_TEXT = "暫無資料"
NO_ESTIMATE_TEXT = "暫無估計"
MOCK_SOURCE_LABEL = "模擬叫號資料"
AI_ESTIMATE_TAG = "AI 估計（原型示意）"


@dataclass(frozen=True)
class QueueDisplay:
    wait_text: str
    number_text: str
    source_label: str = MOCK_SOURCE_LABEL


@dataclass(frozen=True)
class EstimateDisplay:
    text: str
    tag: str | None


class MockQueue:
    def __init__(self, data: Mapping[str, Mapping]):
        self._data = data

    def display(self, station_id: str) -> QueueDisplay:
        row = self._data.get(station_id, {})
        wait, number = row.get("wait_minutes"), row.get("current_number")
        return QueueDisplay(
            wait_text=NO_DATA_TEXT if wait is None else str(wait),
            number_text=NO_DATA_TEXT if number is None else str(number),
        )


def format_estimate(value) -> EstimateDisplay:
    if value is None or value <= 0:
        return EstimateDisplay(NO_ESTIMATE_TEXT, None)
    return EstimateDisplay(str(value), AI_ESTIMATE_TAG)
