CREATE TABLE IF NOT EXISTS tracked_debts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    total_amount REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
