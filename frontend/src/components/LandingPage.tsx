interface Props {
  onGoToLogin: () => void;
}

export function LandingPage({ onGoToLogin }: Props) {
  return (
    <div className="landing-page">
      <div className="landing-hero">
        <div className="hero-logo">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
            <rect width="64" height="64" rx="12" fill="#1e293b"/>
            <path d="M20 24h24v4H20zM20 32h16v4H20zM20 40h20v4H20z" fill="#60a5fa"/>
            <circle cx="44" cy="38" r="8" fill="#a78bfa"/>
          </svg>
        </div>
        <h1>Agent APS</h1>
        <p className="hero-subtitle">基于 Agent 的认知型高级计划与排程系统</p>
        <p className="hero-desc">
          通过自然语言即可管理工业排程规则，让 AI 帮你处理复杂的约束注入与冲突检测。
          钢铁行业首个听得懂业务语言的智能排程平台。
        </p>
        <div className="hero-actions">
          <button className="btn-primary" onClick={onGoToLogin}>
            登录系统
          </button>
          <a href="https://github.com/SHYXIN/agent-aps" target="_blank" rel="noopener" className="btn-secondary">
            查看文档
          </a>
        </div>
      </div>

      <div className="landing-features">
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <h3>自然语言输入</h3>
          <p>用中文描述规则，Agent 自动翻译为结构化约束，无需运筹学背景</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
            </svg>
          </div>
          <h3>智能冲突检测</h3>
          <p>自动识别规则冲突，提供三级降级方案，确保系统永远有解</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 20V10M12 20V4M6 20v-6"/>
            </svg>
          </div>
          <h3>可视化管理</h3>
          <p>规则库、变更日志、批量导入一站式管理，全程可追溯</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <h3>安全可靠</h3>
          <p>独立 JWT 认证，Session 隔离，支持多角色权限管理</p>
        </div>
      </div>

      <footer className="landing-footer">
        <p>Agent APS v1.0 · Built with FastAPI + React</p>
      </footer>
    </div>
  );
}
