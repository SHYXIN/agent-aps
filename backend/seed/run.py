"""运行所有种子数据填充

用法:
    python -m seed.run
"""
from app.database import Base, engine
from seed.users import seed_users
from seed.rules import seed_rules


def main():
    print("=" * 50)
    print("Agent APS 数据填充")
    print("=" * 50)

    # 确保表已创建
    Base.metadata.create_all(bind=engine)
    print("[Seed] 数据库表已就绪")

    # 填充用户
    seed_users()

    # 填充规则
    seed_rules()

    print("=" * 50)
    print("数据填充完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
