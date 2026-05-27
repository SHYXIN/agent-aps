"""认证路由：登录 / 登出 / 当前用户"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.security import verify_password, create_token, verify_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """从 JWT token 获取当前用户"""
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def register_auth_routes(app):
    """注册认证路由"""

    @app.post("/api/auth/login")
    def login(data: dict, db: Session = Depends(get_db)):
        username = data.get("username", "")
        password = data.get("password", "")
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="账号已被禁用")
        token = create_token(user.id, user.username, user.role)
        return {
            "token": token,
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
        }

    @app.get("/api/auth/me")
    def me(user: User = Depends(get_current_user)):
        return {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
        }

    @app.post("/api/auth/logout")
    def logout():
        return {"ok": True}
