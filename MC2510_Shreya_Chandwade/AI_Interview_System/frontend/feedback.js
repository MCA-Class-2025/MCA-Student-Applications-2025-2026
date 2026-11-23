function escapeFeedback(value) {
    return App.escape(value);
}

async function authorizedJson(url) {
    const response = await fetch(url, { headers: App.authHeaders() });
    if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
        return null;
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(App.formatDetail(data));
    return data;
}

function listItems(items, emptyText) {
    if (!items || !items.length) return `<p class="muted">${emptyText}</p>`;
    return items.map((item) => `<div class="area-chip"><span>${escapeFeedback(item)}</span></div>`).join("");
}

function renderFeedback(data) {
    const report = data.report || {};
    const scores = (data.answers || []).map((item) => Number(item.score) || 0);
    const answerQuality = scores.length ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length) : null;
    const technical = report.category_scores?.technical;
    const overall = Math.round(report.overall_score ?? data.overall_score ?? 0);
    const practice = [...(data.answers || [])]
        .map((item, index) => ({ ...item, index }))
        .sort((left, right) => (Number(left.score) || 0) - (Number(right.score) || 0))
        .slice(0, 3);

    document.getElementById("feedbackLead").textContent = `${data.job_role} · ${data.date || "Saved interview"}`;
    document.getElementById("feedbackContent").innerHTML = `
        <section class="report-hero">
            <div class="score-circle"><div><span class="score-number">${overall}%</span><span class="score-grade">${escapeFeedback(report.grade || "Score")}</span></div></div>
            <div>
                <span class="kicker">${escapeFeedback(report.recommendation || "Saved evaluation")}</span>
                <h2>Overall performance</h2>
                <p>${escapeFeedback(report.recommendation_reason || "This score is the average stored for the interview.")}</p>
            </div>
        </section>
        <section class="metric-trio">
            <article class="card"><h3>Overall score</h3><p class="kpi">${overall}%</p></article>
            <article class="card"><h3>Answer quality</h3><p class="kpi">${answerQuality === null ? "—" : `${answerQuality}%`}</p><span class="stat-subtext">Average of saved answer scores</span></article>
            <article class="card"><h3>Technical accuracy</h3><p class="kpi">${technical === undefined ? "—" : `${Math.round(technical)}%`}</p><span class="stat-subtext">Technical round average from the report</span></article>
        </section>
        <section class="report-grid-two">
            <article class="card"><h2>Strengths</h2>${listItems(report.strong_areas, "This report did not list strengths.")}</article>
            <article class="card"><h2>Areas for improvement</h2>${listItems(report.weak_areas, "This report did not list improvement areas.")}</article>
        </section>
        <section class="card section">
            <h2>Suggested topics to study</h2>
            ${listItems(report.key_recommendations, "No study topics were returned with this report.")}
            <div class="actions"><a class="btn btn-primary" href="/plan">Open study plan</a></div>
        </section>
        <section class="card section">
            <h2>Recommended practice questions</h2>
            <p class="muted">These are the lowest-scoring questions from this saved interview.</p>
            ${practice.length ? practice.map((item) => `
                <article class="report-question-card">
                    <div class="q-card-header"><h3>Question ${item.index + 1}</h3><span class="score-pill">${Math.round(Number(item.score) || 0)}%</span></div>
                    <p>${escapeFeedback(item.question)}</p>
                </article>
            `).join("") : `<div class="empty">This interview has no stored questions to practice.</div>`}
        </section>
        <div class="actions">
            <a class="btn btn-ghost" href="/analytics">Performance analytics</a>
            <a class="btn btn-primary" href="/dashboard">Return to dashboard</a>
        </div>
    `;
}

async function loadFeedback() {
    const status = document.getElementById("feedbackStatus");
    const content = document.getElementById("feedbackContent");
    try {
        const params = new URLSearchParams(window.location.search);
        let id = params.get("id") || localStorage.getItem("last_interview_id");
        if (!id) {
            const dashboard = await authorizedJson("/dashboard-data");
            if (!dashboard) return;
            id = dashboard.interviews?.[0]?.id;
        }
        if (!id) {
            status.className = "empty";
            status.textContent = "Complete and save a mock interview to see feedback.";
            return;
        }
        const data = await authorizedJson(`/interview/${id}`);
        if (!data) return;
        renderFeedback(data);
        status.classList.add("hidden");
        content.classList.remove("hidden");
    } catch (error) {
        status.className = "empty";
        status.textContent = error.message || "Could not load feedback.";
        App.toast(status.textContent, "error");
    }
}

loadFeedback();
