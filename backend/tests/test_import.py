"""规则批量导入测试"""
import json
import pytest
from app.services.importer import RuleImporter, ImportResult
from app.schemas.rule import RuleCreate
from app.services.crud import RuleCRUD


def make_rule(name="规则A", rule_type="data_cleaning", value="B", action_value=0.8):
    return {
        "name": name,
        "rule_type": rule_type,
        "condition": {"field": "steel_grade", "operator": "contains", "value": value},
        "action": {"field": "furnace_capacity", "operator": "multiply", "value": action_value},
    }


class TestRuleImporter:

    def test_import_valid_rules(self):
        """导入合法规则"""
        rules = [make_rule(name="规则A"), make_rule(name="规则B")]
        importer = RuleImporter(existing_rules=[])
        result = importer.preview(rules)
        assert result.valid_count == 2
        assert result.error_count == 0
        assert result.conflict_count == 0

    def test_import_with_invalid_rule(self):
        """包含非法规则（缺少必填字段）"""
        rules = [
            make_rule(name="合法规则"),
            {"name": "", "rule_type": "data_cleaning", "condition": {}, "action": {}},  # 无效
        ]
        importer = RuleImporter(existing_rules=[])
        result = importer.preview(rules)
        assert result.valid_count == 1
        assert result.error_count == 1

    def test_import_with_invalid_rule_type(self):
        """rule_type 不合法"""
        rules = [make_rule(name="test", rule_type="invalid_type")]
        importer = RuleImporter(existing_rules=[])
        result = importer.preview(rules)
        assert result.valid_count == 0
        assert result.error_count == 1

    def test_import_with_conflict(self):
        """导入规则与现有规则冲突"""
        existing = [RuleCreate(**make_rule(name="已有规则", action_value=0.8))]
        rules = [make_rule(name="新规则", action_value=0.9)]
        importer = RuleImporter(existing_rules=existing)
        result = importer.preview(rules)
        assert result.valid_count == 1
        assert result.conflict_count == 1

    def test_import_empty_list(self):
        """空列表导入"""
        importer = RuleImporter(existing_rules=[])
        result = importer.preview([])
        assert result.valid_count == 0
        assert result.total == 0

    def test_import_result_summary(self):
        """导入结果摘要"""
        rules = [
            make_rule(name="规则A"),
            make_rule(name="规则B"),
            {"name": "", "rule_type": "data_cleaning", "condition": {}, "action": {}},  # 无效
        ]
        existing = [RuleCreate(**make_rule(name="已有", action_value=0.8))]
        importer = RuleImporter(existing_rules=existing)
        result = importer.preview(rules)
        assert result.total == 3
        assert result.valid_count == 2
        assert result.error_count == 1


class TestRuleImporterExecute:
    """测试 RuleImporter.execute() — 完整导入流程"""

    def test_execute_creates_rules(self):
        """execute 应该创建所有合法规则"""
        from sqlalchemy.orm import sessionmaker
        from app.database import engine
        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            importer = RuleImporter(existing_rules=[])
            rules = [
                make_rule(name="规则A"),
                make_rule(name="规则B"),
            ]
            result = importer.execute(db, rules)
            assert result.created_count == 2
            assert result.skipped_conflicts == 0
            assert result.skipped_errors == 0
        finally:
            db.close()

    def test_execute_skips_conflicts(self):
        """execute 应该跳过有冲突的规则"""
        from sqlalchemy.orm import sessionmaker
        from app.database import engine
        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            # 先创建一条规则
            existing = RuleCreate(**make_rule(name="已有规则", action_value=0.8))
            crud = RuleCRUD(db)
            crud.create(existing)

            importer = RuleImporter(existing_rules=crud.list_all())
            # 同条件不同动作 → 冲突
            conflicting = make_rule(name="冲突规则", action_value=0.9)
            result = importer.execute(db, [conflicting])
            assert result.created_count == 0
            assert result.skipped_conflicts == 1
        finally:
            db.close()

    def test_execute_skips_invalid(self):
        """execute 应该跳过非法规则"""
        from sqlalchemy.orm import sessionmaker
        from app.database import engine
        Session = sessionmaker(bind=engine)
        db = Session()
        try:
            importer = RuleImporter(existing_rules=[])
            rules = [
                make_rule(name="合法规则"),
                {"name": "", "rule_type": "data_cleaning", "condition": {}, "action": {}},
            ]
            result = importer.execute(db, rules)
            assert result.created_count == 1
            assert result.skipped_errors == 1
        finally:
            db.close()
