function escapeDatasetHTML(value) {
    return String(value ?? "").replace(/[&<>'"]/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;"}[character]));
}

function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    window.location.href = "/login";
}

async function loadFusedDataset() {
    const token = localStorage.getItem("access_token");
    if (!token) { window.location.href = "/login"; return; }
    const params = new URLSearchParams({
        search: document.getElementById("datasetSearch").value,
        source: document.getElementById("sourceFilter").value,
        job_role: document.getElementById("roleFilter").value,
        sort: document.getElementById("sortRecords").value
    });
    const status = document.getElementById("datasetStatus");
    try {
        const [statsResponse, recordsResponse] = await Promise.all([
            fetch("/api/fused-dataset/stats", { headers: { "Authorization": `Bearer ${token}` } }),
            fetch(`/api/fused-dataset?${params}`, { headers: { "Authorization": `Bearer ${token}` } })
        ]);
        if (statsResponse.status === 401 || recordsResponse.status === 401) { logout(); return; }
        if (!statsResponse.ok || !recordsResponse.ok) throw new Error("Unable to load the fused dataset.");
        const stats = await statsResponse.json();
        const data = await recordsResponse.json();
        document.getElementById("totalRecords").textContent = stats.total_records;
        document.getElementById("originalRecords").textContent = stats.original_records;
        document.getElementById("studentRecords").textContent = stats.student_generated_records;
        document.getElementById("datasetRows").innerHTML = data.records.map(record => `<tr><td><div class="table-role-cell"><strong>${escapeDatasetHTML(record.source)}</strong><small>${escapeDatasetHTML(record.result_id || record.master_row_id)}</small></div></td><td>${escapeDatasetHTML(record.job_role)}</td><td title="${escapeDatasetHTML(record.question)}">${escapeDatasetHTML(record.question)}</td><td title="${escapeDatasetHTML(record.answer)}">${escapeDatasetHTML(record.answer)}</td><td><span class="score-pill ${record.source === "student_interview" ? "badge-emerald" : "badge-amber"}">${escapeDatasetHTML(record.score || 0)}%</span></td><td>${escapeDatasetHTML(record.percentage || "-")}${record.percentage ? "%" : ""}</td><td><small>${escapeDatasetHTML(record.date)}</small></td></tr>`).join("") || `<tr><td colspan="7">No records match the current filters.</td></tr>`;
        status.textContent = `${data.count} records shown from the actual fused CSV.`;
    } catch (error) { status.textContent = error.message; }
}

document.addEventListener("DOMContentLoaded", () => {
    ["datasetSearch", "sourceFilter", "roleFilter", "sortRecords"].forEach(id => document.getElementById(id).addEventListener("input", loadFusedDataset));
    document.getElementById("refreshDataset").addEventListener("click", loadFusedDataset);
    loadFusedDataset();
});