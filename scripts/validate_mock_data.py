"""檢查模擬資料草稿的內部一致性(D-024)。用法：python3 scripts/validate_mock_data.py [資料目錄]

只檢查「資料彼此是否對得上」，不判斷內容是否符合真實醫院；內容由小組依 D-019 核對。
"""
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

D006_FIELDS = {"name", "age", "sex", "orders", "accessibility_need"}


def load(d: Path, name: str):
    return json.loads((d / name).read_text(encoding="utf-8"))


def reachable(adj, start):
    seen, q = {start}, deque([start])
    while q:
        for n in adj[q.popleft()]:
            if n not in seen:
                seen.add(n)
                q.append(n)
    return seen


def main(d: Path) -> list[str]:
    errs = []
    m = load(d, "hospital_map.json")
    st = load(d, "stations.json")
    fl = load(d, "flow_dependencies.json")
    ex = load(d, "exam_items.json")
    pt = load(d, "patients.json")

    nodes = {n["id"] for n in m["nodes"]}
    floors = {f["id"] for f in m["floors"]}
    for n in m["nodes"]:
        if n["floor"] not in floors:
            errs.append(f"節點 {n['id']} 的樓層 {n['floor']} 不存在")
    adj_all, adj_acc = defaultdict(set), defaultdict(set)
    edge_ids = set()
    for e in m["edges"]:
        if e["id"] in edge_ids:
            errs.append(f"路段 id 重複：{e['id']}")
        edge_ids.add(e["id"])
        for k in ("from", "to"):
            if e[k] not in nodes:
                errs.append(f"路段 {e['id']} 的 {k} 節點 {e[k]} 不存在")
        adj_all[e["from"]].add(e["to"]); adj_all[e["to"]].add(e["from"])
        if e["accessible"] and e["open"]:
            adj_acc[e["from"]].add(e["to"]); adj_acc[e["to"]].add(e["from"])

    start = "N1_ENTRANCE"
    all_reach = reachable(adj_all, start)
    acc_reach = reachable(adj_acc, start)
    for n in nodes - all_reach:
        errs.append(f"節點 {n} 從正門無法到達")

    station_ids = set()
    for s in st["stations"] + st["landmarks"]:
        station_ids.add(s["id"])
        if s["node_id"] not in nodes:
            errs.append(f"{s['id']} 對應的節點 {s['node_id']} 不存在")
        elif s["node_id"] not in acc_reach:
            errs.append(f"{s['id']} 沒有無障礙路線可以到達")
    if sum(1 for s in st["stations"] if s["role"] == "service_desk" and s.get("primary")) != 1:
        errs.append("主要服務台必須剛好一個")
    for w in st["waiting_area_mapping"]:
        for k in ("after_station", "waiting_area"):
            if w[k] not in station_ids:
                errs.append(f"等候區對應引用不存在的站點 {w[k]}")
    for seg in st["metric_segments"]:
        for k in ("from", "to"):
            if seg[k] not in station_ids:
                errs.append(f"計時路段引用不存在的站點 {seg[k]}")

    exam_ids = set()
    for e in ex["exam_items"]:
        exam_ids.add(e["id"])
        if e["station"] not in station_ids:
            errs.append(f"檢查項目 {e['id']} 的站點 {e['station']} 不存在")

    steps = {s["id"]: s for s in fl["steps"]}
    for s in fl["steps"]:
        if s["station"] not in station_ids:
            errs.append(f"步驟 {s['id']} 的站點 {s['station']} 不存在")
        for r in s["requires"]:
            if r not in steps:
                errs.append(f"步驟 {s['id']} 依賴不存在的步驟 {r}")
        if s["when"] != "always":
            oid = s["when"].removeprefix("order:")
            if oid not in exam_ids:
                errs.append(f"步驟 {s['id']} 的條件引用不存在的檢查項目 {oid}")
    state = {}
    def cyclic(sid):
        state[sid] = 1
        for r in steps[sid]["requires"]:
            if r in steps and (state.get(r) == 1 or (state.get(r) is None and cyclic(r))):
                return True
        state[sid] = 2
        return False
    if any(state.get(s) is None and cyclic(s) for s in steps):
        errs.append("流程依賴表有循環")

    pat = re.compile(pt["id_format"]["pattern"])
    ids = set()
    for p in pt["patients"]:
        fields = {k for k in p if not k.startswith("_") and k != "mock_id"}
        if fields != D006_FIELDS:
            errs.append(f"病人 {p.get('mock_id')} 的欄位 {sorted(fields)} 不等於 D-006 的 5 個欄位")
        if not pat.match(p["mock_id"]):
            errs.append(f"模擬身分 {p['mock_id']} 不符合格式")
        if p["mock_id"] in ids:
            errs.append(f"模擬身分重複：{p['mock_id']}")
        ids.add(p["mock_id"])
        for o in p["orders"]:
            if o not in exam_ids:
                errs.append(f"病人 {p['mock_id']} 的醫囑 {o} 不存在")
    return errs


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "mock_data_draft")
    errors = main(d)
    for e in errors:
        print("✗", e)
    print("通過" if not errors else f"共 {len(errors)} 項錯誤")
    sys.exit(1 if errors else 0)
