"""R-DEMO 範例草案(D-038)：只在「檢查者模式」欄位提供，載入後只產生草稿。"""
import pytest

from rules.demo_drafts import ExampleNotFound, FieldHasNoExamples, list_examples, load_example
from rules.plan_pipeline import CHECKER_MODES, PipelineSettings


def test_tc_demo_01_three_examples_labelled():
    ex = list_examples("checker_mode")
    assert sorted(e.value for e in ex) == sorted(CHECKER_MODES)
    assert len(ex) == 3 and all(e.label == "範例" for e in ex)


@pytest.mark.parametrize("field", ["retry_limit", "prompt", "call_timeout_seconds", "unknown"])
def test_tc_demo_02_other_fields_rejected(field):
    with pytest.raises(FieldHasNoExamples):
        list_examples(field)
    with pytest.raises(FieldHasNoExamples):
        load_example(field, "anything")


def test_tc_demo_03_load_only_makes_draft_current_settings_unchanged():
    current = PipelineSettings()
    ex = list_examples("checker_mode")[0]
    draft = load_example("checker_mode", ex.id)
    assert draft.is_example is True and draft.status == "draft"
    assert current.checker_mode == "rules"


def test_tc_demo_04_example_values_are_valid_modes():
    for e in list_examples("checker_mode"):
        PipelineSettings(checker_mode=e.value)


def test_tc_demo_05_examples_only_touch_checker_mode():
    for e in list_examples("checker_mode"):
        draft = load_example("checker_mode", e.id)
        assert draft.changes == {"checker_mode": e.value}


def test_example_ids_unique_and_have_descriptions():
    ex = list_examples("checker_mode")
    assert len({e.id for e in ex}) == 3 and all(e.description for e in ex)


def test_tc_demo_06_unknown_example_rejected():
    with pytest.raises(ExampleNotFound):
        load_example("checker_mode", "no-such-example")
