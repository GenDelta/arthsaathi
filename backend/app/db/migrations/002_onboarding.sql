-- Migration 002: Onboarding — TOTP Auth + User Profiles
-- SQLite ALTER TABLE does not support IF NOT EXISTS; init_db.py handles idempotency.

-- Add is_onboarded flag to users (default false for all existing users)
ALTER TABLE users ADD COLUMN is_onboarded INTEGER NOT NULL DEFAULT 0;

-- Add TOTP secret column to users (populated when user first sets up authenticator)
ALTER TABLE users ADD COLUMN totp_secret TEXT;

-- User profiles table (Living Memory — bounded structured profile)
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id              TEXT PRIMARY KEY REFERENCES users(id),
    employment_type      TEXT CHECK (employment_type IN ('SALARIED','GIG_WORKER','SEASONAL','UNEMPLOYED')),
    occupation           TEXT,
    income_frequency     TEXT CHECK (income_frequency IN ('DAILY','WEEKLY','MONTHLY','SEASONAL')),
    average_income       REAL,
    financial_pain_points TEXT,
    behavioral_summary   TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
);
