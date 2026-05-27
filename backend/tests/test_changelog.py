"""规则变更日志测试"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Rule
from app.services.changelog import ChangelogStore


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def store(db_session):
    return ChangelogStore(db_session)


class TestChangelog:
    def test_log_create(self, store, db_session):
        """记录规则创建操作"""
        store.log(rule_id=1, action="create", after_value={"name": "规则A"})
        logs = store.list_by_rule(1)
        assert len(logs) == 1
        assert logs[0]["action"] == "create"

    def test_log_update(self, store, db_session):
        """记录规则修改操作"""
        store.log(rule_id=1, action="update",
                  before_value={"name": "旧名称"},
                  after_value={"name": "新名称"})
        logs = store.list_by_rule(1)
        assert len(logs) == 1
        assert logs[0]["action"] == "update"
        assert logs[0]["before_value"]["name"] == "旧名称"
        assert logs[0]["after_value"]["name"] == "新名称"

    def test_log_delete(self, store, db_session):
        """记录规则删除操作"""
        store.log(rule_id=1, action="delete", before_value={"name": "规则A"})
        logs = store.list_by_rule(1)
        assert len(logs) == 1
        assert logs[0]["action"] == "delete"

    def test_list_all_logs(self, store, db_session):
        """查询全部变更日志"""
        store.log(rule_id=1, action="create", after_value={"name": "规则A"})
        store.log(rule_id=2, action="create", after_value={"name": "规则B"})
        store.log(rule_id=1, action="update",
                  before_value={"name": "规则A"},
                  after_value={"name": "规则A-改"})
        logs = store.list_all()
        assert len(logs) == 3

    def test_list_by_rule(self, store, db_session):
        """按规则 ID 查询变更日志"""
        store.log(rule_id=1, action="create", after_value={"name": "规则A"})
        store.log(rule_id=2, action="create", after_value={"name": "规则B"})
        store.log(rule_id=1, action="update",
                  before_value={"name": "规则A"},
                  after_value={"name": "规则A-改"})
        logs = store.list_by_rule(1)
        assert len(logs) == 2

    def test_log_order_newest_first(self, store, db_session):
        """变更日志按时间倒序排列"""
        store.log(rule_id=1, action="create", after_value={"name": "v1"})
        store.log(rule_id=1, action="update",
                  before_value={"name": "v1"},
                  after_value={"name": "v2"})
        store.log(rule_id=1, action="update",
                  before_value={"name": "v2"},
                  after_value={"name": "v3"})
        logs = store.list_by_rule(1)
        assert len(logs) == 3
        # 最新一条是最后一次写入
        assert logs[0]["after_value"]["name"] == "v3"
