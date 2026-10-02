-- Migration 003: Make password_hash nullable for TOTP-only users
-- SQLite does not support ALTER COLUMN, so we recreate the users table
-- preserving all data.

CREATE TABLE IF NOT EXISTS users_new (
    id                TEXT PRIMARY KEY,
    organization_id   TEXT REFERENCES organizations(id),
    name              TEXT NOT NULL,
    phone_number      TEXT NOT NULL UNIQUE,
    password_hash     TEXT,                              -- NULL for TOTP-only users
    totp_secret       TEXT,                              -- NULL for password-only users
    occupation        TEXT,
    income_bracket    TEXT CHECK (income_bracket IN ('LT_10K','10K_25K','25K_50K','GT_50K')),
    language_pref     TEXT NOT NULL DEFAULT 'en',
    role              TEXT NOT NULL CHECK (role IN ('CITIZEN','NGO_ADMIN','NGO_EDUCATOR','SPONSOR_VIEWER')) DEFAULT 'CITIZEN',
    is_active         INTEGER NOT NULL DEFAULT 1,
    is_onboarded      INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO users_new
    (id, organization_id, name, phone_number, password_hash, totp_secret,
     occupation, income_bracket, language_pref, role, is_active, is_onboarded,
     created_at, updated_at)
SELECT
    id, organization_id, name, phone_number,
    CASE WHEN password_hash = 'totp-only-no-password' THEN NULL ELSE password_hash END,
    totp_secret,
    occupation, income_bracket, language_pref, role, is_active,
    COALESCE(is_onboarded, 0),
    created_at, updated_at
FROM users;

DROP TABLE users;
ALTER TABLE users_new RENAME TO users;

CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);
