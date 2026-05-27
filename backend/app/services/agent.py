"""Agent 对话翻译模块

负责多轮对话状态管理 + 自然语言 → 结构化规则的翻译。
实际 LLM 调用通过 llm_client 注入，便于测试时 mock。
"""
import json
import re
from dataclasses import dataclass, field


@dataclass
class ConversationState:
    """追踪一次多轮对话的状态"""
    messages: list[dict] = field(default_factory=list)
    pending_rule: dict | None = None
    missing_info: list[str] = field(default_factory=list)
    collected_info: dict = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return len(self.missing_info) == 0 and self.pending_rule is not None

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def set_pending_rule(self, rule: dict):
        self.pending_rule = rule

    def confirm_rule(self):
        self.pending_rule = None
        self.missing_info.clear()
        self.collected_info.clear()

    def add_missing_info(self, field_name: str):
        if field_name not in self.missing_info:
            self.missing_info.append(field_name)

    def collect_info(self, field_name: str, value):
        self.collected_info[field_name] = value
        if field_name in self.missing_info:
            self.missing_info.remove(field_name)


class LLMClient:
    """LLM 客户端（调用 LongCat / DeepSeek 等兼容 OpenAI API 的模型）"""

    def __init__(self, api_key: str | None = None, model: str = "LongCat-2.0-Preview", base_url: str = "https://api.longcat.chat/openai"):
        from app.core.config import OPENAI_API_KEY, LLM_MODEL, OPENAI_BASE_URL
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or LLM_MODEL
        self.base_url = base_url or OPENAI_BASE_URL

    def chat(self, messages: list[dict]) -> str:
        """调用 LLM API，返回回复文本"""
        import urllib.request
        import json as _json
        import ssl

        payload = _json.dumps({
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            resp = urllib.request.urlopen(req, context=ctx, timeout=30)
            data = _json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[LLM 调用失败: {e}]"


class AgentTranslator:
    """自然语言 → 结构化规则的翻译器"""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def parse_user_input(self, text: str) -> dict:
        """
        解析用户输入，返回：
        - 完整规则信息（如果能直接翻译）
        - 或需要澄清的问题（如果有模糊信息）
        """
        # 尝试本地规则匹配（不依赖 LLM）
        result = self._try_local_parse(text)
        if result:
            return result

        # 模糊信息检测
        vague = self._detect_vague_info(text)
        if vague:
            return {
                "needs_clarification": True,
                "missing_fields": vague["missing_fields"],
                "clarification_question": vague["question"],
                "partial_info": vague.get("partial_info", {}),
            }

        # 兜底：调用 LLM 解析
        return self._llm_parse(text)

    def _llm_parse(self, text: str) -> dict:
        """调用 LLM 解析自然语言"""
        system_prompt = """你是一个工业排程规则解析器。用户会用中文描述排程规则，你需要将其解析为结构化 JSON。

规则类型：
- data_cleaning: 数据清洗规则（如：含硼钢炉容打八折）
- scheduling: 排程业务约束（如：Q345不能和Q235连续浇铸）

输出格式（JSON）：
{
  "name": "规则名称",
  "rule_type": "data_cleaning 或 scheduling",
  "condition": {"field": "字段名", "operator": "操作符", "value": "值"},
  "action": {"field": "字段名", "operator": "操作符", "value": "值"},
  "free_text": "无法结构化的描述（可选）"
}

如果信息不足，返回：
{"needs_clarification": true, "missing_fields": ["字段名"], "clarification_question": "请问..."}

只返回 JSON，不要其他内容。"""

        response = self.llm.chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ])

        # 尝试解析 LLM 返回的 JSON
        import json as _json
        try:
            # 提取 JSON（可能被 markdown 包裹）
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            result = _json.loads(json_str)
            return result
        except Exception:
            # LLM 返回无法解析，标记为需要澄清
            return {
                "needs_clarification": True,
                "missing_fields": ["full_rule"],
                "clarification_question": f"我理解您的意思是：{response}。请确认或补充更多细节。",
            }

    def _try_local_parse(self, text: str) -> dict | None:
        """尝试本地规则匹配（覆盖常见模式）"""
        # 模式：X的Y打Z折 / X的Y按Z计算
        patterns = [
            # "含硼钢炉容打八折"
            r'(.+?)的(.+?)打(\d+)折',
            # "含硼钢炉容按80%计算"
            r'(.+?)的(.+?)按(\d+)%计算',
            # "含硼钢炉容乘以0.8"
            r'(.+?)的(.+?)乘以(\d+\.?\d*)',
            # "含硼钢炉容少算点" → 模糊，不匹配
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                subject = match.group(1).strip()  # 含硼钢
                target = match.group(2).strip()   # 炉容
                value_str = match.group(3).strip()  # 八 / 80 / 0.8

                # 转换折扣值
                if '折' in text:
                    discount = int(value_str) / 10
                elif '%' in text:
                    discount = int(value_str) / 100
                else:
                    discount = float(value_str)

                return {
                    "name": f"{subject}{target}折扣",
                    "rule_type": "data_cleaning",
                    "condition": self._infer_condition(subject),
                    "action": self._infer_action(target, discount),
                }

        return None

    def _detect_vague_info(self, text: str) -> dict | None:
        """检测模糊信息，返回需要澄清的问题"""
        # 包含"少算点"、"多一点"、"少一点"等模糊表达
        vague_patterns = [
            (r'少算点|少一点|低一点', 'discount_value', '请问具体是多少？如八折=0.8，九折=0.9'),
            (r'多一点|高一点|多一点', 'add_value', '请问具体加多少？'),
        ]

        for pattern, field, question in vague_patterns:
            if re.search(pattern, text):
                partial = self._extract_partial_info(text)
                return {
                    "missing_fields": [field],
                    "question": question,
                    "partial_info": partial,
                }

        return None

    def _extract_partial_info(self, text: str) -> dict:
        """从模糊输入中提取部分信息"""
        info = {}
        # 提取钢种
        if '硼' in text or 'B' in text:
            info["condition"] = {"field": "steel_grade", "operator": "contains", "value": "B"}
        # 提取目标字段
        if '炉容' in text or '容量' in text:
            info["action_field"] = "furnace_capacity"
        return info

    def _infer_condition(self, subject: str) -> dict:
        """从主语推断条件"""
        if '硼' in subject or 'B' in subject:
            return {"field": "steel_grade", "operator": "contains", "value": "B"}
        return {"field": "steel_grade", "operator": "contains", "value": subject}

    def _infer_action(self, target: str, value: float) -> dict:
        """从目标字段和值推断动作"""
        if '炉容' in target or '容量' in target:
            return {"field": "furnace_capacity", "operator": "multiply", "value": value}
        if '温度' in target:
            return {"field": "temperature", "operator": "add", "value": value}
        return {"field": target, "operator": "multiply", "value": value}

    def build_rule(self, info: dict) -> dict:
        """从收集的信息构建完整规则"""
        return {
            "name": info.get("name", "未命名规则"),
            "rule_type": info.get("rule_type", "data_cleaning"),
            "condition": info.get("condition", {}),
            "action": info.get("action", {}),
        }

    def determine_rule_type(self, text: str) -> str:
        """判断规则类型"""
        scheduling_keywords = ["浇铸", "连浇", "顺序", "不能", "禁止", "兼容", "切换", "排产", "排程"]
        for kw in scheduling_keywords:
            if kw in text:
                return "scheduling"
        return "data_cleaning"

    def generate_clarification_question(self, state: ConversationState) -> str:
        """生成澄清问题"""
        if not state.missing_info:
            return ""

        field = state.missing_info[0]
        questions = {
            "discount_value": "请问折扣比例是多少？如八折=0.8，九折=0.9",
            "add_value": "请问具体加多少？",
            "field_name": "请问是哪个字段？",
            "condition_value": "请问条件的值是什么？",
        }
        return questions.get(field, f"请提供 {field} 的具体值")
