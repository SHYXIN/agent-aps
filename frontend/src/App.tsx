import { useState, useCallback } from "react";
import type { Rule } from "./types/rule";
import { RuleList } from "./components/RuleList";
import { RuleForm } from "./components/RuleForm";
import { RuleDetail } from "./components/RuleDetail";
import { AgentChat } from "./components/AgentChat";
import { BulkImport } from "./components/BulkImport";
import "./App.css";

type View = "list" | "create" | "edit" | "detail" | "chat" | "import";

function App() {
  const [view, setView] = useState<View>("list");
  const [selectedRule, setSelectedRule] = useState<Rule | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleEdit = (rule: Rule) => {
    setSelectedRule(rule);
    setView("edit");
  };

  const handleView = (rule: Rule) => {
    setSelectedRule(rule);
    setView("detail");
  };

  const handleSaved = useCallback(() => {
    setRefreshKey((k) => k + 1);
    setView("list");
    setSelectedRule(null);
  }, []);

  const handleCancel = () => {
    setView("list");
    setSelectedRule(null);
  };

  return (
    <div className="app">
      <header>
        <h1>Agent APS 规则管理</h1>
        <nav>
          {view === "list" && (
            <>
              <button className="primary" onClick={() => setView("create")}>
                + 新建规则
              </button>
              <button onClick={() => setView("chat")}>💬 Agent 对话</button>
              <button onClick={() => setView("import")}>📁 批量导入</button>
            </>
          )}
          {view !== "list" && (
            <button onClick={handleCancel}>← 返回列表</button>
          )}
        </nav>
      </header>

      <main>
        {view === "list" && (
          <RuleList
            onEdit={handleEdit}
            onView={handleView}
            refreshKey={refreshKey}
          />
        )}
        {(view === "create" || view === "edit") && (
          <RuleForm
            rule={selectedRule}
            onSaved={handleSaved}
            onCancel={handleCancel}
          />
        )}
        {view === "detail" && selectedRule && (
          <RuleDetail
            rule={selectedRule}
            onClose={handleCancel}
            onEdit={handleEdit}
          />
        )}
        {view === "chat" && (
          <AgentChat onRuleCreated={handleSaved} />
        )}
        {view === "import" && (
          <BulkImport onImported={handleSaved} onCancel={handleCancel} />
        )}
      </main>
    </div>
  );
}

export default App;
