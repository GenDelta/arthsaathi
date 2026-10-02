-- 005_gender_and_schemes.sql

-- 1. Add gender to user_profiles
ALTER TABLE user_profiles ADD COLUMN gender VARCHAR;

-- 2. Recreate schemes table for CSV ingestion
-- Drop dependent table first
DROP TABLE IF EXISTS scheme_matches;
DROP TABLE IF EXISTS schemes;

CREATE TABLE schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_name TEXT NOT NULL,
    scheme_type TEXT,
    state_name TEXT,
    min_age INTEGER,
    max_age INTEGER,
    details TEXT,
    eligibility TEXT,
    benefits TEXT,
    application_process TEXT,
    tags TEXT
);

CREATE TABLE scheme_matches (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    scheme_id INTEGER NOT NULL REFERENCES schemes(id),
    match_score REAL NOT NULL,
    user_action TEXT CHECK (user_action IN ('VIEWED','APPLIED','DISMISSED')),
    shown_at TEXT NOT NULL DEFAULT (datetime('now')),
    action_at TEXT
);

