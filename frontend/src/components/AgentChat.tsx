import { useState, useRef, useEffect } from "react";
import type { RuleCreate, ConflictInfo } from "../types/rule";

interface Message {
  role: "user" | "agent";
  content: string;
}

interface AgentResponse {
  reply: string;
  pending_rule: RuleCreate | null;
  needs_confirmation: boolean;
  needs_clarification: boolean;
  clarification_question: string | null;
  has_conflict?: boolean;
  conflicts?: ConflictInfo[];
  created_id?: number;
}

interface Props {
  onRuleCreated: () => void;
}

export function AgentChat({ onRuleCreated }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingRule, setPendingRule] = useState<RuleCreate | null>(null);
  const [hasConflict, setHasConflict] = useState(false);
  const [conflicts, setConflicts] = useState<ConflictInfo[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const sessionId = "session-" + Math.random().toString(36).slice(2, 10);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });
      const data: AgentResponse = await res.json();

      setMessages((prev) => [...prev, { role: "agent", content: data.reply }]);
      setPendingRule(data.pending_rule);
      setHasConflict(!!data.has_conflict);
      setConflicts(data.conflicts || []);

      if (data.created_id) {
        onRuleCreated();
        setPendingRule(null);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "agent", content: `错误: ${(e as Error).message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (force: boolean = false) => {
    if (force) {
      // 强制写入（覆盖冲突）
      setLoading(true);
      try {
        const res = await fetch("/api/rules/force", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(pendingRule),
        });
        const data = await res.json();
        setMessages((prev) => [
          ...prev,
          { role: "agent", content: `规则 ${data.name} 已强制写入规则库。` },
        ]);
        setPendingRule(null);
        setHasConflict(false);
        onRuleCreated();
      } catch (e) {
        setMessages((prev) => [
          ...prev,
          { role: "agent", content: `写入失败: ${(e as Error).message}` },
        ]);
      } finally {
        setLoading(false);
      }
    } else {
      sendMessage("确认");
    }
  };

  const handleCancel = () => {
    setMessages((prev) => [
      ...prev,
      { role: "agent", content: "已取消。您可以继续描述新规则。" },
    ]);
    setPendingRule(null);
    setHasConflict(false);
  };

  return (
    <div className="agent-chat">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-hint">
            试着说：含硼钢炉容打八折 或 Q345不能和Q235连续浇铸
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="bubble">{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="message agent">
            <div className="bubble typing">...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {pendingRule && hasConflict && (
        <div className="conflict-bar">
          <strong>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{verticalAlign: "-2px", marginRight: "6px"}}>
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            规则冲突
          </strong>
          <ul>
            {conflicts.map((c, i) => (
              <li key={i}>与 {c.existing_rule} 冲突</li>
            ))}
          </ul>
          <div className="conflict-actions">
            <button onClick={() => handleConfirm(true)} className="primary">
              强制写入
            </button>
            <button onClick={handleCancel}>取消</button>
          </div>
        </div>
      )}

      {pendingRule && !hasConflict && (
        <div className="confirm-bar">
          <button onClick={() => handleConfirm(false)} className="primary">
            ✓ 确认写入
          </button>
          <button onClick={handleCancel}>取消</button>
        </div>
      )}

      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
          placeholder="输入规则描述..."
          disabled={loading}
        />
        <button onClick={() => sendMessage(input)} disabled={loading || !input.trim()}>
          发送
        </button>
      </div>
    </div>
  );
}
