# PRD：Agent APS 规则管理 MVP

## Problem Statement

钢铁企业的排程规则（数据清洗规则 + 排程业务规则）散落在 Excel、经验和口头传达中，无法结构化管理。业务人员无法通过自然语言添加或修改规则，每次规则变更都需要技术人员介入。当新规则与旧规则冲突时，缺乏自动检测机制，容易导致数据处理错误或排程结果异常。

## Solution

构建一个基于 LLM Agent 的规则管理系统。业务人员通过自然语言与 Agent 对话，Agent 将其翻译为结构化规则并写入规则库。系统自动检测规则冲突，模糊冲突交由用户确认。用户确认后规则立即生效。

MVP 阶段只做规则管理，不做排程求解、甘特图、数据适配。

## User Stories

1. As a 计划员, I want 通过自然语言告诉系统新规则（如"含硼钢炉容打八折"），so that 不需要技术人员写代码就能添加规则
2. As a 计划员, I want Agent 在翻译模糊信息时反问我（如"少算点具体是多少？"），so that 规则准确反映我的意图
3. As a 计划员, I want 在 Agent 翻译完规则后看到结构化的 JSON 摘要并确认，so that 我能验证规则是否正确再写入
4. As a 计划员, I want 查看当前规则库中所有规则的列表，so that 我能了解系统当前有哪些规则在生效
5. As a 计划员, I want 禁用或删除某条规则，so that 不再需要的规则可以停用
6. As a 计划员, I want 编辑已有规则的条件或动作，so that 规则变更时不需要删除重建
7. As a 计划员, I want 在添加新规则时，系统自动检测与现有规则的直接矛盾（同条件不同动作），so that 避免规则冲突导致数据处理错误
8. As a 计划员, I want 当检测到规则冲突时，系统展示冲突详情并让我选择覆盖或保留，so that 我能做出明确决策
9. As a 计划员, I want 区分数据清洗规则（Rule A）和排程业务规则（Rule B），so that 规则库分类清晰
10. As a 计划员, I want 为规则添加备注说明，so that 记录规则的业务背景和添加原因
11. As a 计划员, I want 通过对话让 Agent 修改已有规则，so that 不需要手动编辑 JSON
12. As a 计划员, I want 查看规则的创建时间和来源（导入/对话），so that 了解规则的历史
13. As a 计划员, I want 批量导入初始规则（如从 Excel 或 JSON 文件），so that 系统上线时快速建立规则库
14. As a 计划员, I want Agent 记住当前对话的上下文，so that 连续添加多条规则时不需要重复说明背景
15. As a 管理员, I want 查看规则变更日志，so that 能追溯谁在什么时候改了什么规则

## Implementation Decisions

### 1. 规则数据模型

规则采用"条件→动作"结构，支持两种类型：

- **Rule A（数据清洗规则）**：处理 ERP 脏数据，如缺失值填充、异常值修正
- **Rule B（排程业务规则）**：影响排程结果的约束，如钢种兼容性、设备能力限制

95% 的规则可结构化，5% 无法结构化的规则以自由文本存储，Agent 可引用但不自动执行。

### 2. 规则存储

SQLite（MVP），后期可迁移 PostgreSQL。单人项目，SQLite 够用。

### 3. Agent 翻译策略

- Agent 只负责翻译，不负责冲突判断
- 翻译过程中遇到模糊信息（如"少算点"），Agent 必须反问用户获取具体数值
- 翻译完成后展示结构化 JSON 摘要，用户确认后才写入规则库
- 不猜测数值，不留默认值

### 4. 冲突检测策略

- 程序检测：同字段、同条件、不同动作的直接矛盾
- 模糊冲突：程序标记后交给用户确认，不依赖 Agent 做冲突推理
- 冲突检测在用户确认写入前执行

### 5. Agent 状态管理

采用结构化状态管理，不依赖 LLM 对话历史。状态对象包含：
- 当前规则库快照（或摘要）
- 当前对话中待确认的规则
- 用户已回答的信息
- 待追问的模糊点

### 6. LLM 选型

国产大模型（DeepSeek / 千问 / GLM），调用 API，不私有部署。数据不出境，合规优先。

### 7. 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React |
| 后端 | Python FastAPI |
| 数据库 | SQLite（MVP） |
| Agent | 国产大模型 API |
| 规则管理 UI | 对话框 + 规则列表 + 冲突确认弹窗 |

### 8. API 概要

- `POST /api/rules` — 创建规则（Agent 翻译后调用）
- `GET /api/rules` — 查询规则列表（支持按类型筛选）
- `PUT /api/rules/{id}` — 更新规则
- `DELETE /api/rules/{id}` — 删除/禁用规则
- `POST /api/rules/conflict-check` — 检测新规则与现有规则的冲突
- `POST /api/agent/chat` — Agent 对话接口（多轮）
- `POST /api/rules/import` — 批量导入规则

## Testing Decisions

- **Rule Schema**：单元测试验证规则 JSON 的合法性、边界条件
- **Rule Store**：单元测试验证 CRUD 操作、查询逻辑
- **Conflict Detector**：单元测试覆盖直接矛盾、无冲突、多规则冲突等场景
- **Agent Translator**：集成测试，用 10-20 条真实规则样本验证翻译效果（人工确认结果）
- 测试只验证外部行为，不测实现细节

## Out of Scope

- 排程求解器（ALNS / Pyomo + HiGHS）
- 甘特图展示与拖拽交互
- Data Adapter（ERP/MES 数据对接）
- 自动降级机制
- KPI 仪表盘
- Docker 部署
- 多租户
- 用户认证与权限管理
- 增量重排
- 订单分解逻辑

## Further Notes

- MVP 目标：验证 Agent 能否准确翻译工业领域的业务规则
- 用户确认是最终校验，不追求 Agent 100% 准确率
- 后续 Phase 2 才接入排程求解器
- 项目仓库：https://github.com/SHYXIN/agent-aps
