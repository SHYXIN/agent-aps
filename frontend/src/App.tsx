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

  if (!user) {
    if (view === "login") {
      return <LoginPage onLogin={handleLogin} />;
    }
    return <LandingPage onGoToLogin={() => setView("login")} />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-brand">
          <svg width="28" height="28" viewBox="0 0 64 64" fill="none">
            <rect width="64" height="64" rx="12" fill="#1e293b"/>
            <path d="M20 24h24v4H20zM20 32h16v4H20zM20 40h20v4H20z" fill="#60a5fa"/>
            <circle cx="44" cy="38" r="8" fill="#a78bfa"/>
          </svg>
          <span className="brand-name">Agent APS</span>
        </div>

        <nav className="header-nav">
          <button className={view === "list" ? "active" : ""} onClick={() => setView("list")}>
            规则管理
          </button>
          <button className={view === "chat" ? "active" : ""} onClick={() => setView("chat")}>
            Agent 对话
          </button>
          <button className={view === "import" ? "active" : ""} onClick={() => setView("import")}>
            批量导入
          </button>
          <button className="btn-create" onClick={() => setView("create")}>
            + 新建规则
          </button>
        </nav>

        <div className="header-user">
          <span className="user-name">{user.username}</span>
          <span className="user-role">{user.role === "admin" ? "管理员" : "用户"}</span>
          <button className="btn-logout" onClick={handleLogout}>退出</button>
        </div>
      </header>

      <main className="app-main">
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
