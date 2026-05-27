"""Starlette-Admin 管理面板配置"""
import os
from starlette_admin.contrib.sqla import Admin
from starlette_admin import I18nConfig
from app.admin.views import DashboardView, RuleModelView, UserModelView
from app.admin.auth import AdminAuthProvider
from app.database import engine
from app.models import Rule
from app.models.user import User


def create_admin(app):
    """创建并配置 starlette-admin，挂载到 FastAPI app"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)

    admin = Admin(
        engine=engine,
        title="Agent APS 管理后台",
        base_url="/admin",
        route_name="admin",
        templates_dir=templates_dir,
        index_view=DashboardView(),
        auth_provider=AdminAuthProvider(),
        i18n_config=I18nConfig(default_locale="en"),
    )

    admin.add_view(RuleModelView(Rule))
    admin.add_view(UserModelView(User))

    admin.mount_to(app)
    return admin
