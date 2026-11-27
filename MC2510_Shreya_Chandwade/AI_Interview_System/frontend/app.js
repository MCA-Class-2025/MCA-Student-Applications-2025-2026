const App = {
    page: "",

    token() {
        return localStorage.getItem("access_token");
    },

    user() {
        try {
            return JSON.parse(localStorage.getItem("user") || "null");
        } catch {
            return null;
        }
    },

    authHeaders() {
        return {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.token()}`
        };
    },

    mount(options = {}) {
        this.page = options.page || document.body.dataset.page || "";
        if (options.auth && !this.token()) {
            window.location.href = "/login";
            return;
        }
        this.renderChrome();
        this.bindChrome();
        if (window.lucide) {
            window.lucide.createIcons();
        }
    },

    links() {
        const loggedIn = Boolean(this.token());
        if (!loggedIn) {
            return [
                { href: "/#features", label: "Features", id: "features" },
                { href: "/#how-it-works", label: "How it works", id: "how" },
                { href: "/login", label: "Login", id: "login" },
                { href: "/register", label: "Get Started", id: "register", cta: true }
            ];
        }
        return [
            { href: "/dashboard", label: "Dashboard", id: "dashboard" },
            { href: "/interview", label: "Interview", id: "interview" },
            { href: "/feedback", label: "Feedback", id: "feedback" },
            { href: "/analytics", label: "Analytics", id: "analytics" },
            { href: "/plan", label: "Study Plan", id: "plan" },
            { href: "/fusion", label: "Fusion", id: "fusion" },
            { href: "/fused-dataset", label: "Dataset", id: "dataset" }
        ];
    },

    renderChrome() {
        const header = document.getElementById("site-header");
        const footer = document.getElementById("site-footer");
        const loggedIn = Boolean(this.token());
        const user = this.user();

        if (header) {
            const nav = this.links().map((link) => `
                <a href="${link.href}" class="nav-link${link.cta ? " nav-cta" : ""}${this.page === link.id ? " active" : ""}" ${this.page === link.id ? 'aria-current="page"' : ""}>${link.label}</a>
            `).join("");

            header.innerHTML = `
                <a class="brand" href="${loggedIn ? "/dashboard" : "/"}">
                    <span class="brand-mark" aria-hidden="true">AI</span>
                    <span><strong>InterviewOS</strong></span>
                </a>
                <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">
                    <i data-lucide="menu"></i>
                    <span class="sr-only">Open menu</span>
                </button>
                <nav id="site-nav" class="site-nav" aria-label="Primary">
                    ${nav}
                    ${loggedIn ? `<button type="button" class="nav-link nav-logout" id="logoutButton">Sign out${user?.name ? ` · ${this.escape(user.name.split(" ")[0])}` : ""}</button>` : ""}
                </nav>
            `;
        }

        if (footer) {
            footer.innerHTML = `
                <div class="footer-brand">
                    <strong>InterviewOS</strong>
                    <p>Mock interviews, feedback, and study plans.</p>
                </div>
                <div class="footer-links">
                    <a href="/">Home</a>
                    <a href="/login">Login</a>
                    <a href="/register">Register</a>
                    <a href="/fusion">Data fusion</a>
                </div>
            `;
        }

        if (!document.getElementById("toast-region")) {
            const region = document.createElement("div");
            region.id = "toast-region";
            region.className = "toast-region";
            region.setAttribute("aria-live", "polite");
            document.body.appendChild(region);
        }

        if (!document.getElementById("confirm-dialog")) {
            const dialog = document.createElement("div");
            dialog.id = "confirm-dialog";
            dialog.className = "modal-backdrop hidden";
            dialog.innerHTML = `
                <div class="modal-card confirm-card" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
                    <h2 id="confirm-title">Please confirm</h2>
                    <p id="confirm-message"></p>
                    <div class="confirm-actions">
                        <button type="button" class="btn btn-ghost" id="confirm-cancel">Cancel</button>
                        <button type="button" class="btn btn-primary" id="confirm-ok">Confirm</button>
                    </div>
                </div>
            `;
            document.body.appendChild(dialog);
        }
    },

    bindChrome() {
        const toggle = document.querySelector(".nav-toggle");
        const nav = document.getElementById("site-nav");
        if (toggle && nav) {
            toggle.addEventListener("click", () => {
                const open = nav.classList.toggle("open");
                toggle.setAttribute("aria-expanded", String(open));
            });
        }
        const logoutButton = document.getElementById("logoutButton");
        if (logoutButton) {
            logoutButton.addEventListener("click", () => this.logout());
        }
    },

    async logout() {
        const ok = await this.confirm("Sign out of InterviewOS?");
        if (!ok) return;
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.href = "/login";
    },

    toast(message, type = "info") {
        const region = document.getElementById("toast-region");
        if (!region) return;
        const item = document.createElement("div");
        item.className = `toast toast-${type}`;
        item.textContent = message;
        region.appendChild(item);
        setTimeout(() => item.remove(), 4200);
    },

    confirm(message) {
        const dialog = document.getElementById("confirm-dialog");
        const text = document.getElementById("confirm-message");
        const ok = document.getElementById("confirm-ok");
        const cancel = document.getElementById("confirm-cancel");
        if (!dialog || !text || !ok || !cancel) {
            return Promise.resolve(window.confirm(message));
        }
        text.textContent = message;
        dialog.classList.remove("hidden");
        ok.focus();
        return new Promise((resolve) => {
            const close = (value) => {
                dialog.classList.add("hidden");
                ok.removeEventListener("click", onOk);
                cancel.removeEventListener("click", onCancel);
                resolve(value);
            };
            const onOk = () => close(true);
            const onCancel = () => close(false);
            ok.addEventListener("click", onOk);
            cancel.addEventListener("click", onCancel);
        });
    },

    escape(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },

    skillLabel(average, interviews) {
        if (!interviews) return "Not assessed";
        if (average >= 85) return "Advanced";
        if (average >= 70) return "Proficient";
        if (average >= 55) return "Developing";
        return "Foundation";
    },

    formatDetail(data) {
        const detail = data?.detail;
        if (Array.isArray(detail)) {
            return detail.map((item) => item.msg || item).join(", ");
        }
        return detail || "Request failed.";
    }
};

function logout() {
    App.logout();
}

document.addEventListener("DOMContentLoaded", () => {
    if (document.body.dataset.autoMount === "true") {
        App.mount({
            page: document.body.dataset.page,
            auth: document.body.dataset.auth === "required"
        });
    }
});
