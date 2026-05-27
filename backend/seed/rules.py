"""规则种子数据"""
import json
from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.models import Rule


def seed_rules():
    """创建示例规则"""
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        if db.query(Rule).count() > 0:
            print("[Seed] 规则数据已存在，跳过")
            return

        rules = [
            # ── 数据清洗规则（Rule A）──
            Rule(
                name="含硼钢炉容折扣",
                description="含硼钢种的炉容容量按80%计算",
                rule_type="data_cleaning",
                condition_json=json.dumps({"field": "steel_grade", "operator": "contains", "value": "B"}),
                action_json=json.dumps({"field": "furnace_capacity", "operator": "multiply", "value": 0.8}),
                status="active",
                source="seed",
            ),
            Rule(
                name="含钛钢温度补偿",
                description="含钛钢种出钢温度需额外加15度",
                rule_type="data_cleaning",
                condition_json=json.dumps({"field": "steel_grade", "operator": "contains", "value": "Ti"}),
                action_json=json.dumps({"field": "temperature", "operator": "add", "value": 15}),
                status="active",
                source="seed",
            ),
            Rule(
                name="炉容上限修正",
                description="1号炉实际炉容比标称值低5%",
                rule_type="data_cleaning",
                condition_json=json.dumps({"field": "furnace_id", "operator": "eq", "value": "1"}),
                action_json=json.dumps({"field": "furnace_capacity", "operator": "multiply", "value": 0.95}),
                status="active",
                source="seed",
            ),
            Rule(
                name="新炉台经验值填充",
                description="未满月的炉台使用历史平均值填充",
                rule_type="data_cleaning",
                condition_json=json.dumps({"field": "furnace_age_days", "operator": "lt", "value": 30}),
                action_json=json.dumps({"field": "use_experience_value", "operator": "set", "value": True}),
                free_text="经验上新建炉台前30天数据不可靠，用历史均值平滑",
                status="active",
                source="seed",
            ),
            # ── 排程业务规则（Rule B）──
            Rule(
                name="Q345与Q235不兼容",
                description="Q345和Q235不能连续浇铸",
                rule_type="scheduling",
                condition_json=json.dumps({"field": "steel_grade_pair", "operator": "incompatible", "value": ["Q345", "Q235"]}),
                action_json=json.dumps({"field": "casting_sequence", "operator": "block"}),
                status="active",
                source="seed",
            ),
            Rule(
                name="宽度过渡限制",
                description="相邻浇次宽度差不能超过200mm",
                rule_type="scheduling",
                condition_json=json.dumps({"field": "width_diff", "operator": "gt", "value": 200}),
                action_json=json.dumps({"field": "casting_sequence", "operator": "block"}),
                status="active",
                source="seed",
            ),
            Rule(
                name="VIP客户优先",
                description="VIP客户订单延迟惩罚权重翻倍",
                rule_type="scheduling",
                condition_json=json.dumps({"field": "customer_level", "operator": "eq", "value": "VIP"}),
                action_json=json.dumps({"field": "delay_penalty_weight", "operator": "multiply", "value": 2}),
                status="active",
                source="seed",
            ),
            Rule(
                name="1号连铸机周二检修",
                description="每周二下午1号连铸机停机检修",
                rule_type="scheduling",
                condition_json=json.dumps({"field": "day_of_week", "operator": "eq", "value": "2"}),
                action_json=json.dumps({"field": "caster_1_available", "operator": "set", "value": False}),
                status="active",
                source="seed",
            ),
            Rule(
                name="高碳钢连续浇铸上限",
                description="高碳钢连续浇铸不超过5炉",
                rule_type="scheduling",
                condition_json=json.dumps({"field": "steel_type", "operator": "eq", "value": "high_carbon"}),
                action_json=json.dumps({"field": "max_consecutive_heats", "operator": "set", "value": 5}),
                status="active",
                source="seed",
            ),
        ]
        db.add_all(rules)
        db.commit()
        print(f"[Seed] 已创建 {len(rules)} 条规则")
    finally:
        db.close()
