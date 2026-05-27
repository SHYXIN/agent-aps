"""规则批量导入"""
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.schemas.rule import RuleCreate
from app.services.conflict import ConflictDetector
from app.services.crud import RuleCRUD
from app.services.changelog import ChangelogStore


@dataclass
class ImportResult:
    total: int = 0
    valid_count: int = 0
    error_count: int = 0
    conflict_count: int = 0
    created_count: int = 0
    skipped_conflicts: int = 0
    skipped_errors: int = 0
    valid_rules: list[RuleCreate] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)


class RuleImporter:
    def __init__(self, existing_rules: list):
        self.existing_rules = existing_rules

    def preview(self, raw_rules: list[dict]) -> ImportResult:
        """预览导入结果（不写入数据库）"""
        result = ImportResult(total=len(raw_rules))
        detector = ConflictDetector(self.existing_rules)

        for i, raw in enumerate(raw_rules):
            try:
                rule = RuleCreate(**raw)
            except Exception as e:
                result.error_count += 1
                result.errors.append({"index": i, "name": raw.get("name", ""), "error": str(e)})
                continue

            conflicts = detector.check(rule)
            if conflicts:
                result.conflict_count += 1
                result.conflicts.append({
                    "index": i,
                    "name": rule.name,
                    "conflicts": conflicts,
                })

            result.valid_count += 1
            result.valid_rules.append(rule)

        return result

    def execute(self, db: Session, raw_rules: list[dict]) -> ImportResult:
        """执行导入：校验 + 冲突检测 + 写入数据库"""
        crud = RuleCRUD(db)
        result = self.preview(raw_rules)
        result.skipped_errors = result.error_count

        for rule in result.valid_rules:
            # 跳过有冲突的
            detector = ConflictDetector(crud.list_all())
            if detector.check(rule):
                result.skipped_conflicts += 1
                continue
            created = crud.create(rule)
            ChangelogStore(db).log(
                rule_id=created.id,
                action="create",
                after_value={"name": created.name, "source": "import"},
            )
            result.created_count += 1

        return result
