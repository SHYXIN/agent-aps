"""用户种子数据"""
from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models.user import User, UserRole
from app.core.security import hash_password


def seed_users():
    """创建初始用户"""
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        # 检查是否已有用户
        if db.query(User).count() > 0:
            print("[Seed] 用户数据已存在，跳过")
            return

        users = [
            User(
                username="admin",
                email="admin@agent-aps.local",
                password_hash=hash_password("admin123"),
                role=UserRole.ADMIN.value,
                is_active=True,
            ),
            User(
                username="operator",
                email="operator@agent-aps.local",
                password_hash=hash_password("operator123"),
                role=UserRole.USER.value,
                is_active=True,
            ),
        ]
        db.add_all(users)
        db.commit()
        print(f"[Seed] 已创建 {len(users)} 个用户")
    finally:
        db.close()
