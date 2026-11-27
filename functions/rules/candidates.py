"""R-CAND：依流程依賴表、目前進度與有效醫囑，算出允許的下一站候選(FR-02、[REQ-04-03]、D-020)。

`when` 欄位：always，或 order:<檢查項目 id>(有該醫囑才需要這個步驟)。
"""
from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass

from rules.static_data import StaticData


@dataclass(frozen=True)
class Candidates:
    steps: tuple[str, ...]        # 依 id 排序，結果固定
    stations: frozenset[str]


def applies(when: str, orders: Iterable[str]) -> bool:
    if when == "always":
        return True
    if when.startswith("order:"):
        return when[len("order:"):] in set(orders)
    raise ValueError(f"不認得的 when 規則：{when}")


def next_candidates(static: StaticData, *, orders: Iterable[str], completed: Collection[str]) -> Candidates:
    orders, completed = list(orders), set(completed)
    picked = [
        s for s in static.require_steps()
        if s.id not in completed and applies(s.when, orders) and set(s.requires) <= completed
    ]
    return Candidates(steps=tuple(sorted(s.id for s in picked)),
                      stations=frozenset(s.station for s in picked))
