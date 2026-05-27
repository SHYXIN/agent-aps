"""路由注册入口"""
from app.api.routes.rules import register_rule_routes
from app.api.routes.import_ import register_import_routes
from app.api.routes.agent import register_agent_routes


def register_routes(app):
    """注册所有 API 路由"""
    register_rule_routes(app)
    register_import_routes(app)
    register_agent_routes(app)
