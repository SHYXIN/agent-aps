# Handoff: Agent APS 规则管理 MVP

**日期：** 2026-05-27
**仓库：** https://github.com/SHYXIN/agent-aps
**项目路径：** D:\ai-research\agent-aps

---

## 1. 产品背景

基于 LLM Agent 的工业排程规则管理系统。MVP 阶段只做规则管理（不做排程求解、甘特图、数据适配）。

**核心用户场景：** 钢铁企业计划员通过自然语言与 Agent 对话，Agent 将业务规则翻译为结构化 JSON，写入规则库，支持冲突检测和用户确认。

**关键产品决策（grill-me 讨论确认）：**
- 先做钢铁行业，再做通用平台
- 规则分两类：Rule A（数据清洗）+ Rule B（排程业务约束），95% 可结构化
- Agent 只翻译，不猜测——模糊信息必须反问用户
- 用户确认是最终校验
- 冲突检测：程序检测直接矛盾，模糊冲突交给用户决策
- LLM 选型：国产大模型 API（DeepSeek/千问/GLM），数据不出境
- 排程规模：大型（几百炉次），需要 ALNS 等启发式算法（MVP 不做）
- 批量排程，允许等待，不需要增量求解

---

## 2. 已完成的工作

### 2.1 项目初始化
- GitHub 仓库创建：https://github.com/SHYXIN/agent-aps
- Agent skills 配置（CLAUDE.md + docs/agents/）
- GitHub Labels 创建：needs-triage / needs-info / ready-for-agent / ready-for-human / wontfix

### 2.2 PRD + Issues
- PRD 文档：`docs/prd-rule-management-mvp.md`
- GitHub Issue #1（PRD）：https://github.com/SHYXIN/agent-aps/issues/1
- 6 个垂直切片 Issues：
  - #2 规则 Schema + CRUD API + 基础 UI
  - #3 Agent 对话翻译规则（依赖 #2）
  - #4 规则冲突检测（依赖 #2）
  - #5 Agent → 冲突检测 → 写入全链路集成（依赖 #3, #4）
  - #6 规则批量导入（依赖 #4）
  - #7 规则变更日志（依赖 #2）

### 2.3 后端实现（已完成，已提交）

**技术栈：** Python FastAPI + SQLAlchemy + SQLite + Pydantic

**文件结构：**
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 应用入口 + API 端点
│   ├── schemas.py       # Pydantic 模型（Condition/Action/RuleCreate）
│   ├── models.py        # SQLAlchemy Rule 模型
│   ├── crud.py          # CRUD 操作（RuleCRUD 类）
│   └── database.py      # 数据库配置（SQLite + SessionLocal）
├── tests/
│   ├── test_schemas.py  # 8 个测试，全部通过
│   ├── test_crud.py     # 11 个测试，全部通过
│   └── test_api.py      # 9 个测试，全部通过
└── .venv/               # Python 虚拟环境
```

**API 端点：**
- `POST /api/rules` — 创建规则（201）
- `GET /api/rules` — 列表（支持 rule_type/status 筛选）
- `GET /api/rules/{id}` — 单条查询
- `PUT /api/rules/{id}` — 更新
- `DELETE /api/rules/{id}` — 删除

**规则 Schema：**
```python
RuleCreate:
  name: str
  description: Optional[str]
  rule_type: "data_cleaning" | "scheduling"
  condition: {field, operator, value}
  action: {field, operator, value}
  free_text: Optional[str]
  status: str = "active"
  notes: Optional[str]
```

**测试状态：** 28/28 全部通过 ✅

---

## 3. 下一步工作

### 3.1 立即继续：前端 UI（Issue #2 的后半部分）

后端 API 已完成，需要 React 前端：
- 规则列表页（展示所有规则，按类型/状态筛选）
- 规则详情/编辑页
- 新建规则表单

**技术栈：** React（技术选型已确认）

### 3.2 可并行（依赖 #2 完成后）

- **Issue #3：Agent 对话翻译规则**
  - 调国产大模型 API
  - 多轮对话补全模糊信息
  - 翻译后展示 JSON 摘要 + 用户确认
  
- **Issue #4：规则冲突检测**
  - 同条件不同动作的直接矛盾检测
  - 冲突确认弹窗 UI

- **Issue #7：规则变更日志**
  - 记录创建/修改/删除操作
  - 变更历史查询 API + UI

### 3.3 后续（依赖 #3+#4）

- **Issue #5：全链路集成**
- **Issue #6：批量导入**

---

## 4. 重要技术细节

### 4.1 API 测试的一个坑
`TestClient` 的 startup 事件会用默认 engine（文件型 SQLite）建表，但测试用内存型 SQLite。解决方法：清除 `app.router.on_startup`，在 fixture 中手动建表。

### 4.2 数据库
MVP 用 SQLite（`sqlite:///./agent_aps.db`），后期可迁移 PostgreSQL。

### 4.3 规则存储
condition 和 action 以 JSON 字符串存储在 `condition_json` / `action_json` 字段中。

---

## 5. 建议调用的 Skills

- `/tdd` — 继续用 TDD 开发剩余模块
- `/to-issues` — 如果需要进一步拆分 issues
- `/requesting-code-review` — 完成一个模块后做代码审查

---

## 6. 关键链接

- 仓库：https://github.com/SHYXIN/agent-aps
- PRD Issue：https://github.com/SHYXIN/agent-aps/issues/1
- 后端代码：`backend/app/` 和 `backend/tests/`
