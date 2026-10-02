-- 004_profile_expansion.sql

ALTER TABLE user_profiles ADD COLUMN date_of_birth DATE;
ALTER TABLE user_profiles ADD COLUMN state_of_residence VARCHAR;

CREATE TABLE flagged_entities (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    entity_name VARCHAR NOT NULL,
    source_document_id VARCHAR,
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(source_document_id) REFERENCES documents(id) ON DELETE SET NULL
);

