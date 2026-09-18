# n8n workflow setup

The workflow file (`n8n/workflows/ai_support_agent_workflow.json`) is the
actual orchestration layer: it receives a customer query, calls the
FastAPI backend to process it, and either emails your team (if
escalated) or returns the AI's answer directly (if resolved).

## What it does, node by node

1. **Webhook - Customer Query** — receives `POST` requests with
   `{ query_text, customer_name, customer_email }`. This is what
   `frontend/customer.html` will eventually call instead of hitting the
   backend directly (see "Switching the customer form to use n8n" below).
2. **Create Ticket** — calls `POST /tickets/create`.
3. **Get AI Response** — calls `POST /tickets/{id}/respond`. This single
   call already does classification (if not done), retrieval, response
   generation, confidence scoring, and the escalation decision -- so the
   workflow itself only needs to branch on the *result*, not re-implement
   any of that logic.
4. **Was It Escalated?** — branches on `status == "Escalated"`.
5. **Notify Team** (escalated branch only) — sends an email to the
   relevant team's inbox with the ticket details.
6. **Respond - Escalated** / **Respond - Resolved** — sends the final
   reply back to whoever called the webhook (either the customer form,
   or anything else that hits this webhook).

## Import steps

1. Open your local n8n instance (the one running in Docker).
2. Click **Add workflow** (or the **+** button), then the **⋯** menu →
   **Import from File**.
3. Select `n8n/workflows/ai_support_agent_workflow.json`.
4. All 7 nodes should appear, already connected.

## Required manual configuration (n8n won't work without this)

### 1. Point the HTTP Request nodes at your backend

The two HTTP Request nodes (**Create Ticket**, **Get AI Response**) are
set to `http://host.docker.internal:8000` -- this is the special DNS
name Docker Desktop provides so a container (n8n) can reach services
running on your actual machine (your backend, running via `uvicorn`
outside Docker). This should work as-is on Windows/Mac Docker Desktop.
If it doesn't resolve, replace it with your machine's local IP address
instead (find it with `ipconfig` on Windows, look for IPv4 Address).

### 2. Add SMTP credentials for the email node

The **Notify Team** node needs real SMTP credentials -- n8n stores
these encrypted in its own credential store, never in this JSON file
(that's why the file only has a placeholder credential ID).

1. In n8n, go to **Credentials** → **Add Credential** → search **SMTP**.
2. Fill in your email provider's SMTP details. For a quick demo setup
   with no real email account needed, use a free
   [Mailtrap](https://mailtrap.io) sandbox inbox -- emails get captured
   there instead of actually sending, which is ideal for demoing this
   without spamming real inboxes.
3. Save the credential, then open the **Notify Team** node and select
   it from the credential dropdown.

### 3. Update the "to" email addresses

The **Notify Team** node routes to different addresses based on
`assigned_team` (Sales, Engineering, Internship Coordination, or a
general fallback). These are currently the fictional
`@pranavxlabs.example` addresses from the knowledge base -- replace
them with real addresses (or your single Mailtrap inbox) before demoing.

## Testing the workflow

1. Activate the workflow (toggle in the top-right of the n8n editor).
2. n8n shows the webhook's live URL (something like
   `http://localhost:5678/webhook/support-query`).
3. Send a test request:
   ```
   curl -X POST http://localhost:5678/webhook/support-query \
     -H "Content-Type: application/json" \
     -d '{"query_text": "What is the pricing for standard support automation?", "customer_name": "Test", "customer_email": "test@example.com"}'
   ```
4. You should get back a JSON response with the AI's answer. Try a
   query you know escalates (e.g. a complaint) and confirm the email
   arrives in your Mailtrap inbox.

## Switching the customer form to use n8n instead of the backend directly

Right now, `frontend/customer.js` calls the FastAPI backend directly
(`/tickets/create` then `/tickets/{id}/respond`) -- this was built and
tested first since it doesn't depend on n8n being configured. Once your
n8n workflow is confirmed working, you can point `customer.js` at the
webhook URL instead, collapsing it to a single call:

```javascript
const res = await fetch("http://localhost:5678/webhook/support-query", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ query_text, customer_name, customer_email }),
});
const { message, ticket_id, status } = await res.json();
```

This is optional -- both approaches produce the same end result. Routing
through n8n is what makes the system "automation-orchestrated" per the
project's architecture, but the direct-API version is simpler to keep
running if n8n isn't active during a demo.
