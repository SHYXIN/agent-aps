"""Rule CRUD 操作测试"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.crud import RuleCRUD
from app.schemas import RuleCreate


@pytest.fixture
def db_session():
    """每个测试用独立的内存数据库"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def crud(db_session):
    return RuleCRUD(db_session)


@pytest.fixture
def sample_rule():
    return RuleCreate(
        name="含硼钢炉容折扣",
        description="含硼钢种的炉容容量按80%计算",
        rule_type="data_cleaning",
        condition={"field": "steel_grade", "operator": "contains", "value": "B"},
        action={"field": "furnace_capacity", "operator": "multiply", "value": 0.8},
    )


class TestRuleCRUD:
    def test_create_rule(self, crud, sample_rule):
        """创建规则后应返回带 id 的规则对象"""
        result = crud.create(sample_rule)
        assert result.id is not None
        assert result.name == "含硼钢炉容折扣"
        assert result.rule_type == "data_cleaning"

    def test_get_rule_by_id(self, crud, sample_rule):
        """根据 id 查询规则"""
        created = crud.create(sample_rule)
        result = crud.get_by_id(created.id)
        assert result is not None
        assert result.name == "含硼钢炉容折扣"

    def test_get_nonexistent_rule_returns_none(self, crud):
        """查询不存在的规则返回 None"""
        result = crud.get_by_id(999)
        assert result is None

    def test_list_rules(self, crud, sample_rule):
        """列出所有规则"""
        crud.create(sample_rule)
        crud.create(RuleCreate(
            name="另一条规则",
            rule_type="scheduling",
            condition={"field": "x", "operator": "eq", "value": 1},
            action={"field": "y", "operator": "set", "value": 2},
        ))
        results = crud.list_all()
        assert len(results) == 2

    def test_list_rules_filter_by_type(self, crud, sample_rule):
        """按类型筛选规则"""
        crud.create(sample_rule)
        crud.create(RuleCreate(
            name="排程规则",
            rule_type="scheduling",
            condition={"field": "x", "operator": "eq", "value": 1},
            action={"field": "y", "operator": "set", "value": 2},
        ))
        results = crud.list_all(rule_type="data_cleaning")
        assert len(results) == 1
        assert results[0].rule_type == "data_cleaning"

    def test_list_rules_filter_by_status(self, crud, sample_rule):
        """按状态筛选规则"""
        created = crud.create(sample_rule)
        crud.update(created.id, {"status": "disabled"})
        crud.create(RuleCreate(
            name="启用的规则",
            rule_type="data_cleaning",
            condition={"field": "x", "operator": "eq", "value": 1},
            action={"field": "y", "operator": "set", "value": 2},
        ))
        results = crud.list_all(status="active")
        assert len(results) == 1

    def test_update_rule(self, crud, sample_rule):
        """更新规则的字段"""
        created = crud.create(sample_rule)
        updated = crud.update(created.id, {"name": "新名称", "status": "disabled"})
        assert updated.name == "新名称"
        assert updated.status == "disabled"

    def test_update_nonexistent_rule_returns_none(self, crud):
        """更新不存在的规则返回 None"""
        result = crud.update(999, {"name": "x"})
        assert result is None

    def test_delete_rule(self, crud, sample_rule):
        """删除规则"""
        created = crud.create(sample_rule)
        assert crud.delete(created.id) is True
        assert crud.get_by_id(created.id) is None

    def test_delete_nonexistent_rule_returns_false(self, crud):
        """删除不存在的规则返回 False"""
        assert crud.delete(999) is False

    def test_create_rule_with_free_text(self, crud):
        """创建带 free_text 的规则"""
        rule = RuleCreate(
            name="经验温度调整",
            rule_type="data_cleaning",
            condition={"field": "steel_grade", "operator": "contains", "value": "B"},
            action={"field": "temperature", "operator": "add", "value": 20},
            free_text="经验上1号炉出钢温度要比标准高20度",
        )
        result = crud.create(rule)
        assert result.free_text == "经验上1号炉出钢温度要比标准高20度"
