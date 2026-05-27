"""Rule API 端点测试"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db, Base
from app.models.changelog import ChangelogEntry  # noqa: F401 — 注册模型
from app.main import app


# API 测试需要自己的 engine（因为 TestClient 在另一个线程）
@pytest.fixture
def api_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_db(api_engine):
    """用测试数据库覆盖 get_db 依赖"""
    Session = sessionmaker(bind=api_engine)
    def _get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


SAMPLE_RULE = {
    "name": "含硼钢炉容折扣",
    "description": "含硼钢种的炉容容量按80%计算",
    "rule_type": "data_cleaning",
    "condition": {"field": "steel_grade", "operator": "contains", "value": "B"},
    "action": {"field": "furnace_capacity", "operator": "multiply", "value": 0.8},
}


class TestRuleCRUD:
    def test_create_rule(self, client):
        response = client.post("/api/rules", json=SAMPLE_RULE)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "含硼钢炉容折扣"
        assert data["id"] is not None

    def test_create_rule_invalid_type(self, client):
        bad_rule = {**SAMPLE_RULE, "rule_type": "invalid"}
        response = client.post("/api/rules", json=bad_rule)
        assert response.status_code == 422

    def test_list_rules(self, client):
        client.post("/api/rules", json=SAMPLE_RULE)
        response = client.get("/api/rules")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_rules_filter_by_type(self, client):
        client.post("/api/rules", json=SAMPLE_RULE)
        client.post("/api/rules", json={**SAMPLE_RULE, "name": "排程规则", "rule_type": "scheduling"})
        response = client.get("/api/rules", params={"rule_type": "data_cleaning"})
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_rule_by_id(self, client):
        create_resp = client.post("/api/rules", json=SAMPLE_RULE)
        rule_id = create_resp.json()["id"]
        response = client.get(f"/api/rules/{rule_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "含硼钢炉容折扣"

    def test_get_nonexistent_rule(self, client):
        response = client.get("/api/rules/999")
        assert response.status_code == 404

    def test_update_rule(self, client):
        create_resp = client.post("/api/rules", json=SAMPLE_RULE)
        rule_id = create_resp.json()["id"]
        response = client.put(f"/api/rules/{rule_id}", json={"name": "新名称"})
        assert response.status_code == 200
        assert response.json()["name"] == "新名称"

    def test_update_rule_empty_body(self, client):
        create_resp = client.post("/api/rules", json=SAMPLE_RULE)
        rule_id = create_resp.json()["id"]
        response = client.put(f"/api/rules/{rule_id}", json={})
        assert response.status_code == 400

    def test_delete_rule(self, client):
        create_resp = client.post("/api/rules", json=SAMPLE_RULE)
        rule_id = create_resp.json()["id"]
        response = client.delete(f"/api/rules/{rule_id}")
        assert response.status_code == 200
        response = client.get(f"/api/rules/{rule_id}")
        assert response.status_code == 404

    def test_create_rule_with_notes(self, client):
        rule = {**SAMPLE_RULE, "notes": "客户张三要求"}
        response = client.post("/api/rules", json=rule)
        assert response.status_code == 201
        assert response.json()["notes"] == "客户张三要求"


class TestConflictCheck:
    def test_conflict_check_no_conflict(self, client):
        response = client.post("/api/rules/conflict-check", json=SAMPLE_RULE)
        assert response.status_code == 200
        assert response.json()["has_conflict"] is False

    def test_conflict_check_with_conflict(self, client):
        client.post("/api/rules", json=SAMPLE_RULE)
        conflicting = {**SAMPLE_RULE, "name": "冲突规则",
                       "action": {"field": "furnace_capacity", "operator": "multiply", "value": 0.9}}
        response = client.post("/api/rules/conflict-check", json=conflicting)
        assert response.status_code == 200
        assert response.json()["has_conflict"] is True
        assert len(response.json()["conflicts"]) == 1

    def test_create_rule_with_conflict_returns_conflict_info(self, client):
        client.post("/api/rules", json=SAMPLE_RULE)
        conflicting = {**SAMPLE_RULE, "name": "冲突规则",
                       "action": {"field": "furnace_capacity", "operator": "multiply", "value": 0.9}}
        response = client.post("/api/rules", json=conflicting)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "conflict"

    def test_force_create_rule(self, client):
        client.post("/api/rules", json=SAMPLE_RULE)
        conflicting = {**SAMPLE_RULE, "name": "冲突规则",
                       "action": {"field": "furnace_capacity", "operator": "multiply", "value": 0.9}}
        response = client.post("/api/rules/force", json=conflicting)
        assert response.status_code == 201
        assert response.json()["name"] == "冲突规则"


class TestChangelog:
    def test_changelog_on_create(self, client):
        resp = client.post("/api/rules", json=SAMPLE_RULE)
        rule_id = resp.json()["id"]
        response = client.get(f"/api/rules/{rule_id}/changelog")
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) == 1
        assert logs[0]["action"] == "create"

    def test_changelog_on_update(self, client):
        resp = client.post("/api/rules", json=SAMPLE_RULE)
        rule_id = resp.json()["id"]
        client.put(f"/api/rules/{rule_id}", json={"name": "新名称"})
        response = client.get(f"/api/rules/{rule_id}/changelog")
        logs = response.json()
        assert len(logs) == 2
        assert logs[0]["action"] == "update"

    def test_changelog_on_delete(self, client):
        resp = client.post("/api/rules", json=SAMPLE_RULE)
        rule_id = resp.json()["id"]
        client.delete(f"/api/rules/{rule_id}")
        response = client.get(f"/api/rules/{rule_id}/changelog")
        logs = response.json()
        assert len(logs) == 2
        assert logs[0]["action"] == "delete"

    def test_all_changelog(self, client):
        r1 = client.post("/api/rules", json=SAMPLE_RULE).json()
        client.post("/api/rules/force", json={**SAMPLE_RULE, "name": "规则B"}).json()
        client.put(f"/api/rules/{r1['id']}", json={"name": "改了"})
        response = client.get("/api/changelog")
        assert response.status_code == 200
        assert len(response.json()) == 3
