"""Rule Schema 定义"""
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
