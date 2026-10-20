export function Navbar({ goTo, dbStatus, userSession, onLogout }) {
  return (
    <header className="navbar">
      <button className="brand" onClick={() => goTo("home")} type="button">
        <span className="brand-mark">B</span>
        <span className="brand-name">BlindPaper</span>
      </button>

      {userSession ? (
        <div className="nav-actions">
          <div className="faculty-badge">
            <span className="faculty-avatar">🎓</span>
            <span className="faculty-name">{userSession.name}</span>
            <span className="faculty-role">({userSession.role})</span>
          </div>

          <div
            className={`db-indicator ${dbStatus === "connected" ? "db-online" : "db-offline"}`}
            title={`MongoDB Database: ${dbStatus || "checking..."}`}
          >
            <span className="status-dot"></span>
            <span>DB {dbStatus === "connected" ? "Connected" : "Local (Checking)"}</span>
          </div>

          <button
            className="secondary-button nav-btn"
            onClick={() => goTo("faculty_dashboard")}
            type="button"
          >
            Dashboard
          </button>

          <button
            className="primary-button nav-btn"
            onClick={() => goTo("create_paper")}
            type="button"
          >
            + Create Paper
          </button>

          <button className="logout-button" onClick={onLogout} type="button">
            Sign Out
          </button>
        </div>
      ) : (
        <>
          <nav className="nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How it works</a>
            <a href="#about">About</a>
          </nav>

          <div className="nav-actions">
            <button
              className="login-button"
              onClick={() => goTo("login")}
              type="button"
            >
              Faculty Login
            </button>
            <button
              className="primary-button"
              onClick={() => goTo("register")}
              type="button"
            >
              Register
            </button>
          </div>
        </>
      )}
    </header>
  );
}
