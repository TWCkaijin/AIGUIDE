"""R-WL 白名單：組成送給 AI 的病人資料(FR-07、FR-22)。

規則來源：
- D-006：病人資料只有姓名、年齡、性別、醫囑、無障礙需求。
- D-030：缺少無障礙需求時，視為「無需求」。
"""
from collections.abc import Mapping
import copy

WHITELIST_FIELDS: tuple[str, ...] = ("name", "age", "sex", "orders", "accessibility_need")


def build_llm_patient(patient: Mapping) -> dict:
    """只取白名單欄位，回傳新的 dict，不改動傳入的資料(design.md P2、P7)。"""
    out = {k: copy.deepcopy(patient[k]) for k in WHITELIST_FIELDS if k in patient}
    if "accessibility_need" not in out:
        out["accessibility_need"] = False  # D-030
    return out
