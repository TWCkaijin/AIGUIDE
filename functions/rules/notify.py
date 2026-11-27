"""R-NOTIFY：站內通知(D-013、D-015、AC-14.3、AC-20.5)。

- 醫囑推送使行程變更：只通知該次就醫的使用者，文案固定，不列出醫囑內容。
- 路線或站點變動：同一導引工作階段、同一發布版本只推送一次。
"""
from __future__ import annotations

from dataclasses import dataclass

SCHEDULE_UPDATED_TEXT = "今日行程已更新，請確認下一站"  # D-013
# 路線變動通知的文案，規格沒有指定；暫沿用 D-013 的文案，待小組確認(見 DEVLOG 2026-11-27 階段 5)。
ROUTE_CHANGED_TEXT = SCHEDULE_UPDATED_TEXT


@dataclass(frozen=True)
class Notification:
    user_id: str
    kind: str  # schedule_updated / route_changed
    text: str
    session_id: str | None = None
    version: str | None = None


class NotificationCenter:
    def __init__(self):
        self._items: list[Notification] = []
        self._sent_keys: set[tuple[str, str]] = set()

    def send_schedule_updated(self, user_id: str) -> Notification:
        n = Notification(user_id, "schedule_updated", SCHEDULE_UPDATED_TEXT)
        self._items.append(n)
        return n

    def send_route_changed(self, user_id: str, session_id: str, version: str) -> Notification | None:
        key = (session_id, version)
        if key in self._sent_keys:
            return None
        self._sent_keys.add(key)
        n = Notification(user_id, "route_changed", ROUTE_CHANGED_TEXT, session_id, version)
        self._items.append(n)
        return n

    def items_for(self, user_id: str) -> list[Notification]:
        return [n for n in self._items if n.user_id == user_id]
