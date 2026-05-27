"""规则冲突检测"""
import json


class ConflictDetector:
    """检测新规则与现有规则的直接矛盾

    只检测：同类型 + 同条件（field + operator + value）+ 不同动作
    不做语义推理，模糊冲突交给用户确认

    existing_rules: ORM 对象列表 或 dict 列表，每个元素需有:
      - name: str
      - rule_type: str
      - condition / condition_json: dict 或 JSON 字符串
      - action / action_json: dict 或 JSON 字符串
    new_rule: RuleCreate 或 dict，需有:
      - rule_type: str
      - condition: dict
      - action: dict
    """

    def __init__(self, existing_rules: list):
        self.existing_rules = existing_rules

    def check(self, new_rule) -> list[dict]:
        new_type = new_rule.rule_type if hasattr(new_rule, "rule_type") else new_rule.get("rule_type")
        new_cond = self._parse_condition(new_rule)
        new_act = self._parse_action(new_rule)

        conflicts = []
        for existing in self.existing_rules:
            ex_type = existing.rule_type if hasattr(existing, "rule_type") else existing["rule_type"]
            ex_name = existing.name if hasattr(existing, "name") else existing.get("name", "unknown")
            ex_cond = self._parse_condition(existing)
            ex_act = self._parse_action(existing)

            if self._is_conflict(ex_type, ex_name, ex_cond, ex_act, new_type, new_cond, new_act):
                conflicts.append({
                    "existing_rule": ex_name,
                    "reason": "same_condition_different_action",
                })
        return conflicts

    def _parse_condition(self, rule):
        if hasattr(rule, "condition"):
            raw = rule.condition
        elif hasattr(rule, "condition_json"):
            raw = rule.condition_json
        else:
            raw = rule.get("condition") or rule.get("condition_json")
        return json.loads(raw) if isinstance(raw, str) else raw

    def _parse_action(self, rule):
        if hasattr(rule, "action"):
            raw = rule.action
        elif hasattr(rule, "action_json"):
            raw = rule.action_json
        else:
            raw = rule.get("action") or rule.get("action_json")
        return json.loads(raw) if isinstance(raw, str) else raw

    def _is_conflict(self, ex_type, ex_name, ex_cond, ex_act, new_type, new_cond, new_act):
        if ex_type != new_type:
            return False
        if not self._same_condition(ex_cond, new_cond):
            return False
        if self._same_action(ex_act, new_act):
            return False
        return True

    def _to_dict(self, obj):
        """统一转 dict：Pydantic 对象、dict、或其他"""
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return obj

    def _same_condition(self, a, b) -> bool:
        a, b = self._to_dict(a), self._to_dict(b)
        return (a.get("field") == b.get("field")
                and a.get("operator") == b.get("operator")
                and a.get("value") == b.get("value"))

    def _same_action(self, a, b) -> bool:
        a, b = self._to_dict(a), self._to_dict(b)
        return (a.get("field") == b.get("field")
                and a.get("operator") == b.get("operator")
                and a.get("value") == b.get("value"))
