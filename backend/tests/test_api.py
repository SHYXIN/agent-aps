"""Rule API 端点测试"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.models import Rule  # noqa: F401 — 确保模型注册到 Base
from app.main import app

engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# 禁用 startup 事件（它会用默认 engine 建表）
app.router.on_startup.clear()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

SAMPLE_RULE = {
    "name": "含硼钢炉容折扣",
    "description": "含硼钢种的炉容容量按80%计算",
    "rule_type": "data_cleaning",
    "condition": {"field": "steel_grade", "operator": "contains", "value": "B"},
    "action": {"field": "furnace_capacity", "operator": "multiply", "value": 0.8},
}


class TestRuleAPI:
    def test_create_rule(self):
        """POST /api/rules 创建规则"""
        response = client.post("/api/rules", json=SAMPLE_RULE)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "含硼钢炉容折扣"
        assert data["id"] is not None

    def test_create_rule_invalid_type(self):
        """POST /api/rules 无效 rule_type 返回 422"""
        bad_rule = {**SAMPLE_RULE, "rule_type": "invalid"}
        response = client.post("/api/rules", json=bad_rule)
        assert response.status_code == 422

    def test_list_rules(self):
        """GET /api/rules 列出规则"""
        client.post("/api/rules", json=SAMPLE_RULE)
        response = client.get("/api/rules")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_rules_filter_by_type(self):
        """GET /api/rules?rule_type=data_cleaning 按类型筛选"""
        client.post("/api/rules", json=SAMPLE_RULE)
        client.post("/api/rules", json={
            **SAMPLE_RULE,
            "name": "排程规则",
            "rule_type": "scheduling",
        })
        response = client.get("/api/rules", params={"rule_type": "data_cleaning"})
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_rule_by_id(self):
        """GET /api/rules/{id} 查询单条规则"""
        create_resp = client.post("/api/rules", json=SAMPLE_RULE)
        rule_id = create_resp.json()["id"]
        response = client.get(f"/api/rules/{rule_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "含硼钢炉容折扣"

    def test_get_nonexistent_rule(self):
        """GET /api/rules/999 不存在返回 404"""
        response = client.get("/api/rules/999")
        assert response.status_code == 404

    def test_update_rule(self):
        """PUT /api/rules/{id} 更新规则"""
        create_resp = client.post("/api/rules", json=SAMPLE_RULE)
        rule_id = create_resp.json()["id"]
        response = client.put(f"/api/rules/{rule_id}", json={"name": "新名称"})
        assert response.status_code == 200
        assert response.json()["name"] == "新名称"

    def test_delete_rule(self):
        """DELETE /api/rules/{id} 删除规则"""
        create_resp = client.post("/api/rules", json=SAMPLE_RULE)
        rule_id = create_resp.json()["id"]
        response = client.delete(f"/api/rules/{rule_id}")
        assert response.status_code == 200
        response = client.get(f"/api/rules/{rule_id}")
        assert response.status_code == 404

    def test_create_rule_with_notes(self):
        """POST /api/rules 创建带 notes 的规则"""
        rule = {**SAMPLE_RULE, "notes": "客户张三要求"}
        response = client.post("/api/rules", json=rule)
        assert response.status_code == 201
        assert response.json()["notes"] == "客户张三要求"
