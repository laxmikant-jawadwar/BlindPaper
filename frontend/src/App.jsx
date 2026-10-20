import { useEffect, useState } from "react";
import "./App.css";
import { getHealthStatus } from "./api";
import { Navbar } from "./components/Navbar";
import { FacultyDashboard } from "./components/FacultyDashboard";
import { CreatePaperChoice } from "./components/CreatePaperChoice";
import { UploadSyllabus } from "./components/UploadSyllabus";
import { SyllabusReview } from "./components/SyllabusReview";
import { PaperConfig } from "./components/PaperConfig";
import { QuestionReview } from "./components/QuestionReview";
import { PaperPreview } from "./components/PaperPreview";

function App() {
  const [page, setPage] = useState("home");
  const [dbStatus, setDbStatus] = useState("checking");
  const [userSession, setUserSession] = useState(null);

  // Active examination paper session state
  const [selectedSyllabus, setSelectedSyllabus] = useState(null);
  const [paperConfig, setPaperConfig] = useState(null);
  const [generatedQuestions, setGeneratedQuestions] = useState([]);
  const [validationReport, setValidationReport] = useState(null);
  const [generationMeta, setGenerationMeta] = useState({
    mode: "demo",
    message: "",
  });

  // Auth form state
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authName, setAuthName] = useState("");
  const [authError, setAuthError] = useState("");

  // Check backend and MongoDB connection on mount
  useEffect(() => {
    async function checkBackendHealth() {
      try {
        const health = await getHealthStatus();
        setDbStatus(health.database === "connected" ? "connected" : "disconnected");
      } catch {
        setDbStatus("disconnected");
      }
    }
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const goTo = (nextPage) => {
    setPage(nextPage);
    window.scrollTo(0, 0);
  };

  const handleLoginSubmit = (e) => {
    e.preventDefault();
    setAuthError("");

    if (!authEmail.trim() || !authPassword.trim()) {
      setAuthError("Please fill in both email and password.");
      return;
    }

    if (!authEmail.includes("@")) {
      setAuthError("Please enter a valid academic email address.");
      return;
    }

    // Set demo faculty session
    setUserSession({
      name: authName.trim() || "Prof. Faculty",
      email: authEmail.trim(),
      role: "Faculty Member (Demo Session)",
    });

    goTo("faculty_dashboard");
  };

  const handleLogout = () => {
    setUserSession(null);
    goTo("home");
  };

  const handleResetWorkflow = () => {
    setSelectedSyllabus(null);
    setPaperConfig(null);
    setGeneratedQuestions([]);
    setValidationReport(null);
    goTo("faculty_dashboard");
  };

  // -------------------------------------------------------------
  // Render Specific Views
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
            <span>Manage registered faculty and staff members.</span>
          </div>

          <div className="admin-option">
            <strong>📄 Question Papers</strong>
            <span>Review generated examination papers and export logs.</span>
          </div>

          <div className="admin-option">
            <strong>📚 Syllabus Management</strong>
            <span>Inspect courses stored in local MongoDB repository.</span>
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
          <h1>{isLogin ? "Faculty Sign In" : "Register as Faculty"}</h1>
          <p>
            {isLogin
              ? "Sign in to access your Question Paper Studio and syllabus repository."
              : "Create your academic profile to generate AI question papers."}
          </p>

          <div className="demo-session-notice">
            <span>ℹ️ <strong>Demo Faculty Mode:</strong> Enter your email to begin. A faculty session is started with local MongoDB integration enabled.</span>
          </div>

          {authError && (
            <div className="alert-box alert-error">
              <span className="alert-icon">⚠️</span>
              <div className="alert-body">
                <p>{authError}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleLoginSubmit}>
            {!isLogin && (
              <label>
                Full Name & Title
                <input
                  type="text"
                  placeholder="e.g. Dr. A. P. Sharma"
                  value={authName}
                  onChange={(e) => setAuthName(e.target.value)}
                  required
                />
              </label>
            )}

            <label>
              Faculty Email Address
              <input
                type="email"
                placeholder="faculty@university.edu"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                required
              />
            </label>

            <label>
              Password
              <input
                type="password"
                placeholder="Enter password (demo: 6+ characters)"
                minLength={6}
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                required
              />
            </label>

            <button type="submit" className="primary-button full-button">
              {isLogin ? "Sign In to Studio →" : "Register & Start →"}
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
            {isLogin ? "Don't have an account?" : "Already registered?"}
            <button
              type="button"
              onClick={() => {
                setAuthError("");
                goTo(isLogin ? "register" : "login");
              }}
            >
              {isLogin ? " Register as Faculty" : " Sign In"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Application Layout for Authenticated Pages
  return (
    <div className="app-layout">
      <Navbar
        page={page}
        goTo={goTo}
        dbStatus={dbStatus}
        userSession={userSession}
        onLogout={handleLogout}
      />

      <main className="main-content">
        {page === "home" && (
          <LandingPage goTo={goTo} userSession={userSession} />
        )}

        {page === "faculty_dashboard" && (
          <FacultyDashboard
            goTo={goTo}
            dbStatus={dbStatus}
            onSelectSyllabus={(syllabusDoc) => {
              setSelectedSyllabus(syllabusDoc);
            }}
            onEditSyllabusStructure={(syllabusDoc) => {
              setSelectedSyllabus(syllabusDoc);
            }}
          />
        )}

        {page === "create_paper" && (
          <CreatePaperChoice
            goTo={goTo}
            onSelectSyllabus={(syllabusDoc) => {
              setSelectedSyllabus(syllabusDoc);
            }}
          />
        )}

        {page === "upload_syllabus" && (
          <UploadSyllabus
            goTo={goTo}
            onExtractionComplete={(structuredData) => {
              setSelectedSyllabus(structuredData);
            }}
            onSelectExisting={() => goTo("create_paper")}
          />
        )}

        {page === "syllabus_review" && (
          <SyllabusReview
            goTo={goTo}
            syllabusData={selectedSyllabus}
            onSyllabusConfirmed={(confirmedDoc) => {
              setSelectedSyllabus(confirmedDoc);
            }}
          />
        )}

        {page === "paper_config" && (
          <PaperConfig
            goTo={goTo}
            syllabus={selectedSyllabus}
            configState={paperConfig}
            onConfigChange={(newConfig) => {
              setPaperConfig(newConfig);
            }}
            onGenerationComplete={({
              questions,
              generationMode,
              generationMessage,
              validationReport: vReport,
            }) => {
              setGeneratedQuestions(questions);
              setGenerationMeta({
                mode: generationMode,
                message: generationMessage,
              });
              setValidationReport(vReport);
            }}
          />
        )}

        {page === "question_review" && (
          <QuestionReview
            goTo={goTo}
            syllabus={selectedSyllabus}
            config={paperConfig}
            questions={generatedQuestions}
            generationMode={generationMeta.mode}
            generationMessage={generationMeta.message}
            initialValidationReport={validationReport}
            onQuestionsUpdated={(updatedQuestions) => {
              setGeneratedQuestions(updatedQuestions);
            }}
          />
        )}

        {page === "paper_preview" && (
          <PaperPreview
            goTo={goTo}
            config={paperConfig}
            questions={generatedQuestions}
            onResetWorkflow={handleResetWorkflow}
          />
        )}
      </main>

      {page === "home" && (
        <footer className="footer">
          <button
            className="brand footer-brand"
            onClick={() => goTo("home")}
            type="button"
          >
            <span className="brand-mark">B</span>
            <span className="brand-name">BlindPaper</span>
          </button>
          <p>
            AI-driven syllabus-centric question paper generation & validation for modern education.
          </p>
          <span>© {new Date().getFullYear()} BlindPaper</span>
        </footer>
      )}
    </div>
  );
}

// -------------------------------------------------------------
// Landing Page Subcomponent
// -------------------------------------------------------------

function LandingPage({ goTo, userSession }) {
  return (
    <div className="landing-page">
      <section className="hero">
        <div className="hero-content">
          <div className="announcement">
            ✨ AI-powered academic assessment & validation
          </div>

          <h1>
            Smarter Question Papers.
            <br />
            <span>Better Learning.</span>
          </h1>

          <p className="hero-description">
            Create syllabus-centric question papers with the power of AI.
            Save teachers' time, maintain strict syllabus alignment, and design
            balanced assessments aligned with Bloom's Taxonomy.
          </p>

          <div className="hero-actions">
            <button
              className="primary-button hero-button"
              onClick={() => goTo(userSession ? "faculty_dashboard" : "login")}
              type="button"
            >
              {userSession ? "Open Question Paper Studio →" : "Get Started (Faculty Login) →"}
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
            <span>✓</span> Bloom's Taxonomy
            <span>✓</span> Local MongoDB
          </div>
        </div>

        <div className="hero-visual">
          <div className="paper-card">
            <div className="paper-header">
              <span className="paper-tag">EXAMINATION PAPER</span>
              <span className="paper-marks">Max Marks: 50</span>
            </div>
            <div className="paper-subject">CS-302: Data Structures</div>
            <div className="paper-line"></div>
            <div className="paper-q">
              <strong>Q1.</strong> Explain the difference between linear and
              non-linear data structures with examples. [5 Marks]
            </div>
            <div className="paper-q">
              <strong>Q2.</strong> Implement a stack using an array and write
              push and pop algorithms. [10 Marks]
            </div>
            <div className="paper-footer-badge">
              ✓ Grounded in Syllabus • Zero Hallucinations
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="section" id="features">
        <span className="eyebrow">FEATURES</span>
        <h2>Built specifically for college educators.</h2>
        <p className="section-description">
          Unlike generic chatbots, BlindPaper enforces syllabus grounding,
          balanced question types, and quality validation.
        </p>

        <div className="feature-grid">
          <Feature
            icon="📄"
            title="Syllabus PDF Extraction"
            description="Upload college syllabus PDFs. Fast PyMuPDF extraction structures content into units, topics, and subtopics."
          />
          <Feature
            icon="🧠"
            title="Bloom's Taxonomy Alignment"
            description="Automatically infers and balances cognitive levels from Remember and Understand up to Apply, Analyze, and Create."
          />
          <Feature
            icon="🔍"
            title="Intelligent Validation Engine"
            description="Detects exact and near-duplicate questions, checks syllabus coverage, and verifies total marks consistency."
          />
          <Feature
            icon="💾"
            title="Local MongoDB Persistence"
            description="Courses and structured syllabi are saved in local MongoDB for instant reuse without re-uploading."
          />
          <Feature
            icon="🎛️"
            title="Faculty Editorial Control"
            description="Faculty inspects, edits, adds, or removes generated questions before approving the final examination paper."
          />
          <Feature
            icon="📥"
            title="Publication-Ready PDF Export"
            description="Download formatted, print-ready question papers generated in memory via ReportLab with college headers and marks."
          />
        </div>
      </section>

      {/* How It Works Section */}
      <section className="section how-it-works" id="how-it-works">
        <span className="eyebrow">WORKFLOW</span>
        <h2>From syllabus PDF to approved question paper in 4 steps.</h2>

        <div className="workflow-grid">
          <Workflow
            number="1"
            title="Upload Course Syllabus"
            description="Provide your syllabus PDF. PyMuPDF extracts text and the engine identifies units and topics."
          />
          <Workflow
            number="2"
            title="Review & Confirm Structure"
            description="Verify topics and Bloom's cognitive suggestions, then persist the syllabus in local MongoDB."
          />
          <Workflow
            number="3"
            title="Configure & Generate"
            description="Select units, specify marks and question formats. The engine generates grounded examination questions."
          />
          <Workflow
            number="4"
            title="Validate & Export PDF"
            description="Run duplicate detection and coverage validation, make faculty edits, and export the final printable PDF."
          />
        </div>
      </section>

      {/* About Section */}
      <section className="about-section" id="about">
        <div>
          <span className="eyebrow">ABOUT BLINDPAPER</span>
          <h2>AI generates questions; BlindPaper validates; Faculty approves.</h2>
          <p>
            BlindPaper ensures that university examinations remain fair,
            rigorous, and strictly aligned with institutional curricula.
          </p>
        </div>
        <button
          className="primary-button hero-button"
          onClick={() => goTo(userSession ? "faculty_dashboard" : "login")}
          type="button"
        >
          Start Creating Papers →
        </button>
      </section>
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
