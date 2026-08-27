"""Top-level tests package.

Mirror of app/ directory structure:
  tests/
    api/          ← tests for app/api/ routers
    repositories/ ← tests for app/repositories/ (incl. isolation tests)
    agents/       ← tests for app/agents/ graph logic
    services/     ← tests for app/services/
    security/     ← static-analysis security tests (route coverage, no PII leak, etc.)
    conftest.py   ← shared fixtures (test DB, mock LLM, test client)
"""
