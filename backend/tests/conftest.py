"""共享测试 fixtures"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Rule  # noqa: F401 — 注册模型
from app.models.changelog import ChangelogEntry  # noqa: F401 — 注册模型


@pytest.fixture(scope="session")
def engine():
    """全局共享内存数据库引擎"""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(autouse=True)
def setup_db(engine):
    """每个测试前建表，测试后删表"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine):
    """提供独立的数据库 session"""
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
