"""Starlette-Admin 视图定义"""
from typing import Any, List
import csv
import io

from starlette.requests import Request
from starlette.responses import Response
from starlette_admin import CustomView, action
from starlette_admin.contrib.sqla import ModelView
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import engine
from app.models.user import User
from app.models import Rule


class DashboardView(CustomView):
    """管理后台首页仪表盘"""

    def __init__(self):
        super().__init__(
            label="仪表盘",
            icon="fa fa-dashboard",
            path="/",
            template_path="dashboard.html",
            add_to_menu=True,
        )

    async def render(self, request: Request, templates) -> Response:
        session: Session = request.state.session
        stats = {
            "rule_count": session.query(func.count(Rule.id)).scalar(),
            "active_rule_count": session.query(func.count(Rule.id)).filter(Rule.status == "active").scalar(),
            "user_count": session.query(func.count(User.id)).scalar(),
        }
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={"title": "仪表盘", "stats": stats},
        )


class RuleModelView(ModelView):
    """规则管理视图"""
    label = "规则管理"
    icon = "fa fa-list"

    fields = [
        Rule.id, Rule.name, Rule.description, Rule.rule_type,
        Rule.condition_json, Rule.action_json, Rule.free_text,
        Rule.status, Rule.source, Rule.notes, Rule.created_at,
    ]
    search_fields = [Rule.name, Rule.description]
    exclude_fields_from_create = ["source"]
    exclude_fields_from_edit = ["source"]
    actions = ["delete", "toggle_status", "export_csv"]

    @action(
        name="toggle_status",
        text="切换状态",
        confirmation="确定要切换选中规则的状态吗？",
        submit_btn_text="确定",
        submit_btn_class="btn-warning",
        icon_class="fa fa-toggle-on",
    )
    async def toggle_status_action(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        rules = session.query(Rule).filter(Rule.id.in_(pks)).all()
        count = 0
        for r in rules:
            r.status = "disabled" if r.status == "active" else "active"
            count += 1
        session.commit()
        return f"已切换 {count} 条规则的状态"

    @action(
        name="export_csv",
        text="导出 CSV",
        confirmation="确定要导出选中的数据吗？",
        submit_btn_text="导出",
        submit_btn_class="btn-success",
        icon_class="fa fa-download",
        custom_response=True,
    )
    async def export_csv_action(self, request: Request, pks: List[Any]) -> Response:
        session: Session = request.state.session
        items = session.query(Rule).filter(Rule.id.in_(pks)).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "名称", "类型", "状态", "创建时间"])
        for item in items:
            writer.writerow([item.id, item.name, item.rule_type, item.status, item.created_at])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=rules_export.csv"},
        )


class UserModelView(ModelView):
    """用户管理视图"""
    label = "用户管理"
    icon = "fa fa-users"

    fields = [
        User.id, User.username, User.email, User.role,
        User.is_active, User.created_at,
    ]
    search_fields = [User.username, User.email]
    exclude_fields_from_create = ["password_hash"]
    exclude_fields_from_edit = ["password_hash"]
    actions = ["delete", "toggle_active"]

    @action(
        name="toggle_active",
        text="切换激活状态",
        confirmation="确定要切换选中用户的激活状态吗？",
        submit_btn_text="确定",
        submit_btn_class="btn-warning",
        icon_class="fa fa-toggle-on",
    )
    async def toggle_active_action(self, request: Request, pks: List[Any]) -> str:
        session: Session = request.state.session
        users = session.query(User).filter(User.id.in_(pks)).all()
        count = 0
        for user in users:
            user.is_active = not user.is_active
            count += 1
        session.commit()
        return f"已切换 {count} 个用户的激活状态"
