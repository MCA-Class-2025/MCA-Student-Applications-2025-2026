const progressKey = `study-plan-progress-${App.user()?.id || "account"}`;

function readProgress() {
    try {
        return JSON.parse(localStorage.getItem(progressKey) || "{}");
    } catch {
        return {};
    }
}

function parseDays(text) {
    const parts = String(text || "").split(/\n###\s+/);
    if (parts.length < 2) return [];
    return parts.slice(1).map((part) => {
        const lines = part.trim().split("\n").filter(Boolean);
        const title = lines[0].replace(/\*\*/g, "").trim();
        const items = lines.slice(1).map((line) => line.replace(/^[-*\d.\s]+/, "").replace(/\*\*/g, "").trim()).filter(Boolean);
        return { title, items };
    });
}

function renderProgress(total) {
    const saved = readProgress();
    const done = Object.values(saved).filter(Boolean).length;
    const percent = total ? Math.round((done / total) * 100) : 0;
    document.getElementById("planProgress").style.width = `${percent}%`;
    document.getElementById("planProgressLabel").textContent = total
        ? `${done} of ${total} days marked complete on this browser.`
        : "No day-by-day plan is available yet.";
}

function renderPlan(data) {
    const days = parseDays(data.study_plan);
    const container = document.getElementById("planDays");
    const saved = readProgress();
    const topics = Array.isArray(data.weak_topics) ? data.weak_topics.join(", ") : "";
    document.getElementById("planLead").textContent = data.job_role
        ? `${data.job_role}${data.current_score !== undefined ? ` · recent answer average ${Math.round(data.current_score)}%` : ""}`
        : "Generated from your recent saved interviews.";
    document.getElementById("planFocus").textContent = topics ? `Focus from recent interviews: ${topics}` : "";
    if (!days.length) {
        container.innerHTML = `<article class="card"><div class="evaluation">${App.escape(data.study_plan || "No plan returned.")}</div></article>`;
        renderProgress(0);
        return;
    }
    container.innerHTML = days.map((day, index) => `
        <article class="card day-card${saved[index] ? " done" : ""}">
            <label class="check-row">
                <input type="checkbox" data-day="${index}" ${saved[index] ? "checked" : ""}>
                <span><h3>${App.escape(day.title)}</h3></span>
            </label>
            <ul>${day.items.map((item) => `<li>${App.escape(item)}</li>`).join("")}</ul>
        </article>
    `).join("");
    renderProgress(days.length);
    container.querySelectorAll("input[type=checkbox]").forEach((input) => {
        input.addEventListener("change", () => {
            const next = readProgress();
            next[input.dataset.day] = input.checked;
            localStorage.setItem(progressKey, JSON.stringify(next));
            input.closest(".day-card").classList.toggle("done", input.checked);
            renderProgress(days.length);
        });
    });
}

async function loadPlan() {
    const status = document.getElementById("planStatus");
    const button = document.getElementById("refreshPlan");
    button.disabled = true;
    status.className = "loading-inline";
    status.innerHTML = `<span class="spinner"></span> Building your plan.`;
    document.getElementById("planDays").innerHTML = "";
    try {
        const response = await fetch("/study-plan", { headers: App.authHeaders() });
        if (response.status === 401) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("user");
            window.location.href = "/login";
            return;
        }
        const data = await response.json();
        if (!response.ok) throw new Error(App.formatDetail(data));
        renderPlan(data);
        status.classList.add("hidden");
    } catch (error) {
        status.className = "empty";
        status.textContent = error.message || "Could not generate the study plan.";
    } finally {
        button.disabled = false;
    }
}

document.getElementById("refreshPlan").addEventListener("click", loadPlan);
loadPlan();
