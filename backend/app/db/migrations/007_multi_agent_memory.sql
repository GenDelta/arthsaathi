-- Migration 007: Multi-Agent Memory & Flagged Entities

CREATE TABLE IF NOT EXISTS flagged_entities (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    source_document_id TEXT,
    detected_at TEXT NOT NULL
);

-- We don't alter user_profiles for savings_percentage since SQLite doesn't natively support IF NOT EXISTS for ADD COLUMN easily across all versions.
-- Instead, we will store the dynamic savings_percentage in behavioral_summary or simply add a table for dynamic settings if needed, 
-- or we can use a try/catch in Python during initialization. For now, creating the flagged_entities table is the critical schema addition.
