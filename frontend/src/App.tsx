import { useState, useCallback, useEffect } from "react";
import type { User } from "./types/rule";
import { authApi } from "./api/auth";
import { LandingPage } from "./components/LandingPage";
import { LoginPage } from "./components/LoginPage";
import { RuleList } from "./components/RuleList";
import { RuleForm } from "./components/RuleForm";
import { RuleDetail } from "./components/RuleDetail";
import { AgentChat } from "./components/AgentChat";
import { BulkImport } from "./components/BulkImport";
import "./App.css";

type View = "landing" | "login" | "list" | "create" | "edit" | "detail" | "chat" | "import";

function App() {
  const [view, setView] = useState<View>("landing");
  const [user, setUser] = useState<User | null>(null);
  const [selectedRule, setSelectedRule] = useState<import("./types/rule").Rule | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  // 检查是否已登录
  useEffect(() => {
    if (authApi.isAuthenticated()) {
      authApi.me().then((u) => {
        if (u) {
          setUser(u);
          setView("list");
        }
      });
    }
  }, []);

  const handleLogin = useCallback(() => {
    authApi.me().then((u) => {
      if (u) {
        setUser(u);
        setView("list");
      }
    });
  }, []);

  const handleLogout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
    setView("landing");
  }, []);

  const handleEdit = (rule: import("./types/rule").Rule) => {
    setSelectedRule(rule);
    setView("edit");
  };

  const handleView = (rule: import("./types/rule").Rule) => {
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

  // 未登录：落地页或登录页
  if (!user) {
    if (view === "login") {
      return <LoginPage onLogin={handleLogin} />;
    }
    return <LandingPage onGoToLogin={() => setView("login")} />;
  }

  // 已登录：主应用
  return (
    <div className="app">
      <header>
        <div className="header-left">
          <span className="header-icon">🏭</span>
          <h1>Agent APS</h1>
        </div>
        <nav>
          {view === "list" && (
            <>
              <button className="primary" onClick={() => setView("create")}>
                ➕ 新建规则
              </button>
              <button onClick={() => setView("chat")}>💬 Agent 对话</button>
              <button onClick={() => setView("import")}>📁 批量导入</button>
            </>
          )}
          {view !== "list" && (
            <button onClick={handleCancel}>← 返回列表</button>
          )}
        </nav>
        <div className="header-right">
          <span className="user-info">
            👤 {user.username} {user.role === "admin" ? "🛡️" : ""}
          </span>
          <button onClick={handleLogout}>🚪 退出</button>
        </div>
      </header>

      <main>
        {view === "list" && (
          <RuleList onEdit={handleEdit} onView={handleView} refreshKey={refreshKey} />
        )}
        {(view === "create" || view === "edit") && (
          <RuleForm rule={selectedRule} onSaved={handleSaved} onCancel={handleCancel} />
        )}
        {view === "detail" && selectedRule && (
          <RuleDetail rule={selectedRule} onClose={handleCancel} onEdit={handleEdit} />
        )}
        {view === "chat" && <AgentChat onRuleCreated={handleSaved} />}
        {view === "import" && <BulkImport onImported={handleSaved} onCancel={handleCancel} />}
      </main>
    </div>
  );
}

export default App;
