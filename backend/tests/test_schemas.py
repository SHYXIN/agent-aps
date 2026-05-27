"""Rule Schema 验证测试"""
import pytest
from pydantic import ValidationError
from app.schemas import RuleCreate


class TestRuleSchema:
    """测试规则 JSON Schema 的合法性校验"""

    def test_valid_data_cleaning_rule(self):
        """一条合法的数据清洗规则（Rule A）应该通过验证"""
        rule = RuleCreate(
            name="含硼钢炉容折扣",
            description="含硼钢种的炉容容量按80%计算",
            rule_type="data_cleaning",
            condition={"field": "steel_grade", "operator": "contains", "value": "B"},
            action={"field": "furnace_capacity", "operator": "multiply", "value": 0.8},
        )
        assert rule.name == "含硼钢炉容折扣"
        assert rule.rule_type == "data_cleaning"

    def test_valid_scheduling_rule(self):
        """一条合法的排程业务规则（Rule B）应该通过验证"""
        rule = RuleCreate(
            name="Q345不能和Q235连续浇铸",
            rule_type="scheduling",
            condition={"field": "steel_grade_pair", "operator": "incompatible", "value": ["Q345", "Q235"]},
            action={"field": "casting_sequence", "operator": "block"},
        )
        assert rule.rule_type == "scheduling"

    def test_rule_type_must_be_data_cleaning_or_scheduling(self):
        """rule_type 只能是 data_cleaning 或 scheduling"""
        with pytest.raises(ValidationError):
            RuleCreate(
                name="test",
                rule_type="invalid_type",
                condition={"field": "x", "operator": "eq", "value": 1},
                action={"field": "y", "operator": "set", "value": 2},
            )

    def test_name_is_required(self):
        """name 字段必填"""
        with pytest.raises(ValidationError):
            RuleCreate(
                rule_type="data_cleaning",
                condition={"field": "x", "operator": "eq", "value": 1},
                action={"field": "y", "operator": "set", "value": 2},
            )

    def test_condition_must_have_field_operator_value(self):
        """condition 必须包含 field、operator、value"""
        with pytest.raises(ValidationError):
            RuleCreate(
                name="test",
                rule_type="data_cleaning",
                condition={"field": "x"},  # 缺少 operator 和 value
                action={"field": "y", "operator": "set", "value": 2},
            )

    def test_free_text_rule(self):
        """无法结构化的规则可以用 free_text 存储"""
        rule = RuleCreate(
            name="经验温度调整",
            rule_type="data_cleaning",
            condition={"field": "steel_grade", "operator": "contains", "value": "B"},
            action={"field": "temperature", "operator": "add", "value": 20},
            free_text="经验上1号炉出钢温度要比标准高20度，老师傅说的",
        )
        assert rule.free_text is not None

    def test_default_status_is_active(self):
        """新规则默认状态为 active"""
        rule = RuleCreate(
            name="test",
            rule_type="data_cleaning",
            condition={"field": "x", "operator": "eq", "value": 1},
            action={"field": "y", "operator": "set", "value": 2},
        )
        assert rule.status == "active"

    def test_notes_field_is_optional(self):
        """notes 字段可选"""
        rule = RuleCreate(
            name="test",
            rule_type="data_cleaning",
            condition={"field": "x", "operator": "eq", "value": 1},
            action={"field": "y", "operator": "set", "value": 2},
        )
        assert rule.notes is None
