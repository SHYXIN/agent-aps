"""Starlette-Admin 认证提供者"""
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models.user import User
from app.core.security import verify_password


class AdminAuthProvider(AuthProvider):
    """Session-based 认证，仅允许管理员登录"""

    def __init__(self):
        super().__init__()
        self.SessionLocal = sessionmaker(bind=engine)

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        db = self.SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user or not verify_password(password, user.password_hash):
                raise ValueError("用户名或密码错误")
            if user.role != "admin":
                raise ValueError("仅管理员可登录后台")
            request.session["admin_user_id"] = user.id
            request.session["admin_username"] = user.username
            return response
        finally:
            db.close()

    async def is_authenticated(self, request: Request) -> bool:
        user_id = request.session.get("admin_user_id")
        if not user_id:
            return False
        db = self.SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user is not None and user.role == "admin"
        finally:
            db.close()

    def get_admin_config(self, request: Request) -> AdminConfig:
        username = request.session.get("admin_username", "Admin")
        return AdminConfig(app_title=f"Agent APS — {username}")

    def get_admin_user(self, request: Request) -> AdminUser:
        username = request.session.get("admin_username", "Admin")
        return AdminUser(username=username)

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response
