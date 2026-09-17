# Test dataset

Day 14 requirement: 30-50 realistic queries covering Normal, Difficult,
Ambiguous, and Sensitive/failure categories.

Rather than a manually-filled table, this is implemented as an
**automated test suite**: `backend/scripts/run_test_suite.py` contains
36 queries across all four categories, sends each one through the real,
live API (`/tickets/create` -> `/tickets/{id}/respond`), and generates
`tests/test_results.md` automatically -- intent, priority, sentiment,
confidence score, status, assigned team, and pass/fail against expected
outcome, per query, plus category-level summary stats.

Run it with:

    docker-compose up -d postgres
    uvicorn app.main:app --app-dir backend --reload   (separate terminal)
    python backend/scripts/run_test_suite.py

That script's own docstring also lists two failure scenarios that need
a manual step (stopping Postgres, using an invalid API key) rather than
being automatable -- see the "Manual checks" section of the generated
`test_results.md` after running it.
