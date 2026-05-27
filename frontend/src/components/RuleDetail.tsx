import { useState, useEffect } from "react";
import type { Rule, ChangelogEntry } from "../types/rule";
import { ruleApi } from "../api/rules";

interface Props {
  rule: Rule;
  onClose: () => void;
  onEdit: (rule: Rule) => void;
}

export function RuleDetail({ rule, onClose, onEdit }: Props) {
  const [changelog, setChangelog] = useState<ChangelogEntry[]>([]);
  const [tab, setTab] = useState<"detail" | "changelog">("detail");

  useEffect(() => {
    ruleApi.getChangelog(rule.id).then(setChangelog).catch(console.error);
  }, [rule.id]);

  return (
    <div className="rule-detail">
      <div className="detail-header">
        <h2>{rule.name}</h2>
        <button onClick={onClose}>关闭</button>
      </div>

      <div className="tabs">
        <button className={tab === "detail" ? "active" : ""} onClick={() => setTab("detail")}>
          规则详情
        </button>
        <button className={tab === "changelog" ? "active" : ""} onClick={() => setTab("changelog")}>
          变更日志
        </button>
      </div>

      {tab === "detail" && (
        <div className="detail-body">
          <div className="detail-row">
            <label>类型</label>
            <span>{rule.rule_type === "data_cleaning" ? "数据清洗（Rule A）" : "排程约束（Rule B）"}</span>
          </div>
          <div className="detail-row">
            <label>状态</label>
            <span className={`status ${rule.status}`}>{rule.status === "active" ? "启用" : "禁用"}</span>
          </div>
          {rule.description && (
            <div className="detail-row">
              <label>描述</label>
              <span>{rule.description}</span>
            </div>
          )}
          <div className="detail-row">
            <label>条件</label>
            <pre>{JSON.stringify(JSON.parse(rule.condition_json), null, 2)}</pre>
          </div>
          <div className="detail-row">
            <label>动作</label>
            <pre>{JSON.stringify(JSON.parse(rule.action_json), null, 2)}</pre>
          </div>
          {rule.free_text && (
            <div className="detail-row">
              <label>自由文本</label>
              <p>{rule.free_text}</p>
            </div>
          )}
          {rule.notes && (
            <div className="detail-row">
              <label>备注</label>
              <p>{rule.notes}</p>
            </div>
          )}
          <div className="detail-row">
            <label>创建时间</label>
            <span>{rule.created_at ? new Date(rule.created_at).toLocaleString("zh-CN") : "-"}</span>
          </div>
          <div className="detail-row">
            <label>更新时间</label>
            <span>{rule.updated_at ? new Date(rule.updated_at).toLocaleString("zh-CN") : "-"}</span>
          </div>

          <button onClick={() => onEdit(rule)}>编辑规则</button>
        </div>
      )}

      {tab === "changelog" && (
        <div className="changelog">
          {changelog.length === 0 ? (
            <div className="empty">暂无变更记录</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>操作</th>
                  <th>变更前</th>
                  <th>变更后</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                {changelog.map((entry) => (
                  <tr key={entry.id}>
                    <td>
                      <span className={`action ${entry.action}`}>{entry.action}</span>
                    </td>
                    <td>
                      <pre>{entry.before_value ? JSON.stringify(entry.before_value, null, 2) : "-"}</pre>
                    </td>
                    <td>
                      <pre>{entry.after_value ? JSON.stringify(entry.after_value, null, 2) : "-"}</pre>
                    </td>
                    <td>{entry.created_at ? new Date(entry.created_at).toLocaleString("zh-CN") : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
