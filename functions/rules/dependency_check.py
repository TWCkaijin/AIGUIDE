"""R-DEP：檢查 AI 選定的下一站是否違反流程依賴表([REQ-04-03]、FR-02)。"""
from __future__ import annotations

from collections.abc import Collection, Iterable

from rules.candidates import applies
from rules.plan_pipeline import CheckVerdict
from rules.static_data import StaticData


def check_dependencies(static: StaticData, station_id: str, *, orders: Iterable[str],
                       completed: Collection[str]) -> CheckVerdict:
    orders, completed = list(orders), set(completed)
    if station_id not in static.station_nodes:
        return CheckVerdict(False, f"dep.unknown_station:{station_id}")
    pending = [s for s in static.require_steps()
               if s.station == station_id and s.id not in completed and applies(s.when, orders)]
    if not pending:
        return CheckVerdict(False, f"dep.no_pending_step:{station_id}")
    for s in pending:
        if set(s.requires) <= completed:
            return CheckVerdict(True)
    missing = sorted(set(pending[0].requires) - completed)
    return CheckVerdict(False, "dep.requires_not_done:" + ",".join(missing))
