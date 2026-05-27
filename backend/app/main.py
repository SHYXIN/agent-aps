"""FastAPI 应用入口"""
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.database import engine, Base as DBase
from app.models.user import User  # noqa: F401 — 注册模型
from app.core.config import ADMIN_SECRET_KEY, ADMIN_DEFAULT_USERNAME, ADMIN_DEFAULT_PASSWORD
from app.core.security import hash_password

app = FastAPI(title="Agent APS Rule Manager", on_startup=[])

# Session 中间件（Admin 认证依赖）
app.add_middleware(
    SessionMiddleware,
    secret_key=ADMIN_SECRET_KEY,
    session_cookie="admin_session",
    max_age=3600,
)


def _create_default_admin():
    """首次启动时创建默认管理员账号"""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == ADMIN_DEFAULT_USERNAME).first()
        if not existing:
            admin = User(
                username=ADMIN_DEFAULT_USERNAME,
                password_hash=hash_password(ADMIN_DEFAULT_PASSWORD),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"[Admin] 默认管理员已创建: {ADMIN_DEFAULT_USERNAME} / {ADMIN_DEFAULT_PASSWORD}")
    finally:
        db.close()


_create_default_admin()

# 注册 API 路由
from app.api.routes import register_routes
register_routes(app)

# 挂载 Starlette-Admin 管理后台
from app.admin import create_admin

admin = create_admin(app)
