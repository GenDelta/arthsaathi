-- Migration 010: Account Binding & Legal Name
-- Links bank statements to users to prevent cross-uploading.

CREATE TABLE IF NOT EXISTS account_bindings (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES users(id),
    account_hmac    TEXT NOT NULL UNIQUE,
    account_last4   TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_account_bindings_user ON account_bindings(user_id);
CREATE INDEX IF NOT EXISTS idx_account_bindings_hmac ON account_bindings(account_hmac);

-- Add legal_name to user_profiles for matching against bank statement holder names.
-- Note: init_db.py gracefully handles duplicate column errors if this is re-run.
ALTER TABLE user_profiles ADD COLUMN legal_name TEXT;
