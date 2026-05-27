"""安全工具测试"""
import pytest
from app.core.security import hash_password, verify_password, create_token, verify_token


class TestPassword:
    def test_hash_and_verify(self):
        """密码哈希后应该能正确验证"""
        hashed = hash_password("admin123")
        assert verify_password("admin123", hashed) is True

    def test_wrong_password_fails(self):
        """错误密码应该验证失败"""
        hashed = hash_password("admin123")
        assert verify_password("wrong", hashed) is False

    def test_different_hashes_for_same_password(self):
        """相同密码的哈希值应该不同（salt）"""
        h1 = hash_password("admin123")
        h2 = hash_password("admin123")
        assert h1 != h2


class TestJWT:
    def test_create_and_verify_token(self):
        """创建的 token 应该能正确验证"""
        token = create_token(user_id=1, username="admin", role="admin")
        payload = verify_token(token)
        assert payload["user_id"] == 1
        assert payload["username"] == "admin"
        assert payload["role"] == "admin"

    def test_invalid_token_fails(self):
        """无效 token 应该返回 None"""
        assert verify_token("invalid.token.here") is None

    def test_tampered_token_fails(self):
        """篡改的 token 应该返回 None"""
        token = create_token(user_id=1, username="admin", role="admin")
        # 篡改 payload
        parts = token.split(".")
        parts[1] = "tampered"
        assert verify_token(".".join(parts)) is None
