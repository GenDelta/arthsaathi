-- ═══════════════════════════════════════════════════════════════════════════════
-- ArthSaathi — Initial Schema (Migration 001)
-- Source of truth: ARCHITECTURE.md §2.1
-- Applied by: backend/app/db/init_db.py
-- ═══════════════════════════════════════════════════════════════════════════════

-- Enable WAL mode and foreign key enforcement (applied at connection-open time
-- in init_db.py via PRAGMA statements before running this script).

-- ═══════════════════════════════════════════════════════════════════════════════
-- ORGANIZATIONS (NGO / Sponsor tenants)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS organizations (
    id                TEXT PRIMARY KEY,          -- UUIDv4
    name              TEXT NOT NULL,
    tenant_type       TEXT NOT NULL CHECK (tenant_type IN ('NGO','SPONSOR')),
    region            TEXT,                      -- e.g. state/district, for cohort scoping
    is_active         INTEGER NOT NULL DEFAULT 1,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- USERS
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS users (
    id                TEXT PRIMARY KEY,          -- UUIDv4
    organization_id   TEXT REFERENCES organizations(id),  -- NULL for CITIZEN
    name              TEXT NOT NULL,
    phone_number      TEXT NOT NULL UNIQUE,      -- primary auth identifier (India context)
    password_hash     TEXT NOT NULL,             -- bcrypt
    occupation        TEXT,                      -- free-text, normalized against a controlled vocabulary in app layer
    income_bracket    TEXT CHECK (income_bracket IN ('LT_10K','10K_25K','25K_50K','GT_50K')),
    language_pref     TEXT NOT NULL DEFAULT 'hi', -- ISO 639-1
    role              TEXT NOT NULL CHECK (role IN ('CITIZEN','NGO_ADMIN','NGO_EDUCATOR','SPONSOR_VIEWER')) DEFAULT 'CITIZEN',
    is_active         INTEGER NOT NULL DEFAULT 1,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- ORGANIZATION MEMBERSHIPS (citizen opt-in to an NGO cohort)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS organization_memberships (
    id                TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES users(id),   -- must be role=CITIZEN
    organization_id   TEXT NOT NULL REFERENCES organizations(id),
    consented_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, organization_id)
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- TRANSACTIONS (Income Tracker ledger)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS transactions (
    id                TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES users(id),
    type              TEXT NOT NULL CHECK (type IN ('INCOME','EXPENSE')),
    category          TEXT NOT NULL CHECK (category IN (
                          'GIG_WAGE','AGRICULTURAL_SALE','OTHER_INCOME',
                          'FOOD','TRANSPORT','UTILITIES','DEBT_REPAYMENT',
                          'DISCRETIONARY','HEALTHCARE','OTHER_EXPENSE'
                      )),
    amount            REAL NOT NULL CHECK (amount > 0),
    currency          TEXT NOT NULL DEFAULT 'INR',
    description       TEXT,
    occurred_at       TEXT NOT NULL,             -- ISO-8601, user-supplied date of transaction
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_transactions_user_time ON transactions(user_id, occurred_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════════
-- NUDGES (micro-savings prompts + Guardian alerts)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS nudges (
    id                    TEXT PRIMARY KEY,
    user_id               TEXT NOT NULL REFERENCES users(id),
    transaction_id        TEXT REFERENCES transactions(id),  -- NULL for Guardian alerts not tied to one tx
    nudge_type            TEXT NOT NULL CHECK (nudge_type IN ('MICRO_SAVINGS','GUARDIAN_ALERT')),
    message               TEXT NOT NULL,
    suggested_amount      REAL,                  -- populated for MICRO_SAVINGS (2-5% of income)
    risk_score            REAL,                  -- populated for GUARDIAN_ALERT (0.0-1.0)
    acknowledged_status   TEXT NOT NULL CHECK (acknowledged_status IN ('PENDING','APPROVED','DISMISSED')) DEFAULT 'PENDING',
    created_at            TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at           TEXT
);
CREATE INDEX IF NOT EXISTS idx_nudges_user_status ON nudges(user_id, acknowledged_status);

-- ═══════════════════════════════════════════════════════════════════════════════
-- SAVINGS GOALS (created only on explicit HITL approval of a nudge)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS savings_goals (
    id                TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES users(id),
    nudge_id          TEXT REFERENCES nudges(id),
    amount            REAL NOT NULL CHECK (amount > 0),
    status            TEXT NOT NULL CHECK (status IN ('ACTIVE','WITHDRAWN')) DEFAULT 'ACTIVE',
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- DOCUMENTS (Scam Scanner — HITL + audit trail; raw image never persisted)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS documents (
    id                    TEXT PRIMARY KEY,
    user_id               TEXT NOT NULL REFERENCES users(id),
    original_filename     TEXT NOT NULL,
    mime_type             TEXT NOT NULL CHECK (mime_type IN ('application/pdf','image/jpeg','image/png')),
    extracted_text        TEXT,                  -- raw OCR output
    verified_text         TEXT,                  -- post-HITL user-corrected text; NULL until user approves
    risk_summary          TEXT,
    risk_level            TEXT CHECK (risk_level IN ('LOW','MEDIUM','HIGH')),
    matched_clause_ids    TEXT,                  -- JSON array of LanceDB clause ids matched
    status                TEXT NOT NULL CHECK (status IN (
                              'PENDING_OCR','PENDING_VERIFICATION','ANALYZING','ANALYZED','FAILED'
                          )) DEFAULT 'PENDING_OCR',
    error_message         TEXT,
    created_at            TEXT NOT NULL DEFAULT (datetime('now')),
    analyzed_at           TEXT
);
CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- SCHEMES (relational mirror of scheme metadata; embeddings live in LanceDB)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS schemes (
    id                        TEXT PRIMARY KEY,
    scheme_name               TEXT NOT NULL,
    issuing_body              TEXT NOT NULL,
    eligible_occupations      TEXT NOT NULL,     -- JSON array, e.g. ["gig_worker","agricultural_worker"]
    eligibility_income_max    REAL,              -- NULL = no income cap
    eligibility_states        TEXT,              -- JSON array of applicable states; NULL = national
    description               TEXT NOT NULL,
    benefit_summary           TEXT NOT NULL,
    is_active                 INTEGER NOT NULL DEFAULT 1,
    created_at                TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- SCHEME MATCHES (audit log for success-metric tracking)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS scheme_matches (
    id                TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES users(id),
    scheme_id         TEXT NOT NULL REFERENCES schemes(id),
    match_score       REAL NOT NULL,             -- cosine similarity, 0.0-1.0
    user_action       TEXT CHECK (user_action IN ('VIEWED','APPLIED','DISMISSED')),
    shown_at          TEXT NOT NULL DEFAULT (datetime('now')),
    action_at         TEXT
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- KATHA SESSIONS (Storyteller audit log — enforces word-limit compliance)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS katha_sessions (
    id                TEXT PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES users(id),
    input_term        TEXT NOT NULL,
    occupation_context TEXT NOT NULL,
    generated_story   TEXT NOT NULL,
    word_count        INTEGER NOT NULL CHECK (word_count <= 100),
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- AUDIT LOGS (compliance trail for NGO aggregate-data access)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS audit_logs (
    id                TEXT PRIMARY KEY,
    actor_user_id     TEXT NOT NULL REFERENCES users(id),
    action            TEXT NOT NULL,             -- e.g. 'NGO_COHORT_VIEW'
    resource          TEXT NOT NULL,             -- e.g. 'organization:{id}:cohort_summary'
    metadata          TEXT,                      -- JSON, non-PII details only
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
