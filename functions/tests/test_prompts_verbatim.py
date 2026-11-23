"""P4：提示詞檔中的原文段落必須與 AI-specification.md 逐字相同。"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC_LINES = set((ROOT / "AI-specification.md").read_text(encoding="utf-8").split("\n"))
PROMPTS = Path(__file__).resolve().parents[1] / "prompts"


def _quoted_lines(path: Path):
    """去掉檔案自己加的標題、註解與分隔線，其餘每一行都必須是規格原文。"""
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line == "" or line == "---" or line.startswith("# ") or line.startswith("<!--"):
            continue
        yield line


@pytest.mark.parametrize("name", ["planner.system.md", "checker.system.md"])
def test_prompt_lines_are_verbatim_spec(name):
    lines = list(_quoted_lines(PROMPTS / name))
    assert lines, f"{name} 沒有任何原文段落"
    missing = [l for l in lines if l not in SPEC_LINES]
    assert missing == [], f"{name} 有不在規格書中的文字：{missing}"
