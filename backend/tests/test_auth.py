"""认证 API 测试"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.core.security import hash_password, create_token, verify_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_user(db_session):
    """获取已存在的管理员用户（seed 创建）"""
    user = db_session.query(User).filter(User.username == "admin").first()
    if not user:
        user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def normal_user(db_session):
    """获取普通用户（seed 创建）"""
    user = db_session.query(User).filter(User.username == "operator").first()
    if not user:
        user = User(
            username="operator",
            password_hash=hash_password("operator123"),
            role="user",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


class TestLogin:
    def test_login_success(self, client, admin_user):
        """管理员登录成功返回 token"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["username"] == "admin"
        assert data["role"] == "admin"
        # 验证 token 有效
        payload = verify_token(data["token"])
        assert payload is not None
        assert payload["user_id"] == admin_user.id

    def test_login_wrong_password(self, client, admin_user):
        """密码错误返回 401"""
        response = client.post("/api/auth/login", json={
            "username": "admin",
            "password": "wrong",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client, admin_user):
        """用户不存在返回 401"""
        response = client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "pass",
        })
        assert response.status_code == 401

    def test_login_inactive_user(self, client, admin_user, db_session):
        """被禁用的用户无法登录"""
        user = User(
            username="banned",
            password_hash=hash_password("pass123"),
            role="user",
            is_active=False,
        )
        db_session.add(user)
        db_session.commit()

        response = client.post("/api/auth/login", json={
            "username": "banned",
            "password": "pass123",
        })
        assert response.status_code == 403


class TestAuthMe:
    def test_me_with_valid_token(self, client, admin_user):
        """有效 token 返回当前用户信息"""
        token = create_token(admin_user.id, admin_user.username, admin_user.role)
        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    def test_me_without_token(self, client):
        """无 token 返回 401"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_token(self, client):
        """无效 token 返回 401"""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid.token"
        })
        assert response.status_code == 401


class TestLogout:
    def test_logout_clears_cookie(self, client, admin_user):
        """登出清除 cookie"""
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        # 检查 cookie 被清除
        cookies = response.cookies
        assert "access_token" not in cookies or cookies.get("access_token") == ""
