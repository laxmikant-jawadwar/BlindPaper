import { useState } from "react";
import "./App.css";
import { UserDashboard } from "./components/UserDashboard";
import { UploadPdf } from "./components/UploadPdf";
import { PaperConfig } from "./components/PaperConfig";

function App() {
  const [page, setPage] = useState("home");
  const [userSession, setUserSession] = useState(null);
  const [uploadedSyllabus, setUploadedSyllabus] = useState(null);

  const goTo = (nextPage) => {
    setPage(nextPage);
    window.scrollTo(0, 0);
  };

  const handleLogout = () => {
    setUserSession(null);
    goTo("home");
  };

  // -------------------------------------------------------------
  // Admin Page
  // -------------------------------------------------------------
  if (page === "admin") {
    return (
      <div className="auth-page">
        <div className="auth-card admin-card">
          <div className="brand-mark">B</div>
          <h1>Admin Dashboard</h1>
          <p>Welcome to the BlindPaper administration panel.</p>

          <div className="admin-option">
            <strong>👥 User Management</strong>
            <span>Manage registered users.</span>
          </div>

          <div className="admin-option">
            <strong>📄 Question Papers</strong>
            <span>Review generated question papers.</span>
          </div>

          <div className="admin-option">
            <strong>📚 Syllabus Management</strong>
            <span>Review uploaded syllabi.</span>
          </div>

          <button
            className="primary-button full-button"
            onClick={() => goTo("login")}
            type="button"
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // Login & Register Pages
  // -------------------------------------------------------------
  if (page === "login" || page === "register") {
    const isLogin = page === "login";

    return (
      <div className="auth-page">
        <button
          className="back-home"
          onClick={() => goTo("home")}
          type="button"
        >
          ← Back to Home
        </button>

        <div className="auth-card">
          <div className="brand-mark">B</div>
          <h1>{isLogin ? "Welcome back!" : "Create your account"}</h1>
          <p>
            {isLogin
              ? "Sign in to continue to BlindPaper."
              : "Join BlindPaper and simplify question paper creation."}
          </p>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              const formData = new FormData(event.currentTarget);
              const email = formData.get("email") || "user@example.com";
              setUserSession({ email });
              goTo("dashboard");
            }}
          >
            {!isLogin && (
              <label>
                Full Name
                <input
                  type="text"
                  name="fullName"
                  placeholder="Enter your full name"
                  required
                />
              </label>
            )}

            <label>
              Email Address
              <input
                type="email"
                name="email"
                placeholder="you@example.com"
                required
              />
            </label>

            <label>
              Password
              <input
                type="password"
                name="password"
                placeholder="Enter your password"
                minLength={6}
                required
              />
            </label>

            <button type="submit" className="primary-button full-button">
              {isLogin ? "Login" : "Create Account"}
            </button>
          </form>

          {isLogin && (
            <button
              type="button"
              className="admin-login-button"
              onClick={() => goTo("admin")}
            >
              Login as Admin →
            </button>
          )}

          <div className="auth-switch">
            {isLogin ? "Don't have an account?" : "Already have an account?"}
            <button
              type="button"
              onClick={() => goTo(isLogin ? "register" : "login")}
            >
              {isLogin ? " Register" : " Login"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // Authenticated Dashboard & Creation Flow Pages
  // -------------------------------------------------------------
  if (page === "dashboard") {
    return (
      <UserDashboard
        goTo={goTo}
        userSession={userSession}
        onSelectPaper={(paper) => {
          setUploadedSyllabus({
            subject_name: paper.subject_name,
            filename: paper.filename,
            units: [
              "Unit 1: Fundamentals",
              "Unit 2: Core Concepts",
              "Unit 3: Applications",
            ],
          });
        }}
        onLogout={handleLogout}
      />
    );
  }

  if (page === "upload_pdf") {
    return (
      <UploadPdf
        goTo={goTo}
        onUploadComplete={(data) => {
          setUploadedSyllabus(data);
        }}
      />
    );
  }

  if (page === "paper_config") {
    return (
      <PaperConfig
        goTo={goTo}
        uploadedSyllabus={uploadedSyllabus}
      />
    );
  }

  // -------------------------------------------------------------
  // Original Landing Page (Unchanged)
  // -------------------------------------------------------------
  return (
    <div className="landing-page">
      <header className="navbar">
        <button
          className="brand"
          onClick={() => goTo("home")}
          type="button"
        >
          <span className="brand-mark">B</span>
          <span className="brand-name">BlindPaper</span>
        </button>

        <nav className="nav-links">
          <a href="#features">Features</a>
          <a href="#how-it-works">How it works</a>
          <a href="#about">About</a>
        </nav>

        <div className="nav-actions">
          {userSession ? (
            <button
              className="primary-button"
              onClick={() => goTo("dashboard")}
              type="button"
            >
              Go to Dashboard
            </button>
          ) : (
            <>
              <button
                className="login-button"
                onClick={() => goTo("login")}
                type="button"
              >
                Login
              </button>
              <button
                className="primary-button"
                onClick={() => goTo("register")}
                type="button"
              >
                Register
              </button>
            </>
          )}
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero-content">
            <div className="announcement">
              ✨ AI-powered academic assessment
            </div>

            <h1>
              Smarter Question Papers.
              <br />
              <span>Better Learning.</span>
            </h1>

            <p className="hero-description">
              Create syllabus-centric question papers with the power of AI.
              Save teachers' time, maintain syllabus alignment, and design
              balanced assessments with ease.
            </p>

            <div className="hero-actions">
              <button
                className="primary-button hero-button"
                onClick={() => goTo("register")}
                type="button"
              >
                Get Started Free <span>→</span>
              </button>
              <button
                className="secondary-button hero-button"
                onClick={() => {
                  document
                    .getElementById("how-it-works")
                    ?.scrollIntoView({ behavior: "smooth" });
                }}
                type="button"
              >
                Explore How It Works
              </button>
            </div>

            <div className="hero-note">
              <span>✓</span> Syllabus-focused
              <span>✓</span> Teacher-friendly
              <span>✓</span> AI-assisted
            </div>
          </div>

          <div className="hero-visual">
            <div className="decor-circle circle-one" />
            <div className="decor-circle circle-two" />

            <div className="paper-card">
              <div className="paper-top">
                <div className="paper-icon">▤</div>
                <span className="status-label">PAPER PREVIEW</span>
              </div>

              <h3>Question Paper</h3>
              <p className="paper-subtitle">
                Computer Science · Sample Preview
              </p>

              <div className="paper-divider" />

              <div className="paper-meta">
                <span>Total Questions</span>
                <strong>Sample</strong>
              </div>
              <div className="paper-meta">
                <span>Syllabus Coverage</span>
                <strong>Unit-wise</strong>
              </div>
              <div className="paper-meta">
                <span>Difficulty</span>
                <strong>Balanced</strong>
              </div>

              <div className="sample-question">
                <span>01</span>
                <div>
                  <strong>Short Answer Question</strong>
                  <p>Explain the key concepts of the selected unit.</p>
                </div>
              </div>

              <div className="sample-question">
                <span>02</span>
                <div>
                  <strong>Application-Based Question</strong>
                  <p>Apply your knowledge to solve a given problem.</p>
                </div>
              </div>

              <div className="paper-footer">
                <span>✦ AI-assisted workflow</span>
                <span>PDF-ready design</span>
              </div>
            </div>

            <div className="floating-card">
              <span className="floating-icon">✦</span>
              <div>
                <strong>AI-assisted</strong>
                <p>Question generation</p>
              </div>
            </div>
          </div>
        </section>

        <section className="trust-strip">
          <span>DESIGNED FOR MODERN EDUCATION</span>
          <div>
            <span>▤ Syllabus Centric</span>
            <span>✦ AI Assisted</span>
            <span>◎ Learning Focused</span>
          </div>
        </section>

        <section className="features section" id="features">
          <div className="section-heading">
            <span className="eyebrow">WHAT MAKES BLINDPAPER DIFFERENT</span>
            <h2>Everything you need to build better assessments</h2>
            <p>
              A structured workflow that helps educators create meaningful,
              syllabus-aligned question papers.
            </p>
          </div>

          <div className="feature-grid">
            <Feature
              icon="📚"
              title="Syllabus-Centric"
              description="Use the uploaded syllabus as the foundation for creating relevant questions across selected units."
            />
            <Feature
              icon="✦"
              title="AI-Assisted Generation"
              description="Generate question suggestions with AI to reduce repetitive manual work for teachers."
            />
            <Feature
              icon="🎯"
              title="Bloom's Taxonomy"
              description="Organize questions by cognitive levels to support a variety of learning objectives."
            />
            <Feature
              icon="✓"
              title="Review and Validation"
              description="Review generated questions and check syllabus coverage before finalizing a paper."
            />
          </div>
        </section>

        <section className="workflow-section section" id="how-it-works">
          <div className="section-heading">
            <span className="eyebrow">SIMPLE WORKFLOW</span>
            <h2>From syllabus to question paper</h2>
            <p>Three simple steps to begin your paper creation workflow.</p>
          </div>

          <div className="workflow-grid">
            <Workflow
              number="01"
              title="Upload Your Syllabus"
              description="Provide the course syllabus PDF to establish the topics for your paper."
            />
            <Workflow
              number="02"
              title="Configure Your Paper"
              description="Select units, marks, difficulty, and question distribution."
            />
            <Workflow
              number="03"
              title="Generate and Review"
              description="Review AI-generated questions, validate coverage, and prepare your paper for export."
            />
          </div>
        </section>

        <section className="about-section" id="about">
          <div>
            <span className="eyebrow">OUR PURPOSE</span>
            <h2>Helping educators focus on teaching, not paperwork.</h2>
            <p>
              BlindPaper is an AI-driven, syllabus-centric question paper
              generation system designed to support teachers in preparing
              structured academic assessments efficiently.
            </p>
          </div>
          <button
            className="primary-button hero-button"
            onClick={() => goTo("register")}
            type="button"
          >
            Get Started <span>→</span>
          </button>
        </section>

        <section className="final-cta">
          <span className="eyebrow">READY TO GET STARTED?</span>
          <h2>Make question paper creation simpler.</h2>
          <p>Explore a smarter workflow for academic assessment.</p>
          <button
            className="primary-button hero-button"
            onClick={() => goTo("register")}
            type="button"
          >
            Create Your Account →
          </button>
        </section>
      </main>

      <footer className="footer">
        <button
          className="brand footer-brand"
          onClick={() => goTo("home")}
          type="button"
        >
          <span className="brand-mark">B</span>
          <span className="brand-name">BlindPaper</span>
        </button>
        <p>AI-driven question paper generation for modern education.</p>
        <span>© {new Date().getFullYear()} BlindPaper</span>
      </footer>
    </div>
  );
}

function Feature({ icon, title, description }) {
  return (
    <article className="feature-card">
      <div className="feature-icon">{icon}</div>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}

function Workflow({ number, title, description }) {
  return (
    <article className="workflow-card">
      <span className="workflow-number">{number}</span>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}

export default App;
