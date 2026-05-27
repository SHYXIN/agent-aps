"""Agent 对话路由"""
import json

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.rule import RuleCreate
from app.services.crud import RuleCRUD
from app.services.conflict import ConflictDetector
from app.services.changelog import ChangelogStore
from app.services.agent import AgentTranslator, ConversationState


# 简易内存存储对话状态（生产环境应存 Redis/DB）
_agent_states: dict[str, ConversationState] = {}


def _get_state(session_id: str) -> ConversationState:
    if session_id not in _agent_states:
        _agent_states[session_id] = ConversationState()
    return _agent_states[session_id]


def _format_rule_confirmation(rule: dict) -> str:
    """格式化规则确认信息"""
    lines = [
        "我理解为您想创建以下规则：",
        f"  名称：{rule.get('name', '未命名')}",
        f"  类型：{'数据清洗' if rule.get('rule_type') == 'data_cleaning' else '排程约束'}",
        f"  条件：{rule.get('condition', {})}",
        f"  动作：{rule.get('action', {})}",
        "",
        "是否确认写入？",
    ]
    return "\n".join(lines)


def register_agent_routes(app):
    """注册 Agent 路由"""

    @app.post("/api/agent/chat")
    def agent_chat(payload: dict, db: Session = Depends(get_db)):
        """Agent 多轮对话接口"""
        session_id = payload.get("session_id", "default")
        message = payload.get("message", "")
        state = _get_state(session_id)
        state.add_message("user", message)

        translator = AgentTranslator()
        crud = RuleCRUD(db)

        # 如果有待确认的规则，且用户回复了"确认"
        if state.pending_rule and message.strip() in ("确认", "是的", "对", "ok", "OK"):
            rule_data = state.pending_rule
            rule = RuleCreate(**rule_data)
            detector = ConflictDetector(crud.list_all())
            conflicts = detector.check(rule)
            if conflicts:
                state.confirm_rule()
                reply = f"检测到与以下规则冲突：{[c['existing_rule'] for c in conflicts]}。请确认是否强制写入？"
                return {
                    "reply": reply,
                    "pending_rule": rule_data,
                    "needs_confirmation": True,
                    "has_conflict": True,
                    "conflicts": conflicts,
                }
            created = crud.create(rule)
            ChangelogStore(db).log(
                rule_id=created.id,
                action="create",
                after_value={"name": created.name, "source": "dialogue"},
            )
            state.confirm_rule()
            return {
                "reply": f"规则「{created.name}」已写入规则库。",
                "pending_rule": None,
                "needs_confirmation": False,
                "created_id": created.id,
            }

        # 如果正在收集缺失信息
        if state.missing_info:
            field = state.missing_info[0]
            state.collect_info(field, message.strip())
            if not state.missing_info:
                rule_data = translator.build_rule(state.collected_info)
                state.set_pending_rule(rule_data)
                reply = _format_rule_confirmation(rule_data)
                return {
                    "reply": reply,
                    "pending_rule": rule_data,
                    "needs_confirmation": True,
                    "needs_clarification": False,
                }
            else:
                question = translator.generate_clarification_question(state)
                return {
                    "reply": question,
                    "pending_rule": None,
                    "needs_confirmation": False,
                    "needs_clarification": True,
                    "clarification_question": question,
                }

        # 新的用户输入
        result = translator.parse_user_input(message)

        if result.get("needs_clarification"):
            for field in result.get("missing_fields", []):
                state.add_missing_info(field)
            partial = result.get("partial_info", {})
            for k, v in partial.items():
                state.collected_info[k] = v
            state.collected_info["rule_type"] = translator.determine_rule_type(message)
            question = result.get("clarification_question",
                                  translator.generate_clarification_question(state))
            return {
                "reply": question,
                "pending_rule": None,
                "needs_confirmation": False,
                "needs_clarification": True,
                "clarification_question": question,
            }

        # needs_llm 分支已废弃（parse_user_input 内部已调用 LLM）
        # 保留作为兜底
        if result.get("needs_llm"):
            return {
                "reply": "抱歉，无法解析您的描述。请尝试更明确的描述，如：含硼钢炉容打八折。",
                "pending_rule": None,
                "needs_confirmation": False,
                "needs_clarification": False,
            }

        # 直接翻译成功
        rule_data = translator.build_rule(result)
        state.set_pending_rule(rule_data)
        reply = _format_rule_confirmation(rule_data)
        return {
            "reply": reply,
            "pending_rule": rule_data,
            "needs_confirmation": True,
            "needs_clarification": False,
        }
