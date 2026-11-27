"""R-IMPACT：變動影響判斷(FR-20；D-015、D-018)。

新版本生效時，比對各導引工作階段「當前路段、尚未走的路段、尚未抵達的站點」：
- 路段不存在、關閉，或(需要無障礙者)失去無障礙通行，視為失效。
- 目的站或待完成站點被移除、或搬到別的節點，視為失效。站點名稱修改、已走完的路段不計。
- 影響當前路段或目的站：立即通知並重新規劃；只影響後面的部分：通知，但可走完當前路段。
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from rules.notify import NotificationCenter
from rules.static_data import StaticData


@dataclass
class GuideSession:
    id: str
    user_id: str
    route_node_ids: tuple[str, ...]
    position: int                       # 目前所在節點在路線中的位置；正在走的路段是 position → position+1
    target_station: str
    accessibility_need: bool
    data_version: str
    pending_stations: tuple[str, ...] = ()

    def arrive(self, latest_version: str) -> None:
        """抵達目的站：之後的規劃改用最新已生效版本(AC-20.6)。"""
        self.position = len(self.route_node_ids) - 1
        self.data_version = latest_version


@dataclass(frozen=True)
class Impact:
    affected: bool
    current: bool        # 影響當前路段或目的站
    later_only: bool     # 只影響後面的路段或站點


def _segment_invalid(new: StaticData, a: str, b: str, need: bool) -> bool:
    e = new.edge_between(a, b)
    return e is None or not e.open or (need and not e.accessible)


def _station_invalid(old: StaticData, new: StaticData, station: str) -> bool:
    return station not in new.station_nodes or new.station_nodes[station] != old.station_nodes.get(station)


def find_impact(old: StaticData, new: StaticData, session: GuideSession) -> Impact:
    route = session.route_node_ids
    segments = list(zip(route[session.position:], route[session.position + 1:]))
    need = session.accessibility_need
    current = bool(segments) and _segment_invalid(new, *segments[0], need)
    current = current or (bool(segments) and _station_invalid(old, new, session.target_station))
    later = any(_segment_invalid(new, a, b, need) for a, b in segments[1:])
    later = later or any(_station_invalid(old, new, s) for s in session.pending_stations)
    return Impact(affected=current or later, current=current, later_only=later and not current)


def notify_affected(center: NotificationCenter, sessions: Iterable[GuideSession], old: StaticData,
                    new: StaticData, *, version: str) -> dict[str, Impact]:
    """回傳受影響的工作階段；同一工作階段、同一版本只推送一次(AC-20.5)。"""
    affected: dict[str, Impact] = {}
    for s in sessions:
        imp = find_impact(old, new, s)
        if imp.affected:
            center.send_route_changed(s.user_id, s.id, version)
            affected[s.id] = imp
    return affected
