"""R-ORCH：規劃流程控制(design.md 第 3、4、6 節)。

規則來源：
- D-008：檢查者模式(預設只用規則程式；兩者都用時先規則、通過後才交給 Agent；檢查結果拿不到就不發布)。
- D-011：重試上限預設 3、可設 0～3，初次產生不計入。
- D-017、AC-NFR01.3：重試用完或 AI 無法使用時轉服務台備援(由 R-DESK 產生，這裡只傳入種類)。
- D-021：R-GUARD 一律執行；R-ROUTE、R-DEP 或 A-CHECK 依模式。
- D-029：單次逾時 30 秒、max_tokens 16000、總等待上限 60 秒(準備再呼叫時已 ≥ 60 秒就不再呼叫)。
- design.md P2：輸入凍結並比對雜湊，AI 呼叫前後不一致視為系統錯誤。
"""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from rules.output_guard import GuardContext, check_plan_output

CHECKER_MODES = ("rules", "agent", "both")  # 只用規則程式／只用專用 Agent／兩者都用


@dataclass(frozen=True)
class PipelineSettings:
    checker_mode: str = "rules"
    retry_limit: int = 3
    call_timeout_seconds: int = 30
    total_wait_cap_seconds: int = 60
    max_tokens: int = 16000

    def __post_init__(self):
        if self.checker_mode not in CHECKER_MODES:
            raise ValueError(f"checker_mode 必須是 {CHECKER_MODES}")
        if not isinstance(self.retry_limit, int) or isinstance(self.retry_limit, bool) \
                or not 0 <= self.retry_limit <= 3:
            raise ValueError("retry_limit 可設範圍 0～3(D-011)")


@dataclass(frozen=True)
class PlanInput:
    """送給 AI 的唯讀輸入包。病人資料應已經過 R-WL 白名單。"""
    patient: dict
    today_text: str
    candidates: tuple
    current_node: str
    floor_map: dict

    def to_json(self) -> str:
        return json.dumps(
            {"patient": self.patient, "today_text": self.today_text, "candidates": list(self.candidates),
             "current_node": self.current_node, "floor_map": self.floor_map},
            ensure_ascii=False, sort_keys=True)

    def digest(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()


@dataclass
class CheckVerdict:
    ok: bool
    reason: str = ""


class CheckUnavailable(Exception):
    """檢查結果拿不到(例如 Agent 逾時)。"""


@dataclass
class PlanResult:
    status: str  # published / out_of_scope / fallback / system_error
    output: Any = None
    fallback: Any = None
    attempts: list = field(default_factory=list)


def run_plan(plan_input: PlanInput, *, client, guard_ctx: GuardContext, settings: PipelineSettings,
             rule_checker: Callable[[dict], CheckVerdict],
             agent_checker: Callable[[dict], CheckVerdict] | None,
             desk_fallback: Callable[[str], Any], clock: Callable[[], float] = time.monotonic) -> PlanResult:
    # 延遲匯入，避免規則層與 AI 層在載入時互相依賴
    from ai.claude_client import AiError, AiTimeout

    digest = plan_input.digest()
    start = clock()
    attempts: list[dict] = []

    def fallback(kind: str, status: str = "fallback") -> PlanResult:
        return PlanResult(status=status, fallback=desk_fallback(kind), attempts=attempts)

    n = 0
    while True:
        if n > 0 and clock() - start >= settings.total_wait_cap_seconds:
            return fallback("retries_exhausted")

        record: dict = {"attempt": n}
        attempts.append(record)
        try:
            resp = client.plan(plan_input, timeout_seconds=settings.call_timeout_seconds,
                               max_tokens=settings.max_tokens)
        except AiTimeout:
            record["outcome"] = "timeout"
            resp = None
        except AiError:
            record["outcome"] = "unavailable"
            return fallback("ai_unavailable")

        if plan_input.digest() != digest:
            record["outcome"] = "system_error"
            return fallback("ai_unavailable", status="system_error")

        if resp is not None:
            if resp.stop_reason == "refusal":
                record["outcome"] = "refusal"
                return fallback("ai_unavailable")
            failed_by = _check(resp, guard_ctx, settings, rule_checker, agent_checker, record)
            if failed_by is None:
                if record.get("out_of_scope"):
                    record["outcome"] = "out_of_scope"
                    return PlanResult(status="out_of_scope", output=resp.data, attempts=attempts)
                record["outcome"] = "published"
                return PlanResult(status="published", output=resp.data, attempts=attempts)
            record["outcome"] = "rejected"
            record["failed_by"] = failed_by

        if n >= settings.retry_limit:
            return fallback("retries_exhausted")
        n += 1


def _check(resp, guard_ctx, settings, rule_checker, agent_checker, record) -> str | None:
    """回傳未通過的一方；全部通過回傳 None。"""
    guard = check_plan_output(resp.data, stop_reason=resp.stop_reason, ctx=guard_ctx)
    if not guard.ok:
        record["errors"] = guard.errors
        return "guard"
    if guard.out_of_scope:
        record["out_of_scope"] = True
        return None
    if settings.checker_mode in ("rules", "both"):
        v = rule_checker(resp.data)
        if not v.ok:
            record["errors"] = [v.reason]
            return "rules"
    if settings.checker_mode in ("agent", "both"):
        try:
            v = agent_checker(resp.data)
        except CheckUnavailable as e:
            record["errors"] = [str(e)]
            return "agent_unavailable"
        if not v.ok:
            record["errors"] = [v.reason]
            return "agent"
    return None
