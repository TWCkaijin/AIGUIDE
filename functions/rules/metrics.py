"""R-METRIC：成效指標(FR-25)。

規則來源：D-014
- 指標 A「站點間平均移動時間(按路段統計)」：每條路段分開統計有效筆數與平均值，另列中止與資料缺漏筆數。
- 指標 B「必要步驟正確完成率」＝正確完成的必要步驟數 ÷ 應完成的必要步驟數 × 100%。
  正確完成須有站點登錄，且符合前置條件；漏做、無登錄或順序不符留在分母，另列登錄缺漏數；
  終點前經院方取消的步驟移出分母；同一步驟只計一次；沒有必要步驟的行程不納入。
- 試辦目標：指標 A 較基準縮短至少 10%；指標 B 達 95% 以上，且不低於基準。

全部使用 Fraction 計算，避免浮點誤差影響邊界判斷。
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from fractions import Fraction

TARGET_A_MIN_REDUCTION = Fraction(1, 10)  # D-014：縮短至少 10%
TARGET_B_MIN_RATE = Fraction(95)          # D-014：達 95% 以上


def _frac(x) -> Fraction:
    return x if isinstance(x, Fraction) else Fraction(str(x))


# ---- 指標 A ----

@dataclass
class SegmentStat:
    valid_count: int = 0
    total_seconds: Fraction = Fraction(0)
    aborted_count: int = 0   # 有開始、沒有抵達
    missing_count: int = 0   # 沒有開始時間(資料缺漏)

    @property
    def average_seconds(self) -> Fraction | None:
        return self.total_seconds / self.valid_count if self.valid_count else None


def segment_stats(timings: Iterable[Mapping]) -> dict[tuple, SegmentStat]:
    """timings 每筆：{"segment": (起站, 迄站), "start": 秒或 None, "end": 秒或 None}。"""
    stats: dict[tuple, SegmentStat] = {}
    for t in timings:
        s = stats.setdefault(tuple(t["segment"]), SegmentStat())
        if t.get("start") is None:
            s.missing_count += 1
        elif t.get("end") is None:
            s.aborted_count += 1
        else:
            s.valid_count += 1
            s.total_seconds += _frac(t["end"]) - _frac(t["start"])
    return stats


# ---- 指標 B ----

@dataclass
class IndicatorB:
    numerator: int
    denominator: int
    missing_log_count: int

    @property
    def rate_percent(self) -> Fraction | None:
        if self.denominator == 0:
            return None  # 沒有必要步驟的行程不納入
        return Fraction(self.numerator * 100, self.denominator)


def indicator_b(required: Mapping[str, list[str]], logs: Iterable[tuple[str, float]],
                cancelled: set[str]) -> IndicatorB:
    """required：必要步驟 → 前置步驟；logs：(步驟, 登錄時間)；cancelled：院方取消的步驟。"""
    steps = {s: reqs for s, reqs in required.items() if s not in cancelled}
    first_log: dict[str, Fraction] = {}
    for step, t in logs:
        t = _frac(t)
        if step in steps and (step not in first_log or t < first_log[step]):
            first_log[step] = t  # 同一步驟只計一次(以最早登錄為準)

    correct = 0
    for step, reqs in steps.items():
        if step not in first_log:
            continue
        prereqs = [r for r in reqs if r in steps]
        if all(r in first_log and first_log[r] < first_log[step] for r in prereqs):
            correct += 1
    missing = sum(1 for s in steps if s not in first_log)
    return IndicatorB(numerator=correct, denominator=len(steps), missing_log_count=missing)


# ---- 試辦目標 ----

def target_a_met(*, baseline_seconds, trial_seconds) -> bool:
    base = _frac(baseline_seconds)
    return (base - _frac(trial_seconds)) / base >= TARGET_A_MIN_REDUCTION


def target_b_met(*, rate_percent, baseline_percent) -> bool:
    rate = _frac(rate_percent)
    return rate >= TARGET_B_MIN_RATE and rate >= _frac(baseline_percent)
