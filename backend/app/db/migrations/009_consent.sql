-- Migration 009: User Consent Ledger
-- Stores append-only records of consent grants and withdrawals.

CREATE TABLE IF NOT EXISTS user_consents (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id),
    purpose         TEXT NOT NULL CHECK (purpose IN (
                        'STATEMENT_PROCESSING', 'VOICE_PROCESSING', 'COHORT_SHARING'
                    )),
    granted         INTEGER NOT NULL CHECK (granted IN (0, 1)),
    notice_version  TEXT NOT NULL,
    method          TEXT NOT NULL CHECK (method IN ('ONBOARDING_UI', 'SETTINGS_UI', 'API')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_consents_user_purpose
    ON user_consents(user_id, purpose, created_at DESC);
