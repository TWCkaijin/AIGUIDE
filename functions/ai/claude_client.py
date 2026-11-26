"""A-CLIENT：模型呼叫介面(AC-NFR01.1、AC-NFR01.2；D-029)。

本階段只定義介面、組請求與缺金鑰行為；真實 API 呼叫在階段 7。
金鑰只從後端環境變數 ANTHROPIC_API_KEY 讀取。
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Protocol

from rules.plan_pipeline import PipelineSettings, PlanInput

MODEL_ID = "claude-haiku-5-5"  # AC-NFR01.2
log = logging.getLogger(__name__)


class AiError(Exception):
    """模型呼叫失敗的共同父類別。"""


class AiUnavailable(AiError):
    """服務無法連線、金鑰未設定等：不重試，直接走服務台備援(AC-NFR01.3)。"""


class AiTimeout(AiError):
    """單次呼叫逾時：視為 AI 失敗，計入重試(D-029)。"""


@dataclass
class AiPlanResponse:
    data: Any
    stop_reason: str


class PlannerClient(Protocol):
    def plan(self, plan_input: PlanInput, *, timeout_seconds: float, max_tokens: int) -> AiPlanResponse: ...


def build_request(plan_input: PlanInput, settings: PipelineSettings, *, system_prompt: str) -> dict:
    """組成送給模型的請求。使用者訊息只含 PlanInput(病人資料已是白名單欄位)；不提供寫入型工具。"""
    return {
        "model": MODEL_ID,
        "max_tokens": settings.max_tokens,
        "timeout": settings.call_timeout_seconds,
        "system": system_prompt,
        "messages": [{"role": "user", "content": plan_input.to_json()}],
    }


class ClaudePlannerClient:
    def __init__(self, api_key: str | None, *, system_prompt: str):
        self._api_key = api_key
        self._system_prompt = system_prompt
        if not api_key:
            log.error("ANTHROPIC_API_KEY 未設定：規劃請求將改走服務台備援")

    @classmethod
    def from_env(cls, *, system_prompt: str) -> "ClaudePlannerClient":
        return cls(os.environ.get("ANTHROPIC_API_KEY"), system_prompt=system_prompt)

    @property
    def has_key(self) -> bool:
        return bool(self._api_key)

    def plan(self, plan_input: PlanInput, *, timeout_seconds: float, max_tokens: int) -> AiPlanResponse:
        if not self._api_key:
            raise AiUnavailable("ANTHROPIC_API_KEY 未設定")
        raise NotImplementedError("真實 API 呼叫在階段 7 實作")
