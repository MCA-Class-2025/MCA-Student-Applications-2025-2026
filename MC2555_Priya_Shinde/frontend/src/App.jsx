import { useState } from "react";
import axios from "axios";
import "./App.css";
import DataDashboard from "./DataDashboard";

const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000/api";

function App() {
  const [claim, setClaim] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showDashboard, setShowDashboard] = useState(false);

  const examples = [
    "India beat Sri Lanka by 165 runs in the first Test in Galle",
    "Government of India announces new scholarship scheme for students",
    "भारत सरकारने विद्यार्थ्यांसाठी नवीन शिष्यवृत्ती योजना सुरू करण्याची घोषणा केली आहे.",
  ];

  // ============================================================
  // VERIFY NEWS
  // ============================================================

  const verifyNews = async () => {
    if (!claim.trim()) {
      setError("Please enter a news claim before verification.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setShowDashboard(false);

    try {
      const response = await axios.post(`${API_URL}/verify`, {
        claim: claim.trim(),
      });

      setResult(response.data.data);
    } catch (err) {
      console.error("Verification error:", err);

      setError(
        err.response?.data?.error ||
          "Unable to connect to the verification server. Please make sure the backend is running on port 5000."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // HELPERS
  // ============================================================

  const formatPercentage = (value) => {
    if (value === undefined || value === null) {
      return "0.00%";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
      return "0.00%";
    }

    return `${(number <= 1 ? number * 100 : number).toFixed(2)}%`;
  };

  const getNumber = (...values) => {
    for (const value of values) {
      if (
        value !== undefined &&
        value !== null &&
        value !== "" &&
        !Number.isNaN(Number(value))
      ) {
        return Number(value);
      }
    }

    return 0;
  };

  const getVerdict = () => {
    return (
      result?.final_verdict ||
      result?.verdict ||
      result?.fusion?.final_verdict ||
      result?.fusion?.verdict ||
      "Needs Verification"
    );
  };

  const getFusionScore = () => {
    return getNumber(
      result?.fusion_score,
      result?.final_fusion_score,
      result?.final_score,
      result?.fusion?.final_fusion_score,
      result?.fusion?.fusion_score,
      result?.fusion?.final_score
    );
  };

  const getEvidenceScore = () => {
    return getNumber(
      result?.evidence_score,
      result?.fusion?.evidence_score
    );
  };

  const getSupportingCount = () => {
    if (Array.isArray(result?.supporting_evidence)) {
      return result.supporting_evidence.length;
    }

    return getNumber(
      result?.supporting_evidence_count,
      result?.supporting_count,
      result?.fusion?.supporting_evidence_count,
      result?.fusion?.supporting_evidence
    );
  };

  const getRelatedCount = () => {
    if (Array.isArray(result?.related_evidence)) {
      return result.related_evidence.length;
    }

    return getNumber(
      result?.related_evidence_count,
      result?.related_count,
      result?.fusion?.related_evidence_count,
      result?.fusion?.related_evidence
    );
  };

  const getContradictingCount = () => {
    if (Array.isArray(result?.contradicting_evidence)) {
      return result.contradicting_evidence.length;
    }

    return getNumber(
      result?.contradicting_evidence_count,
      result?.contradicting_count,
      result?.fusion?.contradicting_evidence_count,
      result?.fusion?.contradicting_evidence
    );
  };

  const getArticles = () => {
    if (Array.isArray(result?.evidence)) {
      return result.evidence;
    }

    if (Array.isArray(result?.articles)) {
      return result.articles;
    }

    if (Array.isArray(result?.evidence_results)) {
      return result.evidence_results;
    }

    return [];
  };

  const getVerdictType = () => {
    const verdict = getVerdict().toLowerCase();

    if (verdict.includes("fake")) {
      return "fake";
    }

    if (verdict.includes("real")) {
      return "real";
    }

    return "needs";
  };

  const getVerdictDescription = () => {
    const type = getVerdictType();

    if (type === "real") {
      return "The collected evidence and ML prediction indicate that this claim is likely authentic.";
    }

    if (type === "fake") {
      return "The available evidence indicates that this claim is likely false or inconsistent with the collected sources.";
    }

    return "The system found relevant information, but the available evidence is not strong enough for a confident verdict.";
  };

  const getEvidenceLabel = (article) => {
    return (
      article?.evidence_type ||
      article?.evidence_status ||
      "Related Evidence"
    );
  };

  const getEvidenceClass = (article) => {
    const type = getEvidenceLabel(article).toLowerCase();

    if (type.includes("contradict")) {
      return "contradiction";
    }

    if (type.includes("support")) {
      return "support";
    }

    return "related";
  };

  const getArticleScore = (article) => {
    return getNumber(
      article?.final_evidence_percentage,
      article?.final_evidence_score,
      article?.similarity_percentage,
      article?.similarity_score
    );
  };

  const getArticleSource = (article) => {
    if (typeof article?.source === "string") {
      return article.source;
    }

    if (article?.source?.name) {
      return article.source.name;
    }

    if (article?.source?.title) {
      return article.source.title;
    }

    return "News Source";
  };

  const getArticleApi = (article) => {
    return (
      article?.api ||
      article?.api_source ||
      "Real-Time News"
    );
  };

  const getArticleUrl = (article) => {
    return article?.url || article?.link || "";
  };

  const formatDate = (date) => {
    if (!date) {
      return "";
    }

    try {
      const parsed = new Date(date);

      if (Number.isNaN(parsed.getTime())) {
        return String(date);
      }

      return parsed.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
    } catch {
      return String(date);
    }
  };

  const getMatchedComponents = (article) => {
    if (
      Array.isArray(article?.matched_components) &&
      article.matched_components.length > 0
    ) {
      return article.matched_components;
    }

    return [];
  };

  const getArticleReason = (article) => {
    if (
      Array.isArray(article?.support_reasons) &&
      article.support_reasons.length > 0
    ) {
      return article.support_reasons[0];
    }

    if (article?.sports_result_reason) {
      return article.sports_result_reason;
    }

    if (article?.reason) {
      return article.reason;
    }

    return "";
  };

  // ============================================================
  // NEW VERIFICATION
  // ============================================================

  const startNewVerification = () => {
    setResult(null);
    setClaim("");
    setError("");
    setShowDashboard(false);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // ============================================================
  // DASHBOARD
  // ============================================================

  const openDashboard = () => {
    setShowDashboard(true);
    setError("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const openVerification = () => {
    setShowDashboard(false);

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  // ============================================================
  // DATA
  // ============================================================

  const verdict = getVerdict();
  const verdictType = getVerdictType();
  const articles = getArticles();
  const fusionScore = getFusionScore();
  const evidenceScore = getEvidenceScore();

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="app">

      {/* ========================================================
          NAVBAR
      ======================================================== */}

      <nav className="navbar">

        <div className="logo-area">

          <div className="logo-mark">
            <span>✓</span>
          </div>

          <div className="logo-text">
            <h1>NewsVerify</h1>
            <p>AI Verification Engine</p>
          </div>

        </div>


        {/* ======================================================
            NAVIGATION MODES
        ====================================================== */}

        <div className="nav-dashboard-buttons">

          <button
            type="button"
            className={`nav-mode-btn ${
              !showDashboard ? "active" : ""
            }`}
            onClick={openVerification}
          >
            Verify News
          </button>

          <button
            type="button"
            className={`nav-mode-btn ${
              showDashboard ? "active" : ""
            }`}
            onClick={openDashboard}
          >
            Data Analytics
          </button>

        </div>


        <div className="nav-right">

          <div className="live-status">
            <span className="live-dot"></span>
            Live System
          </div>

          <div className="ai-badge">
            ✦ AI Powered
          </div>

        </div>

      </nav>


      {/* ========================================================
          MAIN
      ======================================================== */}

      <main>

        {/* ======================================================
            DATA ANALYTICS DASHBOARD
        ====================================================== */}

        {showDashboard ? (

          <DataDashboard
            onBack={openVerification}
          />

        ) : (

          <>

            {/* ==================================================
                HERO
            ================================================== */}

            {!result && !loading && (

              <section className="hero-section">

                <div className="hero-grid"></div>

                <div className="hero-glow hero-glow-one"></div>
                <div className="hero-glow hero-glow-two"></div>

                <div className="hero-content">

                  <div className="eyebrow">
                    <span>✦</span>
                    MULTILINGUAL NEWS INTELLIGENCE
                  </div>

                  <h2>
                    Don't just read the news.
                    <br />
                    <span>Verify it.</span>
                  </h2>

                  <p className="hero-description">
                    An AI-powered news verification system combining
                    machine learning, real-time news sources,
                    semantic evidence matching and data fusion.
                  </p>

                  <div className="hero-features">

                    <div className="hero-feature">
                      <span>◈</span>
                      Machine Learning
                    </div>

                    <div className="hero-feature">
                      <span>◉</span>
                      Real-Time Evidence
                    </div>

                    <div className="hero-feature">
                      <span>◇</span>
                      Multilingual
                    </div>

                  </div>

                </div>

              </section>

            )}


            {/* ==================================================
                INPUT SECTION
            ================================================== */}

            {!result && !loading && (

              <section className="verify-wrapper">

                <div className="verify-card">

                  <div className="verify-top">

                    <div>

                      <div className="section-kicker">
                        STEP 01
                      </div>

                      <h3>
                        Enter a news claim
                      </h3>

                      <p>
                        Paste any statement, headline or news claim
                        you want the system to verify.
                      </p>

                    </div>


                    <div className="language-pill">

                      <span>◎</span>

                      English • हिंदी • मराठी

                    </div>

                  </div>


                  <div className="input-wrapper">

                    <textarea
                      value={claim}
                      onChange={(e) => {
                        setClaim(e.target.value);

                        if (error) {
                          setError("");
                        }
                      }}
                      placeholder="Example: India beat Sri Lanka by 165 runs in the first Test in Galle"
                      disabled={loading}
                    />

                    <div className="input-footer">

                      <span>
                        {claim.length} characters
                      </span>

                      <span>
                        English • Hindi • Marathi supported
                      </span>

                    </div>

                  </div>


                  {error && (

                    <div className="error-box">

                      <span>!</span>

                      <div>

                        <strong>
                          Verification Error
                        </strong>

                        <p>
                          {error}
                        </p>

                      </div>

                    </div>

                  )}


                  <button
                    type="button"
                    className="verify-btn"
                    onClick={verifyNews}
                    disabled={loading}
                  >

                    {loading ? (

                      <>
                        <span className="loader"></span>
                        Analyzing claim...
                      </>

                    ) : (

                      <>
                        Verify News
                        <span className="arrow">→</span>
                      </>

                    )}

                  </button>


                  <div className="example-area">

                    <span className="example-label">
                      Try an example
                    </span>

                    <div className="example-buttons">

                      {examples.map((example, index) => (

                        <button
                          type="button"
                          key={index}
                          onClick={() => setClaim(example)}
                          disabled={loading}
                        >

                          {example.length > 55
                            ? `${example.substring(0, 55)}...`
                            : example}

                        </button>

                      ))}

                    </div>

                  </div>

                </div>

              </section>

            )}


            {/* ==================================================
                HOW IT WORKS
            ================================================== */}

            {!result && !loading && (

              <section className="process-section">

                <div className="section-heading-center">

                  <div className="section-kicker">
                    HOW IT WORKS
                  </div>

                  <h2>
                    From claim to verified evidence
                  </h2>

                  <p>
                    Four intelligent stages work together to evaluate
                    the credibility of a news claim.
                  </p>

                </div>


                <div className="process-grid">

                  <div className="process-card">

                    <div className="process-number">
                      01
                    </div>

                    <div className="process-icon">
                      ◈
                    </div>

                    <h3>
                      ML Prediction
                    </h3>

                    <p>
                      The trained machine learning model evaluates
                      the initial likelihood of the claim being
                      real or fake.
                    </p>

                  </div>


                  <div className="process-card">

                    <div className="process-number">
                      02
                    </div>

                    <div className="process-icon">
                      ◉
                    </div>

                    <h3>
                      Real-Time Search
                    </h3>

                    <p>
                      Multiple news APIs search current sources
                      for relevant information related to the claim.
                    </p>

                  </div>


                  <div className="process-card">

                    <div className="process-number">
                      03
                    </div>

                    <div className="process-icon">
                      ◎
                    </div>

                    <h3>
                      Evidence Matching
                    </h3>

                    <p>
                      Semantic similarity and claim components
                      are compared against collected articles.
                    </p>

                  </div>


                  <div className="process-card">

                    <div className="process-number">
                      04
                    </div>

                    <div className="process-icon">
                      ✦
                    </div>

                    <h3>
                      Data Fusion
                    </h3>

                    <p>
                      ML confidence and evidence signals are combined
                      to produce the final verification verdict.
                    </p>

                  </div>

                </div>

              </section>

            )}


            {/* ==================================================
                LOADING
            ================================================== */}

            {loading && (

              <section className="loading-section">

                <div className="loading-card">

                  <div className="analysis-animation">

                    <div className="analysis-ring"></div>

                    <div className="analysis-core">
                      AI
                    </div>

                  </div>


                  <div className="loading-content">

                    <div className="section-kicker">
                      LIVE ANALYSIS
                    </div>

                    <h2>
                      Verifying your claim
                    </h2>

                    <p>
                      The system is searching real-time news sources
                      and matching evidence.
                    </p>


                    <div className="analysis-steps">

                      <div className="analysis-step active">

                        <span>✓</span>

                        <div>

                          <strong>
                            Claim Analysis
                          </strong>

                          <small>
                            Detecting language and claim structure
                          </small>

                        </div>

                      </div>


                      <div className="analysis-step active">

                        <span>✓</span>

                        <div>

                          <strong>
                            ML Prediction
                          </strong>

                          <small>
                            Running the trained classifier
                          </small>

                        </div>

                      </div>


                      <div className="analysis-step processing">

                        <span>◌</span>

                        <div>

                          <strong>
                            Real-Time Search
                          </strong>

                          <small>
                            Searching multiple news sources
                          </small>

                        </div>

                      </div>


                      <div className="analysis-step">

                        <span>○</span>

                        <div>

                          <strong>
                            Evidence Matching
                          </strong>

                          <small>
                            Comparing semantic evidence
                          </small>

                        </div>

                      </div>


                      <div className="analysis-step">

                        <span>○</span>

                        <div>

                          <strong>
                            Data Fusion
                          </strong>

                          <small>
                            Calculating final verdict
                          </small>

                        </div>

                      </div>

                    </div>

                  </div>

                </div>

              </section>

            )}


            {/* ==================================================
                RESULTS
            ================================================== */}

            {result && !loading && (

              <section className="results-section">

                {/* ----------------------------------------------
                    RESULT HEADER
                ---------------------------------------------- */}

                <div className="results-header">

                  <div>

                    <div className="section-kicker">
                      STEP 02 • COMPLETE
                    </div>

                    <h2>
                      Verification Result
                    </h2>

                    <p>
                      AI analysis completed using ML prediction
                      and real-time evidence.
                    </p>

                  </div>


                  <button
                    type="button"
                    className="new-check-btn"
                    onClick={startNewVerification}
                  >
                    + New Verification
                  </button>

                </div>


                {/* ----------------------------------------------
                    VERIFIED CLAIM
                ---------------------------------------------- */}

                <div className="claim-box">

                  <div className="claim-label">
                    VERIFIED CLAIM
                  </div>

                  <p>
                    {result.claim || claim}
                  </p>

                </div>


                {/* ----------------------------------------------
                    VERDICT
                ---------------------------------------------- */}

                <div
                  className={`verdict-panel ${verdictType}`}
                >

                  <div className="verdict-main">

                    <div className="verdict-icon">

                      {verdictType === "real"
                        ? "✓"
                        : verdictType === "fake"
                        ? "!"
                        : "?"}

                    </div>


                    <div className="verdict-copy">

                      <span>
                        FINAL VERDICT
                      </span>

                      <h2>
                        {verdict}
                      </h2>

                      <p>
                        {getVerdictDescription()}
                      </p>

                    </div>

                  </div>


                  <div className="score-circle">

                    <div>

                      <strong>
                        {formatPercentage(fusionScore)}
                      </strong>

                      <span>
                        FUSION SCORE
                      </span>

                    </div>

                  </div>

                </div>


                {/* ----------------------------------------------
                    TRUST SUMMARY
                ---------------------------------------------- */}

                <div className="trust-summary">

                  <div className="trust-item">

                    <span>✓</span>

                    <div>

                      <strong>
                        ML Analysis
                      </strong>

                      <small>
                        Completed
                      </small>

                    </div>

                  </div>


                  <div className="trust-divider"></div>


                  <div className="trust-item">

                    <span>✓</span>

                    <div>

                      <strong>
                        Real-Time Search
                      </strong>

                      <small>
                        {result.articles_found ?? articles.length} articles
                      </small>

                    </div>

                  </div>


                  <div className="trust-divider"></div>


                  <div className="trust-item">

                    <span>✓</span>

                    <div>

                      <strong>
                        Evidence Matching
                      </strong>

                      <small>
                        Completed
                      </small>

                    </div>

                  </div>


                  <div className="trust-divider"></div>


                  <div className="trust-item">

                    <span>✓</span>

                    <div>

                      <strong>
                        Data Fusion
                      </strong>

                      <small>
                        Completed
                      </small>

                    </div>

                  </div>

                </div>


                {/* ----------------------------------------------
                    METRICS
                ---------------------------------------------- */}

                <div className="result-metrics">

                  <div className="result-metric">

                    <span className="metric-icon">
                      ◎
                    </span>

                    <div>

                      <small>
                        LANGUAGE
                      </small>

                      <strong>
                        {result.language || "Unknown"}
                      </strong>

                    </div>

                  </div>


                  <div className="result-metric">

                    <span className="metric-icon">
                      ◈
                    </span>

                    <div>

                      <small>
                        ML PREDICTION
                      </small>

                      <strong>
                        {result.ml_prediction || "Unknown"}
                      </strong>

                    </div>

                  </div>


                  <div className="result-metric">

                    <span className="metric-icon">
                      %
                    </span>

                    <div>

                      <small>
                        ML CONFIDENCE
                      </small>

                      <strong>
                        {formatPercentage(result.ml_confidence)}
                      </strong>

                    </div>

                  </div>


                  <div className="result-metric">

                    <span className="metric-icon">
                      ◇
                    </span>

                    <div>

                      <small>
                        ARTICLES FOUND
                      </small>

                      <strong>
                        {result.articles_found ?? articles.length}
                      </strong>

                    </div>

                  </div>

                </div>


                {/* ----------------------------------------------
                    LLAMA EXPLANATION
                ---------------------------------------------- */}

                {result?.llm_explanation && (

                  <section className="llm-explanation-section">

                    <div className="llm-explanation-header">

                      <div className="llm-icon">
                        🤖
                      </div>

                      <div className="llm-title-block">

                        <span className="section-eyebrow">
                          AI EXPLANATION
                        </span>

                        <h3>
                          Llama 3.2 Analysis
                        </h3>

                      </div>

                      <div className="llm-badge">
                        Llama 3.2
                      </div>

                    </div>


                    <div className="llm-explanation-body">

                      <p>
                        {result.llm_explanation}
                      </p>

                    </div>


                    <div className="llm-explanation-note">

                      This explanation is generated from the verification
                      results produced by the ML model, evidence matcher,
                      and data fusion engine. Llama does not determine or
                      change the final verdict.

                    </div>

                  </section>

                )}


                {/* ----------------------------------------------
                    EVIDENCE OVERVIEW
                ---------------------------------------------- */}

                <div className="evidence-dashboard">

                  <div className="dashboard-heading">

                    <div>

                      <div className="section-kicker">
                        EVIDENCE OVERVIEW
                      </div>

                      <h2>
                        What did the system find?
                      </h2>

                      <p>
                        Evidence collected from multiple real-time
                        news sources and evaluated by the matcher.
                      </p>

                    </div>


                    <div className="evidence-score-box">

                      <span>
                        Evidence Score
                      </span>

                      <strong>
                        {formatPercentage(evidenceScore)}
                      </strong>

                    </div>

                  </div>


                  <div className="evidence-count-grid">

                    <div className="count-card supporting">

                      <div className="count-top">

                        <span>✓</span>
                        SUPPORTING

                      </div>

                      <strong>
                        {getSupportingCount()}
                      </strong>

                      <p>
                        Evidence supporting the claim
                      </p>

                    </div>


                    <div className="count-card related">

                      <div className="count-top">

                        <span>~</span>
                        RELATED

                      </div>

                      <strong>
                        {getRelatedCount()}
                      </strong>

                      <p>
                        Relevant but not conclusive
                      </p>

                    </div>


                    <div className="count-card contradicting">

                      <div className="count-top">

                        <span>!</span>
                        CONTRADICTING

                      </div>

                      <strong>
                        {getContradictingCount()}
                      </strong>

                      <p>
                        Evidence against the claim
                      </p>

                    </div>

                  </div>

                </div>


                {/* ----------------------------------------------
                    SOURCES
                ---------------------------------------------- */}

                <div className="sources-section">

                  <div className="sources-heading">

                    <div>

                      <div className="section-kicker">
                        REAL-TIME SOURCES
                      </div>

                      <h2>
                        Evidence collected
                      </h2>

                      <p>
                        Sources ranked by their relevance to the claim.
                      </p>

                    </div>

                    <span className="source-count">
                      {articles.length} sources
                    </span>

                  </div>


                  <div className="sources-list">

                    {articles.length === 0 ? (

                      <div className="no-evidence">

                        <div className="no-evidence-icon">
                          ◌
                        </div>

                        <h3>
                          No evidence articles available
                        </h3>

                        <p>
                          The news sources did not return usable
                          evidence for this claim.
                        </p>

                      </div>

                    ) : (

                      articles.slice(0, 10).map((article, index) => {

                        const evidenceType =
                          getEvidenceLabel(article);

                        const evidenceClass =
                          getEvidenceClass(article);

                        const articleScore =
                          getArticleScore(article);

                        const matchedComponents =
                          getMatchedComponents(article);

                        const reason =
                          getArticleReason(article);

                        const articleUrl =
                          getArticleUrl(article);

                        const publishedDate =
                          article?.publishedAt ||
                          article?.published_at ||
                          article?.published;

                        return (

                          <article
                            className={`source-card ${evidenceClass}`}
                            key={`${articleUrl}-${index}`}
                          >

                            <div className="source-index">
                              {String(index + 1).padStart(2, "0")}
                            </div>


                            <div className="source-content">

                              <div className="source-top">

                                <span className="source-api">
                                  {getArticleApi(article)}
                                </span>

                                <span
                                  className={`evidence-tag ${evidenceClass}`}
                                >
                                  {evidenceType}
                                </span>

                              </div>


                              <h3>
                                {article?.title || "News Article"}
                              </h3>


                              <div className="source-meta">

                                <span>
                                  {getArticleSource(article)}
                                </span>

                                {publishedDate && (
                                  <>
                                    <span className="meta-dot">
                                      •
                                    </span>

                                    <span>
                                      {formatDate(publishedDate)}
                                    </span>
                                  </>
                                )}

                                {articleScore > 0 && (
                                  <>
                                    <span className="meta-dot">
                                      •
                                    </span>

                                    <span>
                                      Evidence{" "}
                                      {formatPercentage(articleScore)}
                                    </span>
                                  </>
                                )}

                              </div>


                              {matchedComponents.length > 0 && (

                                <div className="match-row">

                                  <span className="match-label">
                                    MATCHED
                                  </span>

                                  <div className="component-list">

                                    {matchedComponents
                                      .slice(0, 6)
                                      .map(
                                        (
                                          component,
                                          componentIndex
                                        ) => (

                                          <span
                                            key={componentIndex}
                                          >
                                            {String(component).replace(
                                              /_/g,
                                              " "
                                            )}
                                          </span>

                                        )
                                      )}

                                  </div>

                                </div>

                              )}


                              {reason && (

                                <div className="evidence-reason">

                                  <span>

                                    {evidenceClass === "support"
                                      ? "✓"
                                      : evidenceClass === "contradiction"
                                      ? "!"
                                      : "i"}

                                  </span>

                                  <p>
                                    {reason}
                                  </p>

                                </div>

                              )}


                              <div className="source-footer">

                                <span className="source-verified">

                                  <span>
                                    ✓
                                  </span>

                                  AI Evidence Analysis

                                </span>


                                {articleUrl ? (

                                  <a
                                    href={articleUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="read-source"
                                  >
                                    Read Source
                                    <span>↗</span>
                                  </a>

                                ) : (

                                  <span className="read-source disabled">
                                    Source unavailable
                                  </span>

                                )}

                              </div>

                            </div>

                          </article>

                        );

                      })

                    )}

                  </div>


                  {articles.length > 10 && (

                    <div className="more-sources">

                      Showing the top 10 most relevant sources
                      from {articles.length} collected articles.

                    </div>

                  )}

                </div>

              </section>

            )}

          </>

        )}

      </main>


      {/* ========================================================
          FOOTER
      ======================================================== */}

      <footer className="footer">

        <div className="footer-inner">

          <div className="footer-brand">

            <div className="footer-mark">
              ✓
            </div>

            <div>

              <strong>
                NewsVerify AI
              </strong>

              <span>
                Multilingual News Verification
              </span>

            </div>

          </div>


          <div className="footer-tech">

            <span>
              Machine Learning
            </span>

            <span>
              Semantic AI
            </span>

            <span>
              Real-Time Evidence
            </span>

            <span>
              Data Fusion
            </span>

          </div>


          <p>
            MCA Research Project • AI-powered news credibility analysis
          </p>

        </div>

      </footer>

    </div>
  );
}

export default App;