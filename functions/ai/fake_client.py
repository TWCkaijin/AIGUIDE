"""假的模型客戶端與時鐘，供測試與示範使用(不連網)。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ai.claude_client import AiPlanResponse


class FakeClock:
    def __init__(self, start: float = 0.0):
        self._t = start

    def now(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds


@dataclass
class Step:
    """一次呼叫的腳本：結果(回應、例外或函式)與這次呼叫花的秒數。"""
    result: Any
    elapsed: float = 0


class FakePlannerClient:
    def __init__(self, steps: list, clock: FakeClock | None = None):
        self._steps = list(steps)
        self._clock = clock
        self.calls: list[dict] = []

    def plan(self, plan_input, *, timeout_seconds, max_tokens) -> AiPlanResponse:
        self.calls.append({"timeout_seconds": timeout_seconds, "max_tokens": max_tokens})
        assert self._steps, "假客戶端的腳本已用完"
        step = self._steps.pop(0)
        if not isinstance(step, Step):
            step = Step(step)
        if self._clock and step.elapsed:
            self._clock.advance(step.elapsed)
        result = step.result
        if callable(result) and not isinstance(result, Exception):
            result = result(plan_input)
        if isinstance(result, Exception):
            raise result
        return result
