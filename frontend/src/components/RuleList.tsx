import { useState, useEffect } from "react";
import type { Rule } from "../types/rule";
import { ruleApi } from "../api/rules";

interface Props {
  onEdit: (rule: Rule) => void;
  onView: (rule: Rule) => void;
  refreshKey: number;
}

export function RuleList({ onEdit, onView, refreshKey }: Props) {
  const [rules, setRules] = useState<Rule[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    ruleApi
      .list(filter !== "all" ? { rule_type: filter } : undefined)
      .then(setRules)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filter, refreshKey]);

  const handleDelete = async (id: number, name: string) => {
    if (!confirm(`确认删除规则 ${name} ?`)) return;
    try {
      await ruleApi.delete(id);
      setRules((prev) => prev.filter((r) => r.id !== id));
    } catch (e) {
      alert(`删除失败: ${(e as Error).message}`);
    }
  };

  const handleToggleStatus = async (rule: Rule) => {
    const newStatus = rule.status === "active" ? "disabled" : "active";
    try {
      const updated = await ruleApi.update(rule.id, { status: newStatus });
      setRules((prev) => prev.map((r) => (r.id === rule.id ? updated : r)));
    } catch (e) {
      alert(`操作失败: ${(e as Error).message}`);
    }
  };

  if (loading) return <div className="loading">加载中...</div>;
  if (error) return <div className="error">错误: {error}</div>;

  return (
    <div className="rule-list">
      <div className="filters">
        <button className={filter === "all" ? "active" : ""} onClick={() => setFilter("all")}>
          全部
        </button>
        <button className={filter === "data_cleaning" ? "active" : ""} onClick={() => setFilter("data_cleaning")}>
          数据清洗
        </button>
        <button className={filter === "scheduling" ? "active" : ""} onClick={() => setFilter("scheduling")}>
          排程约束
        </button>
      </div>

      {rules.length === 0 ? (
        <div className="empty">暂无规则</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>名称</th>
              <th>类型</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.id} className={rule.status === "disabled" ? "disabled" : ""}>
                <td>
                  <a onClick={() => onView(rule)} style={{ cursor: "pointer", color: "#1890ff" }}>
                    {rule.name}
                  </a>
                </td>
                <td>
                  <span className={`tag ${rule.rule_type}`}>
                    {rule.rule_type === "data_cleaning" ? "数据清洗" : "排程约束"}
                  </span>
                </td>
                <td>
                  <span className={`status ${rule.status}`}>
                    {rule.status === "active" ? "启用" : "禁用"}
                  </span>
                </td>
                <td>{rule.created_at ? new Date(rule.created_at).toLocaleString("zh-CN") : "-"}</td>
                <td className="actions">
                  <button onClick={() => handleToggleStatus(rule)}>
                    {rule.status === "active" ? "禁用" : "启用"}
                  </button>
                  <button onClick={() => onEdit(rule)}>编辑</button>
                  <button className="danger" onClick={() => handleDelete(rule.id, rule.name)}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
