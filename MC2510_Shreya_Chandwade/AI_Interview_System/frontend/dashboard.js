let trendChart = null;
let currentReportData = null;

// Initialize Dashboard
async function loadDashboard() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
        return;
    }

    // Set User Greeting
    const userStr = localStorage.getItem("user");
    if (userStr) {
        try {
            const user = JSON.parse(userStr);
            if (user && user.name) {
                document.getElementById("userName").textContent = user.name;
            }
        } catch (e) {
            console.error("Error parsing user info:", e);
        }
    }

    try {
        const response = await fetch("/dashboard-data", {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem("access_token");
                localStorage.removeItem("user");
                window.location.href = "/login";
                return;
            }
            throw new Error("Unable to load dashboard.");
        }

        const data = await response.json();

        // Update Stats
        document.getElementById("totalInterviews").textContent = data.total_interviews || 0;
        document.getElementById("averageScore").textContent = data.total_interviews ? `${Math.round(data.average_score || 0)}%` : "—";
        const questionsCompleted = document.getElementById("questionsCompleted");
        if (questionsCompleted) questionsCompleted.textContent = data.questions_completed || 0;
        const skillLevel = document.getElementById("skillLevel");
        if (skillLevel) skillLevel.textContent = App.skillLabel(data.average_score || 0, data.total_interviews || 0);
        renderSkillProgress(data.skill_scores || []);
        renderNextSteps(data);
        
        const historyCountTag = document.getElementById("historyCountTag");
        if (historyCountTag) {
            historyCountTag.textContent = `${data.total_interviews || 0} Sessions`;
        }

        // Update Latest Status Badge
        const latestBadge = document.getElementById("latestRecommendationBadge");
        if (data.interviews && data.interviews.length > 0) {
            const latest = data.interviews[0];
            const scoreVal = Math.round(latest.score);
            let statusText = "RECOMMENDED";
            let badgeClass = "rec-badge-emerald";

            if (scoreVal >= 85) {
                statusText = "STRONG HIRE";
                badgeClass = "rec-badge-emerald";
            } else if (scoreVal >= 70) {
                statusText = "RECOMMENDED";
                badgeClass = "rec-badge-green";
            } else if (scoreVal >= 55) {
                statusText = "CONSIDER";
                badgeClass = "rec-badge-amber";
            } else {
                statusText = "NEEDS PRACTICE";
                badgeClass = "rec-badge-rose";
            }

            latestBadge.className = `rec-badge ${badgeClass}`;
            latestBadge.textContent = statusText;
        } else {
            latestBadge.className = "rec-badge rec-badge-neutral";
            latestBadge.textContent = "N/A";
        }

        const historyContainer = document.getElementById("history");
        const historyPlaceholder = document.getElementById("historyPlaceholder");
        const chartWrapper = document.getElementById("chartWrapper");
        const chartPlaceholder = document.getElementById("chartPlaceholder");

        historyContainer.innerHTML = "";

        if (!data.interviews || data.interviews.length === 0) {
            historyPlaceholder.classList.remove("hidden");
            chartWrapper.classList.add("hidden");
            chartPlaceholder.classList.remove("hidden");
            return;
        }

        historyPlaceholder.classList.add("hidden");
        chartWrapper.classList.remove("hidden");
        chartPlaceholder.classList.add("hidden");

        // Build Modern Table for History
        let tableHTML = `
            <table class="history-table">
                <thead>
                    <tr>
                        <th>Job Role & Skills</th>
                        <th>Mode</th>
                        <th>Rounds</th>
                        <th>Date</th>
                        <th>Score</th>
                        <th>Status</th>
                        <th>Report Action</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.interviews.forEach(interview => {
            const scoreVal = Math.round(interview.score);
            let badgeClass = "badge-rose";
            let statusLabel = "Needs Practice";

            if (scoreVal >= 85) {
                badgeClass = "badge-emerald";
                statusLabel = "Strong Hire";
            } else if (scoreVal >= 70) {
                badgeClass = "badge-green";
                statusLabel = "Recommended";
            } else if (scoreVal >= 55) {
                badgeClass = "badge-amber";
                statusLabel = "Consider";
            }

            tableHTML += `
                <tr>
                    <td>
                        <div class="table-role-cell">
                            <strong>${escapeHTML(interview.job_role)}</strong>
                            <small>${escapeHTML(interview.skills || 'General Technical')}</small>
                        </div>
                    </td>
                    <td><span class="mode-pill">${escapeHTML(interview.interview_mode || 'text')}</span></td>
                    <td>${interview.total_rounds || 3} Rounds</td>
                    <td><small style="color: var(--text-muted);">${interview.date}</small></td>
                    <td>
                        <div class="history-score-cell">
                            <span class="score-pill ${badgeClass}">${scoreVal}%</span>
                            <div class="history-score-track"><div class="history-score-fill ${badgeClass}" style="width: ${Math.max(0, Math.min(100, scoreVal))}%"></div></div>
                        </div>
                    </td>
                    <td><span class="status-pill ${badgeClass}">${statusLabel}</span></td>
                    <td>
                        <button class="btn-table-action" onclick="viewInterviewDetails(${interview.id})">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                            View Report
                        </button>
                    </td>
                </tr>
            `;
        });

        tableHTML += `
                </tbody>
            </table>
        `;

        historyContainer.innerHTML = tableHTML;

        // Setup Score Trend Chart (Chronological order)
        const sortedInterviews = [...data.interviews].reverse();
        const labels = sortedInterviews.map((item, idx) => `Session #${idx + 1}`);
        const scores = sortedInterviews.map(item => item.score);

        renderTrendChart(labels, scores);

    } catch (error) {
        console.error("Dashboard error:", error);
        if (window.App) App.toast(error.message || "Unable to load dashboard.", "error");
    }
}

function renderSkillProgress(skillScores) {
    const container = document.getElementById("skillProgress");
    if (!container) return;
    if (!skillScores.length) {
        container.innerHTML = `<div class="empty">Skill scores appear after you save an interview that includes skills.</div>`;
        return;
    }
    container.innerHTML = skillScores.map((item) => `
        <div>
            <div class="history-score-cell">
                <strong>${escapeHTML(item.skill)}</strong>
                <span>${Math.round(item.average)}% · ${item.count} session${item.count === 1 ? "" : "s"}</span>
            </div>
            <div class="progress" aria-hidden="true"><span style="width:${Math.max(0, Math.min(100, item.average))}%"></span></div>
        </div>
    `).join("");
}

function renderNextSteps(data) {
    const container = document.getElementById("nextSteps");
    if (!container) return;
    if (!data.total_interviews) {
        container.innerHTML = `<div class="empty">Complete a mock interview to get next steps from your scores.</div>`;
        return;
    }
    const weak = (data.skill_scores || []).filter((item) => item.average < 70).slice(0, 3);
    const latest = data.interviews[0];
    const items = [];
    if (latest) {
        items.push(`<a class="list-item" href="/feedback?id=${latest.id}"><span>Review feedback for ${escapeHTML(latest.job_role)}</span><strong>${Math.round(latest.score)}%</strong></a>`);
    }
    weak.forEach((item) => {
        items.push(`<div class="list-item"><span>Practice ${escapeHTML(item.skill)}</span><strong>${Math.round(item.average)}%</strong></div>`);
    });
    if (!weak.length) {
        items.push(`<div class="list-item"><span>Saved skill averages are at or above 70%.</span><strong>Keep practicing</strong></div>`);
    }
    items.push(`<a class="list-item" href="/interview"><span>Start another interview</span><strong>Go</strong></a>`);
    container.innerHTML = items.join("");
}


// Render the Chart.js Line Chart
function renderTrendChart(labels, dataPoints) {
    const canvas = document.getElementById("scoreTrendChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    if (trendChart) {
        trendChart.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, "rgba(124, 92, 252, 0.35)");
    gradient.addColorStop(1, "rgba(124, 92, 252, 0.0)");

    trendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Performance Score (%)",
                data: dataPoints,
                borderColor: "#22D3EE",
                borderWidth: 3,
                backgroundColor: gradient,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: "#7C5CFC",
                pointBorderColor: "#ffffff",
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#0f172a",
                    titleFont: { family: "Outfit", size: 13, weight: "bold" },
                    bodyFont: { family: "Plus Jakarta Sans", size: 12 },
                    borderColor: "rgba(148, 163, 184, 0.2)",
                    borderWidth: 1,
                    padding: 10,
                    callbacks: {
                        label: function(context) {
                            return ` Score: ${context.parsed.y}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.04)" },
                    ticks: { color: "#94a3b8", font: { family: "Plus Jakarta Sans", size: 11 } }
                },
                y: {
                    min: 0,
                    max: 100,
                    grid: { color: "rgba(255, 255, 255, 0.04)" },
                    ticks: { color: "#94a3b8", font: { family: "Plus Jakarta Sans", size: 11 }, stepSize: 20 }
                }
            }
        }
    });
}

// Modal Toggle
function toggleDetailsModal(show) {
    const modal = document.getElementById("detailsModal");
    if (!modal) return;
    modal.classList.toggle("hidden", !show);
    document.body.style.overflow = show ? "hidden" : "";
}

// View Comprehensive Interview Report Modal
async function viewInterviewDetails(id) {
    const token = localStorage.getItem("access_token");
    const modalBody = document.getElementById("modalBody");
    const modalTitle = document.getElementById("modalTitle");
    const modalSubtitle = document.getElementById("modalRoleSubtitle");

    modalTitle.textContent = "Generating RAG Interview Report...";
    if (modalSubtitle) modalSubtitle.textContent = "AI Analysis Engine";

    modalBody.innerHTML = `
        <div style="padding: 40px; text-align: center;">
            <div class="skeleton" style="height: 80px; border-radius: 12px; margin-bottom: 20px;"></div>
            <div class="skeleton" style="height: 140px; border-radius: 12px; margin-bottom: 20px;"></div>
            <div class="skeleton" style="height: 200px; border-radius: 12px;"></div>
        </div>
    `;

    toggleDetailsModal(true);

    try {
        const response = await fetch(`/interview/${id}`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error("Failed to retrieve interview report.");
        }

        const data = await response.json();
        currentReportData = data;

        modalTitle.textContent = `Evaluation Report: ${data.job_role}`;
        if (modalSubtitle) modalSubtitle.textContent = `Completed ${data.date}`;

        const report = data.report || {};
        const overallScore = Math.round(report.overall_score || data.overall_score || 0);
        const grade = report.grade || "B";
        const recommendation = report.recommendation || "RECOMMENDED";
        const recReason = report.recommendation_reason || "Candidate completed all evaluation rounds.";
        const strongAreas = report.strong_areas || ["Demonstrated good technical attempt."];
        const weakAreas = report.weak_areas || ["Continue practicing domain concepts."];
        const categoryScores = report.category_scores || { technical: overallScore, coding: overallScore, hr_behavioral: overallScore, communication: overallScore };
        const keyRecommendations = report.key_recommendations || ["Review core concepts and practice timed coding problems."];

        // Determine Recommendation Class
        let recClass = "hero-rec-green";
        if (recommendation.includes("STRONG")) recClass = "hero-rec-emerald";
        else if (recommendation.includes("CONSIDER")) recClass = "hero-rec-amber";
        else if (recommendation.includes("NEEDS")) recClass = "hero-rec-rose";

        // Render Strong Areas Chips
        const strongHTML = strongAreas.map(item => `
            <div class="area-chip area-chip-strong">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                <span>${escapeHTML(item)}</span>
            </div>
        `).join("");

        // Render Weak Areas Chips
        const weakHTML = weakAreas.map(item => `
            <div class="area-chip area-chip-weak">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <span>${escapeHTML(item)}</span>
            </div>
        `).join("");

        // Key recommendations
        const recListHTML = keyRecommendations.map(rec => `
            <li style="margin-bottom: 8px; font-size: 14px; color: var(--text-main);">
                <strong style="color: var(--accent-primary);">•</strong> ${escapeHTML(rec)}
            </li>
        `).join("");

        // Render Question Breakdown Accordion
        let questionsHTML = "";
        data.answers.forEach((ans, index) => {
            const ansScore = Math.round(ans.score);
            let ansScoreClass = "badge-rose";
            if (ansScore >= 80) ansScoreClass = "badge-emerald";
            else if (ansScore >= 60) ansScoreClass = "badge-amber";

            let sentimentHTML = "";
            if (ans.sentiment_label) {
                sentimentHTML = `
                    <div class="sentiment-pill-group">
                        <span class="sentiment-tag">${ans.sentiment_label} Tone</span>
                        <span class="confidence-tag">${ans.confidence_score || 0}% Confidence</span>
                    </div>
                `;
            }

            questionsHTML += `
                <div class="report-question-card">
                    <div class="q-card-header">
                        <div class="q-title-group">
                            <span class="round-number-badge">Round ${ans.round || 1} • ${escapeHTML(ans.question_type || 'Text')}</span>
                            <h4>Q${index + 1}: ${escapeHTML(ans.question)}</h4>
                        </div>
                        <span class="score-pill ${ansScoreClass}">${ansScore}%</span>
                    </div>

                    ${sentimentHTML}

                    <div class="cand-ans-block">
                        <span class="ans-label">Candidate Submission:</span>
                        <div class="ans-content">${escapeHTML(ans.answer)}</div>
                    </div>

                    <div class="eval-result-block">
                        <span class="ans-label">AI Evaluation & Feedback:</span>
                        <div class="eval-content">${escapeHTML(ans.evaluation)}</div>
                    </div>
                </div>
            `;
        });

        // Assemble Full Report Markup
        modalBody.innerHTML = `
            <!-- Hero Summary Container -->
            <div class="report-hero-card ${recClass}">
                <div class="hero-score-column">
                    <div class="score-circle-outer">
                        <div class="score-circle-inner">
                            <span class="score-number">${overallScore}%</span>
                            <span class="score-grade">Grade ${grade}</span>
                        </div>
                    </div>
                </div>
                <div class="hero-info-column">
                    <div class="rec-banner-tag">${recommendation}</div>
                    <h3 class="rec-headline">Candidate Assessment Verdict</h3>
                    <p class="rec-reasoning">${escapeHTML(recReason)}</p>
                    <div class="hero-meta-row">
                        <span>Role: <strong>${escapeHTML(data.job_role)}</strong></span>
                        <span>Mode: <strong>${escapeHTML(data.interview_mode || 'text')}</strong></span>
                        <span>RAG Knowledge Retrieval: <strong style="color: var(--success);">Active</strong></span>
                    </div>
                </div>
            </div>

            <!-- Two-Column Grid: Strong vs Weak Areas -->
            <div class="report-grid-two">
                <!-- Strong Areas Card -->
                <div class="areas-card areas-card-strong">
                    <div class="areas-card-header">
                        <h3>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
                            Strong Areas & Competencies
                        </h3>
                    </div>
                    <div class="chips-container">
                        ${strongHTML}
                    </div>
                </div>

                <!-- Weak Areas Card -->
                <div class="areas-card areas-card-weak">
                    <div class="areas-card-header">
                        <h3>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                            Areas Needing Improvement
                        </h3>
                    </div>
                    <div class="chips-container">
                        ${weakHTML}
                    </div>
                </div>
            </div>

            <!-- Competency Breakdown Progress Bars -->
            <div class="competency-section card">
                <h3>Competency & Skill Domain Breakdown</h3>
                <div class="competency-grid">
                    <div class="comp-item">
                        <div class="comp-label-row">
                            <span>Technical Knowledge</span>
                            <strong>${Math.round(categoryScores.technical || overallScore)}%</strong>
                        </div>
                        <div class="comp-bar-track">
                            <div class="comp-bar-fill" style="width: ${Math.round(categoryScores.technical || overallScore)}%; background: var(--accent-primary);"></div>
                        </div>
                    </div>

                    <div class="comp-item">
                        <div class="comp-label-row">
                            <span>Coding & Problem Solving</span>
                            <strong>${Math.round(categoryScores.coding || overallScore)}%</strong>
                        </div>
                        <div class="comp-bar-track">
                            <div class="comp-bar-fill" style="width: ${Math.round(categoryScores.coding || overallScore)}%; background: var(--coding-accent);"></div>
                        </div>
                    </div>

                    <div class="comp-item">
                        <div class="comp-label-row">
                            <span>HR & Behavioral Fit</span>
                            <strong>${Math.round(categoryScores.hr_behavioral || overallScore)}%</strong>
                        </div>
                        <div class="comp-bar-track">
                            <div class="comp-bar-fill" style="width: ${Math.round(categoryScores.hr_behavioral || overallScore)}%; background: var(--warning);"></div>
                        </div>
                    </div>

                    <div class="comp-item">
                        <div class="comp-label-row">
                            <span>Communication Tone</span>
                            <strong>${Math.round(categoryScores.communication || overallScore)}%</strong>
                        </div>
                        <div class="comp-bar-track">
                            <div class="comp-bar-fill" style="width: ${Math.round(categoryScores.communication || overallScore)}%; background: var(--success);"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- RAG Actionable Next Steps -->
            <div class="action-steps-card card">
                <h3>💡 RAG-Recommended Improvement Plan</h3>
                <ul style="list-style: none; padding: 0; margin-top: 10px;">
                    ${recListHTML}
                </ul>
            </div>

            <!-- Detailed Per-Question Breakdown -->
            <div class="question-breakdown-section">
                <h3 class="section-title-sub">Round-by-Round Question Breakdown</h3>
                <div class="questions-stack">
                    ${questionsHTML}
                </div>
            </div>
        `;

    } catch (error) {
        modalTitle.textContent = "Error";
        modalBody.innerHTML = `<p style="color: var(--danger); text-align: center; padding: 30px;">${error.message}</p>`;
    }
}

// Generate Personalized Study Plan
async function generateStudyPlan() {
    const token = localStorage.getItem("access_token");
    const studyPlan = document.getElementById("studyPlan");

    studyPlan.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 8px; text-align: left;">
            <p style="color: var(--accent-primary); font-weight: 600;">🤖 RAG engine assembling weak topics and personalized roadmap...</p>
            <div class="skeleton" style="height: 16px; border-radius: 4px; width: 90%;"></div>
            <div class="skeleton" style="height: 16px; border-radius: 4px; width: 75%;"></div>
            <div class="skeleton" style="height: 16px; border-radius: 4px; width: 80%;"></div>
        </div>
    `;

    try {
        const response = await fetch("/study-plan", {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Failed to generate study plan.");
        }

        studyPlan.innerHTML = formatMarkdown(data.study_plan);

    } catch (error) {
        studyPlan.innerHTML = `<p style="color: var(--danger); font-weight: 600;">${error.message}</p>`;
    }
}

// Print Report Functionality
function printReport() {
    window.print();
}

// Basic Markdown Formatter
function formatMarkdown(text) {
    if (!text) return "";
    let escaped = escapeHTML(text);
    let formatted = escaped;

    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/^\s*-\s+(.*?)$/gm, '<li style="margin-left: 20px; color: var(--text-main); margin-bottom: 6px;">$1</li>');
    formatted = formatted.replace(/^\s*###\s+(.*?)$/gm, '<h4 style="margin-top: 14px; margin-bottom: 6px; color: var(--accent-secondary); font-family: Outfit, sans-serif; font-size: 15px;">$1</h4>');
    formatted = formatted.replace(/^\s*##\s+(.*?)$/gm, '<h3 style="margin-top: 18px; margin-bottom: 8px; color: var(--accent-primary); font-family: Outfit, sans-serif; font-size: 16px;">$1</h3>');
    formatted = formatted.replace(/\n/g, '<br>');

    return `<div style="text-align: left; line-height: 1.6;">${formatted}</div>`;
}

// HTML Escaping Utility
function escapeHTML(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Logout Utility
function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "/login";
}

// Trigger initial load
loadDashboard();