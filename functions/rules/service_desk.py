"""R-DESK：服務台備援(D-017、AC-04.2～04.4、AC-21.3、AC-NFR01.3)。

由規則程式依生效的樓層圖，選出符合無障礙需求、仍開放且可達的最短路線；
等長先選院方標記的主要服務台，仍相同則依站點識別碼排序。
"""
from __future__ import annotations

import heapq
from collections.abc import Callable
from dataclasses import dataclass

from rules.static_data import StaticData

TEXT_NEARBY_STAFF = "請詢問附近院內人員"
TEXT_AI_UNAVAILABLE = "目前無法自動規劃，請向服務台詢問"  # AC-NFR01.3
TEXT_RETRIES_EXHAUSTED = "目前無法確認下一站，請前往{desk}，由現場人員協助。"  # AC-04.2
TEXT_OUT_OF_SCOPE = "這個問題請向{desk}詢問，現場人員會協助轉介。"  # AC-21.3


@dataclass(frozen=True)
class DeskChoice:
    desk_id: str
    name: str
    node_id: str
    route_node_ids: tuple[str, ...]
    length_m: int


@dataclass(frozen=True)
class DeskFallback:
    kind: str
    text: str | None
    route_node_ids: list[str] | None = None
    needs_start_selection: bool = False
    desk_id: str | None = None


def _shortest_paths(static: StaticData, start: str, accessibility_need: bool):
    adj: dict[str, list] = {}
    for e in static.edges:
        if not e.open or (accessibility_need and not e.accessible):
            continue
        adj.setdefault(e.a, []).append((e.b, e.length_m))
        adj.setdefault(e.b, []).append((e.a, e.length_m))
    dist = {start: 0}
    prev: dict[str, str] = {}
    heap = [(0, start)]
    while heap:
        d, node = heapq.heappop(heap)
        if d > dist.get(node, float("inf")):
            continue
        for nxt, w in sorted(adj.get(node, [])):
            nd = d + w
            if nd < dist.get(nxt, float("inf")):
                dist[nxt], prev[nxt] = nd, node
                heapq.heappush(heap, (nd, nxt))
    return dist, prev


def desk_distances(static: StaticData, start: str, *, accessibility_need: bool) -> dict[str, int]:
    dist, _ = _shortest_paths(static, start, accessibility_need)
    return {d.id: dist[d.node_id] for d in static.service_desks if d.node_id in dist}


def choose_desk(static: StaticData, start: str, *, accessibility_need: bool) -> DeskChoice | None:
    if start not in static.node_names:
        return None
    dist, prev = _shortest_paths(static, start, accessibility_need)
    reachable = [d for d in static.service_desks if d.node_id in dist]
    if not reachable:
        return None
    best = min(reachable, key=lambda d: (dist[d.node_id], 0 if d.primary else 1, d.id))
    path = [best.node_id]
    while path[-1] != start:
        path.append(prev[path[-1]])
    return DeskChoice(best.id, best.name, best.node_id, tuple(reversed(path)), dist[best.node_id])


def make_desk_fallback(static: StaticData, start: str | None, *, accessibility_need: bool,
                       start_selection_declined: bool = False) -> Callable[[str], DeskFallback]:
    """回傳給 R-ORCH 注入用的函式；kind 為 retries_exhausted／ai_unavailable／out_of_scope。"""
    templates = {
        "retries_exhausted": TEXT_RETRIES_EXHAUSTED,
        "ai_unavailable": TEXT_AI_UNAVAILABLE,
        "out_of_scope": TEXT_OUT_OF_SCOPE,
    }

    def fallback(kind: str) -> DeskFallback:
        if kind not in templates:
            raise ValueError(f"不認得的備援種類：{kind}")
        if start is None:
            if start_selection_declined:
                return DeskFallback(kind, TEXT_NEARBY_STAFF)
            return DeskFallback(kind, None, needs_start_selection=True)  # 先請使用者選擇所在站點(AC-04.4)
        choice = choose_desk(static, start, accessibility_need=accessibility_need)
        if choice is None:
            return DeskFallback(kind, TEXT_NEARBY_STAFF)
        return DeskFallback(kind, templates[kind].format(desk=choice.name),
                            list(choice.route_node_ids), desk_id=choice.desk_id)

    return fallback
