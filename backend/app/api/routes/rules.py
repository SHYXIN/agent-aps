"""规则 CRUD 路由"""
import json

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse
from app.services.crud import RuleCRUD
from app.services.conflict import ConflictDetector
from app.services.changelog import ChangelogStore


def _to_response(rule) -> dict:
    """将 Rule ORM 对象转为响应 dict"""
    return RuleResponse.model_validate(rule).model_dump()


def register_rule_routes(app):
    """注册规则相关路由"""

    @app.post("/api/rules", status_code=201)
    def create_rule(rule: RuleCreate, db: Session = Depends(get_db)):
        crud = RuleCRUD(db)
        conflict_detector = ConflictDetector(crud.list_all())
        conflicts = conflict_detector.check(rule)
        if conflicts:
            return {
                "status": "conflict",
                "conflicts": conflicts,
                "message": "检测到规则冲突，请确认是否覆盖",
            }
        created = crud.create(rule)
        ChangelogStore(db).log(
            rule_id=created.id,
            action="create",
            after_value={"name": created.name},
        )
        return _to_response(created)

    @app.post("/api/rules/force", status_code=201, response_model=RuleResponse)
    def create_rule_force(rule: RuleCreate, db: Session = Depends(get_db)):
        """强制创建规则（用户确认覆盖冲突后调用）"""
        crud = RuleCRUD(db)
        created = crud.create(rule)
        ChangelogStore(db).log(
            rule_id=created.id,
            action="create",
            after_value={"name": created.name},
        )
        return _to_response(created)

    @app.get("/api/rules")
    def list_rules(
        rule_type: str | None = None,
        status: str | None = None,
        db: Session = Depends(get_db),
    ):
        crud = RuleCRUD(db)
        return [_to_response(r) for r in crud.list_all(rule_type=rule_type, status=status)]

    @app.get("/api/rules/{rule_id}", response_model=RuleResponse)
    def get_rule(rule_id: int, db: Session = Depends(get_db)):
        crud = RuleCRUD(db)
        rule = crud.get_by_id(rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        return _to_response(rule)

    @app.put("/api/rules/{rule_id}", response_model=RuleResponse)
    def update_rule(rule_id: int, data: RuleUpdate, db: Session = Depends(get_db)):
        crud = RuleCRUD(db)
        old_rule = crud.get_by_id(rule_id)
        if old_rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        # 只更新非 None 字段
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        rule = crud.update(rule_id, update_data)
        ChangelogStore(db).log(
            rule_id=rule_id,
            action="update",
            before_value={"name": old_rule.name},
            after_value=update_data,
        )
        return _to_response(rule)

    @app.delete("/api/rules/{rule_id}")
    def delete_rule(rule_id: int, db: Session = Depends(get_db)):
        crud = RuleCRUD(db)
        old_rule = crud.get_by_id(rule_id)
        if old_rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        crud.delete(rule_id)
        ChangelogStore(db).log(
            rule_id=rule_id,
            action="delete",
            before_value={"name": old_rule.name},
        )
        return {"ok": True}

    @app.post("/api/rules/conflict-check")
    def conflict_check(rule: RuleCreate, db: Session = Depends(get_db)):
        """预检规则冲突（不写入）"""
        crud = RuleCRUD(db)
        detector = ConflictDetector(crud.list_all())
        conflicts = detector.check(rule)
        return {"has_conflict": len(conflicts) > 0, "conflicts": conflicts}

    @app.get("/api/rules/{rule_id}/changelog")
    def get_rule_changelog(rule_id: int, db: Session = Depends(get_db)):
        store = ChangelogStore(db)
        return store.list_by_rule(rule_id)

    @app.get("/api/changelog")
    def get_all_changelog(db: Session = Depends(get_db)):
        store = ChangelogStore(db)
        return store.list_all()
