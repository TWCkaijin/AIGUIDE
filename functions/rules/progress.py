"""R-PROGRESS：就醫進度(FR-05、FR-14、FR-17；D-013、D-014、D-031、D-032)。"""
from __future__ import annotations

from collections.abc import Collection, Iterable
from dataclasses import dataclass

from rules.notify import NotificationCenter


class EmptyTodayText(ValueError):
    """今日事務為空白或只有空白字元，視為沒有輸入(D-031、D-032)。"""


class NoExamSelected(ValueError):
    pass


class UnknownExam(ValueError):
    """檢查項目不在預先登錄的清單內(AC-14.2)。"""


@dataclass(frozen=True)
class ProgressResult:
    changed: bool
    needs_replan: bool


class Visit:
    def __init__(self, *, patient_id: str, user_id: str, orders: Iterable[str] = (),
                 registered_exams: Collection[str] = ()):
        self.patient_id = patient_id
        self.user_id = user_id
        self._orders: list[str] = list(orders)
        self._registered = frozenset(registered_exams)
        self.log: list[tuple[str, float]] = []
        self.today_text: str | None = None

    @property
    def orders(self) -> tuple[str, ...]:
        return tuple(self._orders)

    @property
    def completed(self) -> set[str]:
        return {s for s, _ in self.log}

    def set_today_text(self, text: str) -> str:
        stripped = (text or "").strip()
        if not stripped:
            raise EmptyTodayText()
        self.today_text = stripped
        return stripped

    def complete_step(self, step_id: str, at: float) -> ProgressResult:
        """站點人員登錄完成(模擬)。同一步驟只記一次，以最早時間為準(D-014)。"""
        for i, (s, t) in enumerate(self.log):
            if s == step_id:
                if at < t:
                    self.log[i] = (s, at)
                return ProgressResult(changed=False, needs_replan=False)
        self.log.append((step_id, at))
        return ProgressResult(changed=True, needs_replan=True)

    def add_orders(self, exam_ids: Iterable[str]) -> bool:
        """全部驗證通過才加入；回傳是否有新增。"""
        exam_ids = list(exam_ids)
        if not exam_ids:
            raise NoExamSelected()
        for e in exam_ids:
            if e not in self._registered:
                raise UnknownExam(e)
        new = [e for e in dict.fromkeys(exam_ids) if e not in self._orders]
        self._orders.extend(new)
        return bool(new)


def push_orders(visit: Visit, exam_ids: Iterable[str], *, notifier: NotificationCenter) -> bool:
    """模擬醫囑推送：有新增才送一則通知(只給該次就醫的使用者)。"""
    changed = visit.add_orders(exam_ids)
    if changed:
        notifier.send_schedule_updated(visit.user_id)
    return changed
