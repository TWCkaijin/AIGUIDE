"""R-DEMO：範例草案(D-038)。

- 只有「檢查者模式」欄位提供範例；範例為 D-008 的三種模式。
- 載入範例只產生草稿(is_example=True)，不改動生效設定；之後的送簽、簽核走一般流程(D-016)。
- 範例只含檢查者模式，不含提示詞，因此不會改動提示詞原文。
"""
from __future__ import annotations

from dataclasses import dataclass, field

EXAMPLE_LABEL = "範例"


class FieldHasNoExamples(Exception):
    """該欄位沒有「使用範例」按鈕。"""


class ExampleNotFound(Exception):
    pass


@dataclass(frozen=True)
class Example:
    id: str
    value: str
    title: str
    description: str
    label: str = EXAMPLE_LABEL


@dataclass(frozen=True)
class Draft:
    field: str
    changes: dict
    is_example: bool = True
    status: str = "draft"
    label: str = EXAMPLE_LABEL


_CHECKER_MODE_EXAMPLES = (
    Example("checker-rules-only", "rules", "只用規則程式", "只由規則程式檢查 AI 輸出，每次結果都相同；這是預設模式(D-008)。"),
    Example("checker-agent-only", "agent", "只用專用 Agent", "只由專用 Agent 檢查 AI 輸出；判定可能每次不同(D-008 已知限制)。"),
    Example("checker-both", "both", "兩者都用", "先由規則程式檢查，違規即退回；通過後才交給專用 Agent，兩者都通過才發布(D-008)。"),
)

_EXAMPLES = {"checker_mode": _CHECKER_MODE_EXAMPLES}


def list_examples(field_name: str) -> tuple[Example, ...]:
    if field_name not in _EXAMPLES:
        raise FieldHasNoExamples(field_name)
    return _EXAMPLES[field_name]


def load_example(field_name: str, example_id: str) -> Draft:
    for e in list_examples(field_name):
        if e.id == example_id:
            return Draft(field=field_name, changes={field_name: e.value})
    raise ExampleNotFound(example_id)
