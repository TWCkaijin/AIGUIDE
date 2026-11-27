"""規則程式檢查者：R-ROUTE 加 R-DEP，供 R-ORCH 的「只用規則程式」模式使用(D-008、D-021)。"""
from __future__ import annotations

from collections.abc import Callable, Collection, Iterable

from rules.dependency_check import check_dependencies
from rules.plan_pipeline import CheckVerdict
from rules.route_check import check_route
from rules.static_data import StaticData


def make_rule_checker(static: StaticData, *, patient_orders: Iterable[str], completed: Collection[str],
                      current_node: str, accessibility_need: bool) -> Callable[[dict], CheckVerdict]:
    orders = list(patient_orders)

    def check(output: dict) -> CheckVerdict:
        station = output["next_station_id"]
        route = check_route(static, output["route_node_ids"], start=current_node,
                            target=static.station_nodes.get(station, ""),
                            accessibility_need=accessibility_need)
        if not route.ok:
            return CheckVerdict(False, route.errors[0])
        return check_dependencies(static, station, orders=orders, completed=completed)

    return check
