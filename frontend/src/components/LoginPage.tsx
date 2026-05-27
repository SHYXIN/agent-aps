import { useState } from "react";
import { authApi } from "../api/auth";

interface Props {
  onLogin: () => void;
}

export function LoginPage({ onLogin }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.login(username, password);
      onLogin();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <span className="logo">🏭</span>
          <h1>Agent APS</h1>
          <p>基于 Agent 的认知型 APS 系统</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>👤 用户名</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
              required
            />
          </div>

          <div className="form-group">
            <label>🔒 密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              required
            />
          </div>

          {error && <div className="error-message">❌ {error}</div>}

          <button type="submit" disabled={loading} className="primary full-width">
            {loading ? "登录中..." : "🚀 登录"}
          </button>
        </form>

        <div className="login-footer">
          <p>默认账号: admin / admin123</p>
        </div>
      </div>
    </div>
  );
}
