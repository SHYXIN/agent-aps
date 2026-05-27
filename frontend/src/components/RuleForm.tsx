import { useState } from "react";
import type { Rule, RuleCreate, ConflictInfo } from "../types/rule";
import { ruleApi } from "../api/rules";

interface Props {
  rule?: Rule | null;
  onSaved: () => void;
  onCancel: () => void;
}

const emptyForm: RuleCreate = {
  name: "",
  rule_type: "data_cleaning",
  condition: { field: "", operator: "eq", value: "" },
  action: { field: "", operator: "set", value: "" },
};

export function RuleForm({ rule, onSaved, onCancel }: Props) {
  const isEdit = !!rule;
  const [form, setForm] = useState<RuleCreate>(
    isEdit
      ? {
          name: rule.name,
          description: rule.description || undefined,
          rule_type: rule.rule_type,
          condition: JSON.parse(rule.condition_json),
          action: JSON.parse(rule.action_json),
          free_text: rule.free_text || undefined,
          notes: rule.notes || undefined,
        }
      : { ...emptyForm }
  );
  const [conflicts, setConflicts] = useState<ConflictInfo[]>([]);
  const [saving, setSaving] = useState(false);

  const update = (path: string, value: unknown) => {
    const keys = path.split(".");
    setForm((prev) => {
      const next = { ...prev } as Record<string, unknown>;
      let obj = next;
      for (let i = 0; i < keys.length - 1; i++) {
        obj[keys[i]] = { ...(obj[keys[i]] as Record<string, unknown>) };
        obj = obj[keys[i]] as Record<string, unknown>;
      }
      obj[keys[keys.length - 1]] = value;
      return next as unknown as RuleCreate;
    });
  };

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      alert("请输入规则名称");
      return;
    }
    setSaving(true);
    setConflicts([]);

    try {
      if (isEdit && rule) {
        await ruleApi.update(rule.id, form as unknown as Record<string, unknown>);
        onSaved();
      } else {
        const result = await ruleApi.create(form);
        if ("status" in result && result.status === "conflict") {
          setConflicts(result.conflicts);
          return;
        }
        onSaved();
      }
    } catch (e) {
      alert(`保存失败: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleForceSubmit = async () => {
    setSaving(true);
    try {
      await ruleApi.forceCreate(form);
      onSaved();
    } catch (e) {
      alert(`保存失败: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rule-form">
      <h2>{isEdit ? "编辑规则" : "新建规则"}</h2>

      {conflicts.length > 0 && (
        <div className="conflict-warning">
          <strong>⚠️ 检测到规则冲突：</strong>
          <ul>
            {conflicts.map((c, i) => (
              <li key={i}>
                与 {c.existing_rule} 冲突 ({c.reason})
              </li>
            ))}
          </ul>
          <button onClick={handleForceSubmit} disabled={saving}>
            强制写入
          </button>
          <button onClick={() => setConflicts([])}>取消</button>
        </div>
      )}

      <div className="form-group">
        <label>规则名称 *</label>
        <input
          value={form.name}
          onChange={(e) => update("name", e.target.value)}
          placeholder="如：含硼钢炉容折扣"
        />
      </div>

      <div className="form-group">
        <label>描述</label>
        <input
          value={form.description || ""}
          onChange={(e) => update("description", e.target.value)}
          placeholder="规则的业务说明"
        />
      </div>

      <div className="form-group">
        <label>规则类型</label>
        <select
          value={form.rule_type}
          onChange={(e) => update("rule_type", e.target.value)}
        >
          <option value="data_cleaning">数据清洗（Rule A）</option>
          <option value="scheduling">排程约束（Rule B）</option>
        </select>
      </div>

      <fieldset>
        <legend>条件（Condition）</legend>
        <div className="form-row">
          <div className="form-group">
            <label>字段</label>
            <input
              value={form.condition.field}
              onChange={(e) => update("condition.field", e.target.value)}
              placeholder="如：steel_grade"
            />
          </div>
          <div className="form-group">
            <label>操作符</label>
            <select
              value={form.condition.operator}
              onChange={(e) => update("condition.operator", e.target.value)}
            >
              <option value="eq">等于</option>
              <option value="contains">包含</option>
              <option value="gt">大于</option>
              <option value="lt">小于</option>
              <option value="in">在列表中</option>
              <option value="incompatible">不兼容</option>
            </select>
          </div>
          <div className="form-group">
            <label>值</label>
            <input
              value={String(form.condition.value ?? "")}
              onChange={(e) => update("condition.value", e.target.value)}
              placeholder="如：B"
            />
          </div>
        </div>
      </fieldset>

      <fieldset>
        <legend>动作（Action）</legend>
        <div className="form-row">
          <div className="form-group">
            <label>字段</label>
            <input
              value={form.action.field}
              onChange={(e) => update("action.field", e.target.value)}
              placeholder="如：furnace_capacity"
            />
          </div>
          <div className="form-group">
            <label>操作符</label>
            <select
              value={form.action.operator}
              onChange={(e) => update("action.operator", e.target.value)}
            >
              <option value="set">设为</option>
              <option value="multiply">乘以</option>
              <option value="add">加上</option>
              <option value="block">禁止</option>
            </select>
          </div>
          <div className="form-group">
            <label>值</label>
            <input
              value={String(form.action.value ?? "")}
              onChange={(e) => update("action.value", e.target.value)}
              placeholder="如：0.8"
            />
          </div>
        </div>
      </fieldset>

      <div className="form-group">
        <label>备注说明</label>
        <textarea
          value={form.notes || ""}
          onChange={(e) => update("notes", e.target.value)}
          placeholder="规则的业务背景和添加原因"
          rows={3}
        />
      </div>

      <div className="form-group">
        <label>自由文本（无法结构化的规则）</label>
        <textarea
          value={form.free_text || ""}
          onChange={(e) => update("free_text", e.target.value)}
          placeholder="如：经验上1号炉出钢温度要比标准高20度"
          rows={2}
        />
      </div>

      <div className="form-actions">
        <button onClick={handleSubmit} disabled={saving} className="primary">
          {saving ? "保存中..." : isEdit ? "保存修改" : "创建规则"}
        </button>
        <button onClick={onCancel}>取消</button>
      </div>
    </div>
  );
}
