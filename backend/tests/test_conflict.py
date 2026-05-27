"""规则冲突检测测试"""
import pytest
from app.services.conflict import ConflictDetector


def make_rule(name="test", rule_type="data_cleaning", field="steel_grade",
              operator="contains", value="B", action_field="furnace_capacity",
              action_operator="multiply", action_value=0.8):
    """创建模拟 ORM 规则的 dict"""
    return {
        "name": name,
        "rule_type": rule_type,
        "condition": {"field": field, "operator": operator, "value": value},
        "action": {"field": action_field, "operator": action_operator, "value": action_value},
    }


def make_new_rule(**kwargs):
    """创建新规则 dict（API 端点使用的格式）"""
    defaults = {
        "rule_type": "data_cleaning",
        "condition": {"field": "steel_grade", "operator": "contains", "value": "B"},
        "action": {"field": "furnace_capacity", "operator": "multiply", "value": 0.8},
    }
    defaults.update(kwargs)
    return defaults


class TestConflictDetector:

    def test_no_conflict_when_empty(self):
        """空规则库，任何规则都不冲突"""
        detector = ConflictDetector([])
        conflicts = detector.check(make_new_rule())
        assert conflicts == []

    def test_no_conflict_different_condition(self):
        """条件不同，不冲突"""
        existing = [make_rule(field="steel_grade", value="B")]
        detector = ConflictDetector(existing)
        new_rule = make_new_rule(condition={"field": "steel_grade", "operator": "contains", "value": "C"})
        conflicts = detector.check(new_rule)
        assert conflicts == []

    def test_conflict_same_condition_different_action(self):
        """同条件、不同动作 → 直接矛盾"""
        existing = [make_rule(name="规则A", action_value=0.8)]
        detector = ConflictDetector(existing)
        new_rule = make_new_rule(action={"field": "furnace_capacity", "operator": "multiply", "value": 0.9})
        conflicts = detector.check(new_rule)
        assert len(conflicts) == 1
        assert conflicts[0]["existing_rule"] == "规则A"
        assert conflicts[0]["reason"] == "same_condition_different_action"

    def test_no_conflict_same_condition_same_action(self):
        """同条件、同动作 → 不冲突（重复但不矛盾）"""
        existing = [make_rule(action_value=0.8)]
        detector = ConflictDetector(existing)
        conflicts = detector.check(make_new_rule())
        assert conflicts == []

    def test_conflict_different_rule_type(self):
        """不同类型（data_cleaning vs scheduling），同条件也不冲突"""
        existing = [make_rule(rule_type="data_cleaning")]
        detector = ConflictDetector(existing)
        new_rule = make_new_rule(rule_type="scheduling")
        conflicts = detector.check(new_rule)
        assert conflicts == []

    def test_multiple_conflicts(self):
        """新规则同时与多条现有规则冲突"""
        existing = [
            make_rule(name="规则A", action_value=0.7),
            make_rule(name="规则B", action_value=0.9),
        ]
        detector = ConflictDetector(existing)
        conflicts = detector.check(make_new_rule())
        assert len(conflicts) == 2

    def test_conflict_with_mixed_conditions(self):
        """只有一部分条件匹配时，不冲突"""
        existing = [make_rule(field="steel_grade", value="B", action_field="furnace_capacity")]
        detector = ConflictDetector(existing)
        new_rule = make_new_rule(condition={"field": "steel_grade", "operator": "contains", "value": "C"})
        conflicts = detector.check(new_rule)
        assert conflicts == []

    def test_with_json_string_condition(self):
        """condition_json / action_json 为 JSON 字符串时也能正确解析"""
        import json
        existing = [{
            "name": "规则A",
            "rule_type": "data_cleaning",
            "condition_json": json.dumps({"field": "steel_grade", "operator": "contains", "value": "B"}),
            "action_json": json.dumps({"field": "furnace_capacity", "operator": "multiply", "value": 0.8}),
        }]
        detector = ConflictDetector(existing)
        new_rule = make_new_rule(action={"field": "furnace_capacity", "operator": "multiply", "value": 0.9})
        conflicts = detector.check(new_rule)
        assert len(conflicts) == 1
