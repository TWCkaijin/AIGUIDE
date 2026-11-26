"""R-GUARD：檢查 AI(A-PLAN)的輸出，通過才能交給檢查者與顯示。

規則來源：
- design.md 第 4 節：格式、必須包含、不得出現三類檢查。
- D-020：下一站只能從 R-CAND 候選中挑選；路線以樓層圖節點 id 序列表示。
- D-021：本模組一律執行，不受檢查者模式影響；路線可不可走、流程依賴由檢查者負責。
- D-022：說明文字不做診斷類詞彙檢查。
- D-026：時間估計為 0 或負數不算不合格(只影響顯示)。
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import json

# AI 輸出的欄位(design.md 第 3、4 節)
PLAN_FIELDS: frozenset[str] = frozenset({
    "next_station_id",
    "route_node_ids",
    "explanation",
    "walk_minutes_estimate",
    "total_minutes_estimate",
    "out_of_scope",
    "suggest_help",
})

_BAD_STOP_REASONS = frozenset({"refusal", "max_tokens"})


@dataclass(frozen=True)
class GuardContext:
    """檢查所需的規則資料，全部由規則模組提供(design.md P2)。"""
    candidates: frozenset[str]
    current_node: str
    station_nodes: Mapping[str, str]          # 站點 id → 樓層圖節點 id
    node_names: Mapping[str, str]             # 樓層圖節點 id → 名稱
    forbidden_strings: tuple[str, ...] = ()   # 白名單以外、不得出現在文字中的病人資料(例如 mock_id)


@dataclass
class GuardResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    out_of_scope: bool = False


def _is_number_or_null(v) -> bool:
    return v is None or (isinstance(v, (int, float)) and not isinstance(v, bool))


def _check_format(data, stop_reason: str) -> list[str]:
    errors: list[str] = []
    if stop_reason in _BAD_STOP_REASONS:
        errors.append(f"format.stop_reason:{stop_reason}")
    for k in sorted(PLAN_FIELDS - set(data)):
        errors.append(f"format.missing_field:{k}")
    for k in sorted(set(data) - PLAN_FIELDS):
        errors.append(f"format.extra_field:{k}")

    types = {
        "next_station_id": lambda v: isinstance(v, str),
        "route_node_ids": lambda v: isinstance(v, list) and all(isinstance(x, str) for x in v),
        "explanation": lambda v: isinstance(v, str),
        "walk_minutes_estimate": _is_number_or_null,
        "total_minutes_estimate": _is_number_or_null,
        "out_of_scope": lambda v: isinstance(v, bool),
        "suggest_help": lambda v: isinstance(v, bool),
    }
    for k, ok in types.items():
        if k in data and not ok(data[k]):
            errors.append(f"format.type:{k}")
    return errors


def _mentioned_names(text: str, names: set[str]) -> set[str]:
    """找出文字中出現的站點/節點名稱；長名稱優先比對，避免短名稱重複命中。"""
    found: set[str] = set()
    remaining = text
    for name in sorted(names, key=len, reverse=True):
        if name and name in remaining:
            found.add(name)
            remaining = remaining.replace(name, "\0")
    return found


def _check_guidance(data, ctx: GuardContext) -> list[str]:
    errors: list[str] = []
    station = data["next_station_id"]
    route: list[str] = data["route_node_ids"]

    # 必須包含
    if station not in ctx.candidates:
        errors.append(f"must.next_station_not_candidate:{station}")
    if not route or route[0] != ctx.current_node:
        errors.append("must.route_start")
    target = ctx.station_nodes.get(station)
    if not route or target is None or route[-1] != target:
        errors.append("must.route_end")
    if not data["explanation"].strip():
        errors.append("must.explanation_empty")

    # 不得出現
    for node in route:
        if node not in ctx.node_names:
            errors.append(f"not.unknown_node:{node}")
    allowed = {ctx.node_names[n] for n in route if n in ctx.node_names}
    if target in ctx.node_names:
        allowed.add(ctx.node_names[target])
    for name in sorted(_mentioned_names(data["explanation"], set(ctx.node_names.values())) - allowed):
        errors.append(f"not.station_name_outside_route:{name}")
    for s in ctx.forbidden_strings:
        if s and s in data["explanation"]:
            errors.append("not.forbidden_string")
            break
    return errors


def check_plan_output(raw, *, stop_reason: str, ctx: GuardContext) -> GuardResult:
    """檢查 AI 輸出。raw 可以是 dict 或 JSON 字串。"""
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return GuardResult(ok=False, errors=["format.invalid_json"])
    else:
        data = raw
    if not isinstance(data, dict):
        return GuardResult(ok=False, errors=["format.invalid_json"])

    errors = _check_format(data, stop_reason)
    if errors:
        return GuardResult(ok=False, errors=errors)

    if data["out_of_scope"]:
        # 超出就醫流程範圍：不顯示導引，改由 R-DESK 顯示固定文案(design.md 第 4 節、AC-21.3)
        return GuardResult(ok=True, out_of_scope=True)

    errors = _check_guidance(data, ctx)
    return GuardResult(ok=not errors, errors=errors)
