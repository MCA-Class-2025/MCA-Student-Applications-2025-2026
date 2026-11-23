function statusLabel(value) {
    return value ? `<span class="status-on">Active</span>` : `<span class="status-off">Unavailable</span>`;
}

async function loadFusionStatus() {
    const grid = document.getElementById("fusionStatus");
    try {
        const response = await fetch("/fusion-status");
        const data = await response.json();
        if (!response.ok) throw new Error(App.formatDetail(data));
        const sources = Array.isArray(data.sources) ? data.sources.join(", ") : "Not listed";
        const cards = [
            ["Data-level fusion", statusLabel(data.data_level_fusion), "Record loading and deduplication"],
            ["Feature-level fusion", statusLabel(data.feature_level_fusion), "Combined retrieval features"],
            ["Decision-level fusion", statusLabel(data.decision_level_fusion), "Final ranking decision"],
            ["Sources loaded", data.sources_loaded ?? "—", sources],
            ["Records before dedupe", data.records_before_deduplication ?? "—", "Rows collected from connected inputs"],
            ["Records after dedupe", data.records_after_deduplication ?? "—", "Unified knowledge records"]
        ];
        grid.innerHTML = cards.map(([label, value, note]) => `
            <article class="card stat"><span>${label}</span><strong>${value}</strong><span>${App.escape(note)}</span></article>
        `).join("");
    } catch (error) {
        grid.innerHTML = `<article class="card stat"><span>Fusion status</span><strong>—</strong><span>${App.escape(error.message)}</span></article>`;
    }
}

loadFusionStatus();
