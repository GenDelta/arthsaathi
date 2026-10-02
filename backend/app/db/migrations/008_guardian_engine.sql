CREATE TABLE IF NOT EXISTS nudge_feedback (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    nudge_type TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS flagged_entities (
    id TEXT PRIMARY KEY,
    entity_name TEXT NOT NULL,
    reason TEXT NOT NULL,
    flagged_at TEXT NOT NULL,
    user_id TEXT NOT NULL
);
