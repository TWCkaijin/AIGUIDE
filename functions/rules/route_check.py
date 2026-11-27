"""R-ROUTE：檢查 AI 描述的路線(樓層圖節點序列)(D-020、FR-13)。

相鄰節點之間要有路段、路段要開放、需要無障礙時路段要符合無障礙，起訖點要正確。
缺少無障礙需求時由 R-WL 視為「無需求」(D-030)。
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from rules.static_data import StaticData


@dataclass
class RouteResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    total_length_m: int | None = None


def check_route(static: StaticData, route: Sequence[str], *, start: str, target: str,
                accessibility_need: bool) -> RouteResult:
    if not route:
        return RouteResult(False, ["route.empty"])
    unknown = [f"route.unknown_node:{n}" for n in route if n not in static.node_names]
    if unknown:
        return RouteResult(False, unknown)

    errors: list[str] = []
    if route[0] != start:
        errors.append("route.start")
    if route[-1] != target:
        errors.append("route.end")

    total = 0
    for a, b in zip(route, route[1:]):
        e = static.edge_between(a, b)
        if e is None:
            errors.append(f"route.edge_missing:{a}->{b}")
            continue
        if not e.open:
            errors.append(f"route.edge_closed:{e.id}")
        if accessibility_need and not e.accessible:
            errors.append(f"route.not_accessible:{e.id}")
        total += e.length_m
    return RouteResult(not errors, errors, total if not errors else None)
