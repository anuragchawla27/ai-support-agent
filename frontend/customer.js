// Customer-facing query form (Day 15).
//
// This is the actual public entry point the n8n workflow's webhook
// mirrors: create a ticket, then get a response. Unlike the dashboard,
// this page needs no authentication -- anyone can ask a question.

const API_BASE = "http://127.0.0.1:8000";
// ^ Update this if the backend runs somewhere other than localhost:8000.

const form = document.getElementById("query-form");
const submitBtn = document.getElementById("submit-btn");
const resultCard = document.getElementById("result-card");
const resultHeading = document.getElementById("result-heading");
const resultText = document.getElementById("result-text");
const ticketRef = document.getElementById("ticket-ref");
const errorBanner = document.getElementById("error-banner");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const question = document.getElementById("question").value.trim();
  if (!question) return;

  submitBtn.disabled = true;
  submitBtn.textContent = "Thinking...";
  resultCard.classList.add("hidden");
  errorBanner.classList.add("hidden");

  try {
    const createRes = await fetch(`${API_BASE}/tickets/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query_text: question,
        customer_name: document.getElementById("name").value.trim() || null,
        customer_email: document.getElementById("email").value.trim() || null,
      }),
    });

    if (!createRes.ok) {
      const body = await createRes.json().catch(() => ({}));
      throw new Error(body.detail || "Could not submit your question.");
    }
    const createBody = await createRes.json();

    const respondRes = await fetch(`${API_BASE}/tickets/${createBody.ticket_id}/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });

    if (!respondRes.ok) {
      throw new Error("We received your question but had trouble generating a response.");
    }
    const respondBody = await respondRes.json();

    showResult(respondBody, createBody.ticket_id, question);
    document.getElementById("question").value = "";
  } catch (err) {
    errorBanner.textContent = err.message || "Something went wrong. Please try again.";
    errorBanner.classList.remove("hidden");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Send";
  }
});

function showResult(respondBody, ticketId, questionAsked) {
  const isEscalated = respondBody.status === "Escalated";

  resultCard.classList.remove("hidden");
  resultCard.classList.toggle("escalated", isEscalated);

  const questionEcho = `<span style="color: var(--text-dim);">You asked: "${escapeHtml(questionAsked)}"</span><br><br>`;

  if (isEscalated) {
    resultHeading.textContent = "We're on it";
    resultText.innerHTML =
      questionEcho +
      "Your question needs a closer look from our team. We've logged it and will follow up with you directly.";
  } else {
    resultHeading.textContent = "Here's your answer";
    resultText.innerHTML = questionEcho + escapeHtml(respondBody.response);
  }

  ticketRef.textContent = `Reference: ${ticketId}`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}
