"""R-STATIC：靜態資料(站點、樓層圖、流程依賴表、服務台)，同一版本內每次查詢結果一致(AC-06.1)。

資料格式見 mock_data_draft/(草稿，D-024)。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class MissingStaticData(Exception):
    """版本組合中缺少必要資料(例如流程依賴表)。"""


@dataclass(frozen=True)
class Step:
    id: str
    name: str
    station: str
    requires: tuple[str, ...]
    when: str


@dataclass(frozen=True)
class Edge:
    id: str
    a: str
    b: str
    length_m: int
    accessible: bool
    open: bool


@dataclass(frozen=True)
class Desk:
    id: str
    name: str
    node_id: str
    primary: bool


def load_raw(directory) -> dict:
    d = Path(directory)

    def read(name):
        p = d / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    return {
        "map": read("hospital_map.json"),
        "stations": read("stations.json"),
        "flow": read("flow_dependencies.json"),
        "exams": read("exam_items.json"),
    }


class StaticData:
    def __init__(self, *, version, node_names, station_nodes, station_names, steps, edges, service_desks,
                 exam_stations):
        self.version = version
        self.node_names = node_names
        self.station_nodes = station_nodes
        self.station_names = station_names
        self.steps = steps  # None 代表缺少流程依賴表
        self.edges = edges
        self.service_desks = service_desks
        self.exam_stations = exam_stations
        self._edge_index = {frozenset((e.a, e.b)): e for e in edges}

    @classmethod
    def from_raw(cls, raw: dict, *, version: str) -> "StaticData":
        m, st = raw["map"], raw["stations"]
        flow = raw.get("flow")
        steps = None if flow is None else tuple(
            Step(s["id"], s["name"], s["station"], tuple(s["requires"]), s["when"]) for s in flow["steps"])
        edges = tuple(Edge(e["id"], e["from"], e["to"], e["length_m"], e["accessible"], e["open"])
                      for e in m["edges"])
        desks = tuple(Desk(s["id"], s["name"], s["node_id"], bool(s.get("primary", False)))
                      for s in st["stations"] if s["role"] == "service_desk")
        exams = {x["id"]: x["station"] for x in (raw.get("exams") or {}).get("exam_items", [])}
        return cls(
            version=version,
            node_names={n["id"]: n["name"] for n in m["nodes"]},
            station_nodes={s["id"]: s["node_id"] for s in st["stations"]},
            station_names={s["id"]: s["name"] for s in st["stations"]},
            steps=steps, edges=edges, service_desks=desks, exam_stations=exams,
        )

    def require_steps(self) -> tuple[Step, ...]:
        if self.steps is None:
            raise MissingStaticData("缺少流程依賴表")
        return self.steps

    def edge_between(self, a: str, b: str) -> Edge | None:
        return self._edge_index.get(frozenset((a, b)))
