"""Schema 验证测试"""
import pytest
from pydantic import ValidationError
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse, Condition, Action


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
                condition={"field": "x"},
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


class TestRuleUpdate:
    """测试 RuleUpdate schema"""

    def test_all_fields_optional(self):
        """RuleUpdate 所有字段都是可选的"""
        update = RuleUpdate()
        assert update.name is None
        assert update.status is None

    def test_partial_update(self):
        """可以只更新部分字段"""
        update = RuleUpdate(name="新名称")
        assert update.name == "新名称"
        assert update.status is None

    def test_status_validation(self):
        """status 只能是 active 或 disabled"""
        update = RuleUpdate(status="active")
        assert update.status == "active"
        update = RuleUpdate(status="disabled")
        assert update.status == "disabled"

    def test_invalid_status(self):
        """无效的 status 值"""
        with pytest.raises(ValidationError):
            RuleUpdate(status="invalid")


class TestRuleResponse:
    """测试 RuleResponse schema"""

    def test_from_orm(self):
        """可以从 ORM 对象创建 Response"""
        from datetime import datetime, timezone
        class FakeRule:
            id = 1
            name = "测试规则"
            description = "测试"
            rule_type = "data_cleaning"
            condition_json = '{"field": "x"}'
            action_json = '{"field": "y"}'
            free_text = None
            status = "active"
            source = "manual"
            notes = None
            created_at = datetime(2026, 5, 27, tzinfo=timezone.utc)
            updated_at = datetime(2026, 5, 27, tzinfo=timezone.utc)

        resp = RuleResponse.model_validate(FakeRule())
        assert resp.id == 1
        assert resp.name == "测试规则"
        assert resp.status == "active"

    def test_serialization(self):
        """可以序列化为 JSON"""
        from datetime import datetime, timezone
        resp = RuleResponse(
            id=1,
            name="测试规则",
            description=None,
            rule_type="data_cleaning",
            condition_json="{}",
            action_json="{}",
            free_text=None,
            status="active",
            source="manual",
            notes=None,
            created_at=datetime(2026, 5, 27, tzinfo=timezone.utc),
            updated_at=datetime(2026, 5, 27, tzinfo=timezone.utc),
        )
        data = resp.model_dump()
        assert data["id"] == 1
        assert data["name"] == "测试规则"
