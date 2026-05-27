"""变更日志模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ChangelogEntry(Base):
    __tablename__ = "changelog"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False)
    before_value = Column(Text, nullable=True)
    after_value = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
