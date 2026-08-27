# e2e_manual_test_results.md — ArthSaathi

End-to-end manual test results log (Phase 11 / task 11.2).

---

## Test Run Log

| Run date | Tester | Stack version | US-01 Scam Scanner | US-02 Scheme Matchmaker | US-03 Katha Mode | US-04 Income Tracker | US-05 Financial Guardian | Notes |
|---|---|---|---|---|---|---|---|---|
| *(pending)* | — | — | — | — | — | — | — | Phase 11 not yet reached |

---

## User Story Checklists

### US-01 — Scam Scanner
- [ ] Upload a PDF/JPG/PNG document
- [ ] Confirm extracted OCR text is displayed in an editable textarea before submission
- [ ] Edit and submit via the HITL verify step
- [ ] Poll until `ANALYZED` status
- [ ] Confirm `risk_level` and `risk_summary` render correctly

### US-02 — Scheme Matchmaker
- [ ] Submit an occupation + income_bracket + state profile
- [ ] Confirm exactly 3 scheme cards render (or `partial_results` banner if fewer)
- [ ] Click "Mark as Applied" and confirm network call succeeds

### US-03 — Katha Mode
- [ ] Submit a financial term and occupation context
- [ ] Confirm words appear incrementally (word-by-word SSE stream)
- [ ] Confirm final word count ≤ 100
- [ ] Confirm no direct investment advice language present

### US-04 — Income Tracker & Micro-Savings
- [ ] Log an INCOME transaction
- [ ] Confirm nudge modal appears with a suggested savings amount in 2–5% range
- [ ] Explicitly approve the nudge and confirm a savings goal is created
- [ ] Dismiss a nudge and confirm no goal row is created

### US-05 — Financial Guardian
- [ ] Log expense transactions that form an overspend pattern
- [ ] Confirm a Guardian alert toast appears without a page reload
- [ ] Confirm the alert is non-intrusive and dismissible
