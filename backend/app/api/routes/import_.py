"""批量导入路由"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.crud import RuleCRUD
from app.services.importer import RuleImporter


def register_import_routes(app):
    """注册批量导入路由"""

    @app.post("/api/rules/import/preview")
    def import_preview(rules: list[dict], db: Session = Depends(get_db)):
        """批量导入预览（不写入）"""
        crud = RuleCRUD(db)
        importer = RuleImporter(crud.list_all())
        result = importer.preview(rules)
        return {
            "total": result.total,
            "valid_count": result.valid_count,
            "error_count": result.error_count,
            "conflict_count": result.conflict_count,
            "errors": result.errors,
            "conflicts": result.conflicts,
        }

    @app.post("/api/rules/import")
    def import_rules(rules: list[dict], db: Session = Depends(get_db)):
        """批量导入规则（跳过有冲突和错误的）"""
        crud = RuleCRUD(db)
        importer = RuleImporter(crud.list_all())
        result = importer.execute(db, rules)
        return {
            "imported": result.created_count,
            "skipped_conflicts": result.skipped_conflicts,
            "skipped_errors": result.skipped_errors,
        }
