"""规则变更日志"""
import json
from sqlalchemy.orm import Session

from app.models.changelog import ChangelogEntry


class ChangelogStore:
    def __init__(self, db: Session):
        self.db = db

    def log(self, rule_id: int, action: str,
            before_value: dict | None = None,
            after_value: dict | None = None) -> ChangelogEntry:
        entry = ChangelogEntry(
            rule_id=rule_id,
            action=action,
            before_value=json.dumps(before_value, ensure_ascii=False) if before_value else None,
            after_value=json.dumps(after_value, ensure_ascii=False) if after_value else None,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_by_rule(self, rule_id: int) -> list[dict]:
        entries = (
            self.db.query(ChangelogEntry)
            .filter(ChangelogEntry.rule_id == rule_id)
            .order_by(ChangelogEntry.created_at.desc(), ChangelogEntry.id.desc())
            .all()
        )
        return [self._to_dict(e) for e in entries]

    def list_all(self) -> list[dict]:
        entries = (
            self.db.query(ChangelogEntry)
            .order_by(ChangelogEntry.created_at.desc(), ChangelogEntry.id.desc())
            .all()
        )
        return [self._to_dict(e) for e in entries]

    def _to_dict(self, entry: ChangelogEntry) -> dict:
        return {
            "id": entry.id,
            "rule_id": entry.rule_id,
            "action": entry.action,
            "before_value": json.loads(entry.before_value) if entry.before_value else None,
            "after_value": json.loads(entry.after_value) if entry.after_value else None,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }
