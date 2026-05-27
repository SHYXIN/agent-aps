"""Rule CRUD 操作"""
import json
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Rule
from app.schemas import RuleCreate


class RuleCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, rule: RuleCreate) -> Rule:
        db_rule = Rule(
            name=rule.name,
            description=rule.description,
            rule_type=rule.rule_type,
            condition_json=json.dumps(rule.condition.model_dump(), ensure_ascii=False),
            action_json=json.dumps(rule.action.model_dump(), ensure_ascii=False),
            free_text=rule.free_text,
            status=rule.status,
            notes=rule.notes,
        )
        self.db.add(db_rule)
        self.db.commit()
        self.db.refresh(db_rule)
        return db_rule

    def get_by_id(self, rule_id: int) -> Optional[Rule]:
        return self.db.query(Rule).filter(Rule.id == rule_id).first()

    def list_all(
        self, rule_type: Optional[str] = None, status: Optional[str] = None
    ) -> list[Rule]:
        query = self.db.query(Rule)
        if rule_type:
            query = query.filter(Rule.rule_type == rule_type)
        if status:
            query = query.filter(Rule.status == status)
        return query.all()

    def update(self, rule_id: int, data: dict) -> Optional[Rule]:
        rule = self.get_by_id(rule_id)
        if rule is None:
            return None
        for key, value in data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete(self, rule_id: int) -> bool:
        rule = self.get_by_id(rule_id)
        if rule is None:
            return False
        self.db.delete(rule)
        self.db.commit()
        return True
