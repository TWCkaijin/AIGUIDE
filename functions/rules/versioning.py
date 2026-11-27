"""R-VERSION：版本與審核(FR-06、FR-19、FR-24；D-009、D-011、D-016、D-018、D-027、D-028)。

- 資料版本(部門、路段)：送審 → 另一人審核 → 產生新版本(v1、v2…)。
- 模型設定版本(提示詞、流程依賴表、檢查者模式、模型、重試上限、工具、逾時與 max_tokens)：送簽 → 另一位簽核 → 新版本(s1、s2…)。
- 生效的是「版本組合」；待審、退回期間沿用生效版本；不計時、不提醒(D-027、D-028)。
- 發布前核對流程表引用的站點仍存在(D-018 Q-33)。
- 角色與權限由 R-RBAC(階段 6)判斷，這裡只擋「自己審核自己送的」。
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace

from rules.plan_pipeline import CHECKER_MODES, PipelineSettings
from rules.static_data import StaticData

REGISTERED_TOOLS = ("dept_station_lookup", "flow_dependency_lookup", "route_candidates", "mock_queue")
PROTECTED = ("route_check", "whitelist", "scope_permission")  # 後端強制執行，不可停用(AC-24.5)
PROMPT_NAMES = ("planner", "checker")
SETTING_FIELDS = ("prompts", "flow", "checker_mode", "model", "retry_limit", "tools",
                  "call_timeout_seconds", "max_tokens", "total_wait_cap_seconds")


class SelfApprovalError(PermissionError):
    pass


class NotPending(ValueError):
    pass


class ReasonRequired(ValueError):
    pass


class ConsistencyError(ValueError):
    pass


class ProtectedSetting(ValueError):
    pass


@dataclass(frozen=True)
class VersionCombo:
    data_version: str
    settings_version: str


@dataclass(frozen=True)
class ModelSettings:
    prompts: dict = field(default_factory=dict)
    flow: dict | None = None
    checker_mode: str = "rules"
    model: str = "claude-haiku-5-5"
    retry_limit: int = 3
    tools: dict = field(default_factory=lambda: {t: True for t in REGISTERED_TOOLS})
    call_timeout_seconds: int = 30
    max_tokens: int = 16000
    total_wait_cap_seconds: int = 60

    def to_pipeline_settings(self) -> PipelineSettings:
        return PipelineSettings(
            checker_mode=self.checker_mode, retry_limit=self.retry_limit,
            call_timeout_seconds=self.call_timeout_seconds, total_wait_cap_seconds=self.total_wait_cap_seconds,
            max_tokens=self.max_tokens)


@dataclass
class ChangeRequest:
    id: str
    kind: str  # data / settings
    submitter: str
    payload: dict
    status: str = "pending"  # pending / approved / rejected
    history: list = field(default_factory=list)


def _validate_settings_change(changes: dict) -> None:
    for k in changes:
        if k in PROTECTED:
            raise ProtectedSetting(k)
        if k not in SETTING_FIELDS:
            raise ValueError(f"不認得的設定：{k}")
    if "checker_mode" in changes and changes["checker_mode"] not in CHECKER_MODES:
        raise ValueError("checker_mode 不合法")
    if "retry_limit" in changes:
        PipelineSettings(retry_limit=changes["retry_limit"])  # 0～3(D-011 Q-29)
    if "model" in changes and not (isinstance(changes["model"], str) and changes["model"].strip()):
        raise ValueError("model 不可為空")
    for k in ("call_timeout_seconds", "max_tokens", "total_wait_cap_seconds"):
        if k in changes and not (isinstance(changes[k], int) and not isinstance(changes[k], bool) and changes[k] > 0):
            raise ValueError(f"{k} 必須是正整數")
    for name in changes.get("tools", {}):
        if name in PROTECTED:
            raise ProtectedSetting(name)
        if name not in REGISTERED_TOOLS:
            raise ValueError(f"未登錄的工具：{name}")
    for name in changes.get("prompts", {}):
        if name not in PROMPT_NAMES:
            raise ValueError(f"不認得的提示詞：{name}")


class VersionStore:
    def __init__(self, raw: dict):
        self._data: dict[str, dict] = {"v1": {"map": copy.deepcopy(raw["map"]),
                                              "stations": copy.deepcopy(raw["stations"]),
                                              "exams": copy.deepcopy(raw.get("exams"))}}
        self.settings_versions: dict[str, ModelSettings] = {
            "s1": ModelSettings(flow=copy.deepcopy(raw.get("flow")))}
        self.active = VersionCombo("v1", "s1")
        self.requests: dict[str, ChangeRequest] = {}
        self.events: list[dict] = []
        self.notices: list[dict] = []
        self._n = 0

    # ---- 查詢 ----
    def active_settings(self) -> ModelSettings:
        return self.settings_versions[self.active.settings_version]

    def static(self, combo: VersionCombo | None = None) -> StaticData:
        combo = combo or self.active
        d = self._data[combo.data_version]
        raw = {"map": d["map"], "stations": d["stations"], "exams": d["exams"],
               "flow": self.settings_versions[combo.settings_version].flow}
        return StaticData.from_raw(copy.deepcopy(raw), version=combo.data_version)

    def plan_record(self, *, plan_input_digest: str) -> dict:
        return {"data_version": self.active.data_version, "settings_version": self.active.settings_version,
                "plan_input_digest": plan_input_digest}

    # ---- 送審／送簽 ----
    def _new_request(self, kind, submitter, payload) -> str:
        self._n += 1
        rid = f"CR-{self._n}"
        req = ChangeRequest(rid, kind, submitter, copy.deepcopy(payload))
        req.history.append({"action": "submitted", "by": submitter})
        self.requests[rid] = req
        self.events.append({"type": "submitted", "request": rid})
        return rid

    def _validate_data_patch(self, patch: dict) -> None:
        edges = {e["id"] for e in self._data[self.active.data_version]["map"]["edges"]}
        for eid in patch.get("edges", {}):
            if eid not in edges:
                raise ValueError(f"不存在的路段：{eid}")

    def submit_data_change(self, submitter: str, patch: dict, at=None) -> str:
        self._validate_data_patch(patch)
        return self._new_request("data", submitter, patch)

    def submit_settings_change(self, submitter: str, changes: dict, at=None) -> str:
        _validate_settings_change(changes)
        return self._new_request("settings", submitter, changes)

    def resubmit(self, request_id: str, submitter: str, payload: dict) -> None:
        req = self.requests[request_id]
        if req.status != "rejected":
            raise NotPending("只有被退回的變更可以重新送審")
        if submitter != req.submitter:
            raise PermissionError("只有原送件人可以重新送審")
        if req.kind == "data":
            self._validate_data_patch(payload)
        else:
            _validate_settings_change(payload)
        req.payload = copy.deepcopy(payload)
        req.status = "pending"
        req.history.append({"action": "resubmitted", "by": submitter})
        self.events.append({"type": "resubmitted", "request": request_id})

    # ---- 審核 ----
    def reject(self, request_id: str, reviewer: str, reason: str) -> None:
        req = self.requests[request_id]
        if req.status != "pending":
            raise NotPending(request_id)
        if not (reason or "").strip():
            raise ReasonRequired()
        req.status = "rejected"
        req.history.append({"action": "rejected", "by": reviewer, "reason": reason})
        self.notices.append({"to": req.submitter, "request": request_id, "reason": reason})

    def approve(self, request_id: str, reviewer: str, at=None) -> VersionCombo:
        req = self.requests[request_id]
        if req.status != "pending":
            raise NotPending(request_id)
        if reviewer == req.submitter:
            raise SelfApprovalError(reviewer)  # D-009、D-016
        if req.kind == "data":
            combo = self._publish_data(req)
        else:
            combo = self._publish_settings(req)
        req.status = "approved"
        req.history.append({"action": "approved", "by": reviewer})
        self.active = combo
        self.events.append({"type": "published", "request": request_id, "combo": combo})
        return combo

    @staticmethod
    def _check_flow_stations(flow, station_ids) -> None:
        if flow is None:
            return
        missing = sorted({s["station"] for s in flow["steps"]} - set(station_ids))
        if missing:
            raise ConsistencyError("流程依賴表引用了不存在的站點：" + ",".join(missing))

    def _publish_data(self, req: ChangeRequest) -> VersionCombo:
        base = copy.deepcopy(self._data[self.active.data_version])
        patch = req.payload
        for eid, fields in patch.get("edges", {}).items():
            edge = next(e for e in base["map"]["edges"] if e["id"] == eid)
            edge.update(fields)
        for sid, fields in patch.get("stations", {}).items():
            if fields is None:
                base["stations"]["stations"] = [s for s in base["stations"]["stations"] if s["id"] != sid]
            else:
                next(s for s in base["stations"]["stations"] if s["id"] == sid).update(fields)
        self._check_flow_stations(self.active_settings().flow, [s["id"] for s in base["stations"]["stations"]])
        version = f"v{len(self._data) + 1}"
        self._data[version] = base
        return replace(self.active, data_version=version)

    def _publish_settings(self, req: ChangeRequest) -> VersionCombo:
        changes = copy.deepcopy(req.payload)
        current = self.active_settings()
        if "tools" in changes:
            changes["tools"] = {**current.tools, **changes["tools"]}
        if "prompts" in changes:
            changes["prompts"] = {**current.prompts, **changes["prompts"]}
        if "flow" in changes:
            stations = [s["id"] for s in self._data[self.active.data_version]["stations"]["stations"]]
            self._check_flow_stations(changes["flow"], stations)
        new = replace(current, **changes)
        version = f"s{len(self.settings_versions) + 1}"
        self.settings_versions[version] = new
        return replace(self.active, settings_version=version)
