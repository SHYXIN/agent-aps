interface Props {
  onGoToLogin: () => void;
}

export function LandingPage({ onGoToLogin }: Props) {
  return (
    <div className="landing-page">
      <div className="landing-hero">
        <span className="hero-icon">🏭</span>
        <h1>Agent APS</h1>
        <p className="hero-subtitle">基于 Agent 的认知型 APS 系统</p>
        <p className="hero-desc">
          通过自然语言即可管理工业排程规则，让 AI 帮你处理复杂的约束注入与冲突检测。
        </p>
        <button className="primary large" onClick={onGoToLogin}>
          🚀 立即开始
        </button>
      </div>

      <div className="landing-features">
        <div className="feature">
          <span className="icon">💬</span>
          <h3>自然语言输入</h3>
          <p>用中文描述规则，Agent 自动翻译为结构化约束</p>
        </div>
        <div className="feature">
          <span className="icon">🔍</span>
          <h3>智能冲突检测</h3>
          <p>自动识别规则冲突，提供降级方案</p>
        </div>
        <div className="feature">
          <span className="icon">📊</span>
          <h3>可视化管理</h3>
          <p>规则库、变更日志、批量导入一站式管理</p>
        </div>
        <div className="feature">
          <span className="icon">🔐</span>
          <h3>安全可靠</h3>
          <p>独立 JWT 认证，Session 隔离</p>
        </div>
      </div>
    </div>
  );
}
