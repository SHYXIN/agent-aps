import { useState, useRef } from "react";

interface ImportPreview {
  total: number;
  valid_count: number;
  error_count: number;
  conflict_count: number;
  errors: { index: number; name: string; error: string }[];
  conflicts: { index: number; name: string; conflicts: { existing_rule: string; reason: string }[] }[];
}

interface Props {
  onImported: () => void;
  onCancel: () => void;
}

export function BulkImport({ onImported, onCancel }: Props) {
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      let rules: unknown[];
      if (file.name.endsWith(".json")) {
        const text = await file.text();
        rules = JSON.parse(text);
      } else {
        alert("当前版本仅支持 JSON 文件导入");
        return;
      }

      if (!Array.isArray(rules)) {
        alert("文件格式错误：需要 JSON 数组");
        return;
      }

      const res = await fetch("/api/rules/import/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(rules),
      });
      const data = await res.json();
      setPreview(data);
    } catch (err) {
      alert(`文件解析失败: ${(err as Error).message}`);
    }
  };

  const handleImport = async () => {
    if (!preview) return;
    setImporting(true);
    try {
      // 重新读取文件并导入
      const file = fileRef.current?.files?.[0];
      if (!file) return;
      const text = await file.text();
      const rules = JSON.parse(text);

      const res = await fetch("/api/rules/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(rules),
      });
      const data = await res.json();
      setResult(
        `导入完成：成功 ${data.imported} 条，跳过冲突 ${data.skipped_conflicts} 条，跳过错误 ${data.skipped_errors} 条`
      );
      onImported();
    } catch (err) {
      alert(`导入失败: ${(err as Error).message}`);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="bulk-import">
      <h2>批量导入规则</h2>

      {!preview && !result && (
        <div className="upload-area">
          <p>选择 JSON 文件（规则数组格式）</p>
          <input
            ref={fileRef}
            type="file"
            accept=".json"
            onChange={handleFileSelect}
          />
          <p className="hint">
            文件格式：JSON 数组，每条规则包含 name、rule_type、condition、action 字段
          </p>
        </div>
      )}

      {preview && !result && (
        <div className="preview">
          <h3>导入预览</h3>
          <div className="summary">
            <span>总计：{preview.total} 条</span>
            <span className="success">合法：{preview.valid_count} 条</span>
            <span className="warning">冲突：{preview.conflict_count} 条</span>
            <span className="error">错误：{preview.error_count} 条</span>
          </div>

          {preview.errors.length > 0 && (
            <div className="error-list">
              <h4>错误详情</h4>
              <ul>
                {preview.errors.map((e, i) => (
                  <li key={i}>
                    第 {e.index + 1} 条 {e.name || "(无名称)"}: {e.error}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {preview.conflicts.length > 0 && (
            <div className="conflict-list">
              <h4>冲突详情</h4>
              <ul>
                {preview.conflicts.map((c, i) => (
                  <li key={i}>
                    第 {c.index + 1} 条 {c.name}: 与 {c.conflicts.map((x) => x.existing_rule).join(", ")} 冲突
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="import-actions">
            <button
              onClick={handleImport}
              disabled={importing || preview.valid_count === 0}
              className="primary"
            >
              {importing ? "导入中..." : `确认导入（跳过冲突和错误）`}
            </button>
            <button onClick={() => setPreview(null)}>重新选择文件</button>
          </div>
        </div>
      )}

      {result && (
        <div className="result">
          <p>{result}</p>
          <button onClick={onImported}>完成</button>
        </div>
      )}

      {!result && <button onClick={onCancel}>取消</button>}
    </div>
  );
}
