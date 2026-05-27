"""应用配置"""
import os
from dotenv import load_dotenv

load_dotenv()

# 数据库
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agent_aps.db")

# LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.longcat.chat/openai")
LLM_MODEL = os.getenv("LLM_MODEL", "LongCat-2.0-Preview")

# Admin
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "change-me-in-production")
ADMIN_DEFAULT_USERNAME = os.getenv("ADMIN_DEFAULT_USERNAME", "admin")
ADMIN_DEFAULT_PASSWORD = os.getenv("ADMIN_DEFAULT_PASSWORD", "admin123")

# JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
