"""Agent 对话翻译测试"""
import pytest
from app.services.agent import AgentTranslator, ConversationState


class TestConversationState:
    """测试对话状态管理"""

    def test_initial_state(self):
        """初始状态：空对话，无待确认规则"""
        state = ConversationState()
        assert state.messages == []
        assert state.pending_rule is None
        assert state.is_complete is False

    def test_add_message(self):
        """添加对话消息"""
        state = ConversationState()
        state.add_message("user", "含硼钢炉容打八折")
        assert len(state.messages) == 1
        assert state.messages[0]["role"] == "user"

    def test_set_pending_rule(self):
        """设置待确认规则"""
        state = ConversationState()
        state.set_pending_rule({"name": "含硼钢炉容折扣", "rule_type": "data_cleaning"})
        assert state.pending_rule is not None
        assert state.pending_rule["name"] == "含硼钢炉容折扣"

    def test_confirm_rule(self):
        """确认规则后状态清空"""
        state = ConversationState()
        state.set_pending_rule({"name": "test"})
        state.confirm_rule()
        assert state.pending_rule is None

    def test_missing_info_tracking(self):
        """追踪缺失信息"""
        state = ConversationState()
        state.add_missing_info("discount_value")
        assert "discount_value" in state.missing_info

    def test_is_complete_when_all_info_collected(self):
        """所有信息收集完毕且有 pending_rule 时 is_complete=True"""
        state = ConversationState()
        state.add_missing_info("discount_value")
        state.collected_info["discount_value"] = 0.8
        state.missing_info.clear()
        state.set_pending_rule({"name": "test"})
        assert state.is_complete


class TestAgentTranslator:
    """测试 Agent 翻译逻辑（不依赖外部 LLM API）"""

    def test_parse_user_input_basic(self):
        """解析用户基本输入"""
        agent = AgentTranslator()
        result = agent.parse_user_input("含硼钢炉容打八折")
        # 应该识别出：钢种=B，动作=炉容打折，折扣=0.8
        assert result is not None

    def test_ask_clarification_for_vague_input(self):
        """模糊输入时反问用户"""
        agent = AgentTranslator()
        result = agent.parse_user_input("含硼钢的炉容少算点")
        # 应该返回需要澄清的问题
        assert result.get("needs_clarification") is True
        assert "discount_value" in result.get("missing_fields", [])

    def test_build_rule_from_collected_info(self):
        """从收集的信息构建规则"""
        agent = AgentTranslator()
        info = {
            "name": "含硼钢炉容折扣",
            "rule_type": "data_cleaning",
            "condition": {"field": "steel_grade", "operator": "contains", "value": "B"},
            "action": {"field": "furnace_capacity", "operator": "multiply", "value": 0.8},
        }
        rule = agent.build_rule(info)
        assert rule["name"] == "含硼钢炉容折扣"
        assert rule["rule_type"] == "data_cleaning"

    def test_determine_rule_type_data_cleaning(self):
        """判断为数据清洗规则"""
        agent = AgentTranslator()
        rule_type = agent.determine_rule_type("炉容容量按80%计算")
        assert rule_type == "data_cleaning"

    def test_determine_rule_type_scheduling(self):
        """判断为排程约束规则"""
        agent = AgentTranslator()
        rule_type = agent.determine_rule_type("Q345不能和Q235连续浇铸")
        assert rule_type == "scheduling"
