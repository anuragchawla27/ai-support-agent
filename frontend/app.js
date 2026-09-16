// Dashboard logic (Day 12).
//
// Auth model: the dashboard password is verified once via POST /auth/login,
// then kept in sessionStorage (cleared when the tab closes) and sent as the
// X-Dashboard-Password header on every /dashboard/* request. This matches
// the backend's shared-password auth (app/routers/auth.py).

const API_BASE = "http://127.0.0.1:8000";
// ^ Update this if the backend runs somewhere other than localhost:8000.

const loginScreen = document.getElementById("login-screen");
const loginForm = document.getElementById("login-form");
const passwordInput = document.getElementById("password-input");
const loginError = document.getElementById("login-error");

const dashboard = document.getElementById("dashboard");
const logoutBtn = document.getElementById("logout-btn");
const refreshBtn = document.getElementById("refresh-btn");
const filterStatus = document.getElementById("filter-status");
const filterPriority = document.getElementById("filter-priority");
const tableBody = document.getElementById("ticket-table-body");
const emptyState = document.getElementById("empty-state");

function getStoredPassword() {
  return sessionStorage.getItem("dashboard_password");
}

function showDashboard() {
  loginScreen.classList.add("hidden");
  dashboard.classList.remove("hidden");
  loadAnalytics();
  loadTickets();
}

function showLogin(message) {
  dashboard.classList.add("hidden");
  loginScreen.classList.remove("hidden");
  loginError.textContent = message || "";
}

// --- Login ---

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  loginError.textContent = "";

  const password = passwordInput.value;
  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      loginError.textContent = body.detail || "Login failed.";
      return;
    }

    sessionStorage.setItem("dashboard_password", password);
    passwordInput.value = "";
    showDashboard();
  } catch (err) {
    loginError.textContent = "Could not reach the server. Is the backend running?";
  }
});

logoutBtn.addEventListener("click", () => {
  sessionStorage.removeItem("dashboard_password");
  showLogin();
});

// --- Data fetching ---

async function authorizedFetch(path) {
  const password = getStoredPassword();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "X-Dashboard-Password": password || "" },
  });

  if (res.status === 401) {
    sessionStorage.removeItem("dashboard_password");
    showLogin("Session expired. Please log in again.");
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json();
}

async function loadAnalytics() {
  try {
    const data = await authorizedFetch("/dashboard/analytics");
    document.getElementById("stat-total").textContent = data.total_tickets ?? 0;
    document.getElementById("stat-resolved").textContent = data.by_status?.Resolved ?? 0;
    document.getElementById("stat-escalated").textContent = data.by_status?.Escalated ?? 0;
    document.getElementById("stat-processing").textContent = data.by_status?.Processing ?? 0;
  } catch (err) {
    console.error("Failed to load analytics:", err);
  }
}

async function loadTickets() {
  const params = new URLSearchParams();
  if (filterStatus.value) params.set("status", filterStatus.value);
  if (filterPriority.value) params.set("priority", filterPriority.value);

  try {
    const tickets = await authorizedFetch(`/dashboard/tickets?${params.toString()}`);
    renderTickets(tickets);
  } catch (err) {
    console.error("Failed to load tickets:", err);
  }
}

// --- Rendering ---

function badgeClass(prefix, value) {
  if (!value) return "";
  return `badge ${prefix}-${value.toLowerCase()}`;
}

function formatDate(isoString) {
  if (!isoString) return "-";
  const d = new Date(isoString);
  return d.toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function renderTickets(tickets) {
  tableBody.innerHTML = "";

  if (!tickets || tickets.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }
  emptyState.classList.add("hidden");

  for (const t of tickets) {
    const row = document.createElement("tr");

    row.innerHTML = `
      <td>${escapeHtml(t.customer_name || "Anonymous")}</td>
      <td class="query-cell" title="${escapeHtml(t.query_text)}">${escapeHtml(t.query_text)}</td>
      <td>${escapeHtml(t.intent || "-")}</td>
      <td><span class="${badgeClass("priority", t.priority)}">${t.priority || "-"}</span></td>
      <td>${escapeHtml(t.sentiment || "-")}</td>
      <td><span class="${badgeClass("status", t.status)}">${t.status}</span></td>
      <td>${escapeHtml(t.assigned_team || "-")}</td>
      <td class="confidence-cell">${t.confidence_score != null ? Math.round(t.confidence_score * 100) + "%" : "-"}</td>
      <td class="created-cell">${formatDate(t.created_at)}</td>
    `;
    tableBody.appendChild(row);
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

// --- Filter/refresh controls ---

refreshBtn.addEventListener("click", () => {
  loadAnalytics();
  loadTickets();
});
filterStatus.addEventListener("change", loadTickets);
filterPriority.addEventListener("change", loadTickets);

// --- Init ---

if (getStoredPassword()) {
  showDashboard();
} else {
  showLogin();
}
