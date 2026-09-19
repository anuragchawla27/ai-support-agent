// Customer-facing query form (Day 15).
//
// This calls the n8n webhook, which handles the full pipeline itself:
// create ticket -> classify/respond -> email the customer -> email the
// team if escalated -> reply back here with the result. n8n is the
// orchestrator now -- this page no longer talks to the backend directly.

const N8N_WEBHOOK_URL = "http://localhost:5678/webhook/support-query";
// ^ Update this if your n8n instance runs somewhere other than
// localhost:5678, or if you rename the webhook path in n8n.

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
    const res = await fetch(N8N_WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query_text: question,
        customer_name: document.getElementById("name").value.trim() || null,
        customer_email: document.getElementById("email").value.trim() || null,
      }),
    });

    if (!res.ok) {
      throw new Error("The request didn't go through. Please try again.");
    }
    const body = await res.json();

    showResult(body, question);
    document.getElementById("question").value = "";
  } catch (err) {
    errorBanner.textContent = err.message || "Something went wrong. Please try again.";
    errorBanner.classList.remove("hidden");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Send";
  }
});

function showResult(body, questionAsked) {
  // The two branches of the n8n workflow return slightly different
  // shapes (Resolved passes through the backend's "response" field,
  // Escalated has its own "message" field) -- handle both.
  const answerText = body.response || body.message || "Thanks for your question -- we'll follow up shortly.";
  const isEscalated = body.status === "Escalated";

  resultCard.classList.remove("hidden");
  resultCard.classList.toggle("escalated", isEscalated);

  const questionEcho = `<span style="color: var(--text-dim);">You asked: "${escapeHtml(questionAsked)}"</span><br><br>`;

  resultHeading.textContent = isEscalated ? "We're on it" : "Here's your answer";
  resultText.innerHTML = questionEcho + escapeHtml(answerText);
  ticketRef.textContent = body.ticket_id ? `Reference: ${body.ticket_id}` : "";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}
