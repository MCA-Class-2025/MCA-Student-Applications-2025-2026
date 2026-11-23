const chartText = "#A6B3C5";
const chartGrid = "rgba(248, 250, 252, 0.08)";

function baseOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: chartText } } },
        scales: {
            x: { ticks: { color: chartText }, grid: { color: chartGrid } },
            y: { min: 0, max: 100, ticks: { color: chartText }, grid: { color: chartGrid } }
        }
    };
}

function showChart(canvasId, emptyId, hasData) {
    document.getElementById(emptyId).classList.toggle("hidden", hasData);
    document.getElementById(canvasId).parentElement.classList.toggle("hidden", !hasData);
}

async function loadAnalytics() {
    const status = document.getElementById("analyticsStatus");
    try {
        const response = await fetch("/dashboard-data", { headers: App.authHeaders() });
        if (response.status === 401) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("user");
            window.location.href = "/login";
            return;
        }
        const data = await response.json();
        if (!response.ok) throw new Error(App.formatDetail(data));

        const interviews = [...(data.interviews || [])].reverse();
        showChart("timeChart", "timeEmpty", interviews.length > 0);
        if (interviews.length) {
            new Chart(document.getElementById("timeChart"), {
                type: "line",
                data: {
                    labels: interviews.map((item) => item.date || item.job_role),
                    datasets: [{
                        label: "Score",
                        data: interviews.map((item) => item.score),
                        borderColor: "#22D3EE",
                        backgroundColor: "rgba(124, 92, 252, 0.25)",
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: baseOptions()
            });
        }

        const difficulties = (data.difficulty_scores || []).filter((item) => item.difficulty && item.difficulty !== "Not recorded");
        showChart("difficultyChart", "difficultyEmpty", difficulties.length > 0);
        if (difficulties.length) {
            new Chart(document.getElementById("difficultyChart"), {
                type: "bar",
                data: {
                    labels: difficulties.map((item) => item.difficulty),
                    datasets: [{ label: "Average score", data: difficulties.map((item) => item.average), backgroundColor: "#7C5CFC" }]
                },
                options: baseOptions()
            });
        }

        const skills = data.skill_scores || [];
        showChart("skillChart", "skillEmpty", skills.length > 0);
        if (skills.length) {
            new Chart(document.getElementById("skillChart"), {
                type: "bar",
                data: {
                    labels: skills.map((item) => item.skill),
                    datasets: [{ label: "Average score", data: skills.map((item) => item.average), backgroundColor: "#22D3EE" }]
                },
                options: { ...baseOptions(), indexAxis: "y" }
            });
        }

        const recent = document.getElementById("recentResults");
        recent.innerHTML = (data.interviews || []).slice(0, 6).map((item) => `
            <a class="list-item" href="/feedback?id=${item.id}">
                <span>${App.escape(item.job_role)}<br><small>${App.escape(item.date)}</small></span>
                <strong>${Math.round(item.score)}%</strong>
            </a>
        `).join("") || `<div class="empty">No saved interviews yet.</div>`;

        const weak = skills.filter((item) => item.average < 70);
        document.getElementById("improvementAreas").innerHTML = weak.length
            ? weak.map((item) => `<div class="list-item"><span>${App.escape(item.skill)}</span><strong>${Math.round(item.average)}%</strong></div>`).join("")
            : `<div class="empty">${skills.length ? "No saved skill average is below 70%." : "Skill gaps appear after an interview is saved with skills."}</div>`;

        status.classList.add("hidden");
        document.getElementById("analyticsContent").classList.remove("hidden");
    } catch (error) {
        status.className = "empty";
        status.textContent = error.message || "Could not load analytics.";
    }
}

loadAnalytics();
