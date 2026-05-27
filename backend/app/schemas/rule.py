"""Rule Schema 定义"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class Condition(BaseModel):
    field: str
    operator: str
    value: str | int | float | list | None = None


class Action(BaseModel):
    field: str
    operator: str
    value: str | int | float | list | None = None


class RuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: str  # "data_cleaning" | "scheduling"
    condition: Condition
    action: Action
    free_text: Optional[str] = None
    status: str = "active"
    notes: Optional[str] = None

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v: str) -> str:
        if v not in ("data_cleaning", "scheduling"):
            raise ValueError("rule_type must be 'data_cleaning' or 'scheduling'")
        return v


class RuleUpdate(BaseModel):
    """部分更新规则——所有字段可选"""
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    condition: Optional[Condition] = None
    action: Optional[Action] = None
    free_text: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("data_cleaning", "scheduling"):
            raise ValueError("rule_type must be 'data_cleaning' or 'scheduling'")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("active", "disabled"):
            raise ValueError("status must be 'active' or 'disabled'")
        return v


class RuleResponse(BaseModel):
    """规则响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    rule_type: str
    condition_json: str
    action_json: str
    free_text: Optional[str] = None
    status: str
    source: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
