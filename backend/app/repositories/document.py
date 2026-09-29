"""DocumentRepository — data access for the documents table."""

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import aiosqlite

from app.core.config import get_settings
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DocumentRow:
    id: str
    user_id: str
    original_filename: str
    mime_type: str
    extracted_text: str | None
    verified_text: str | None
    risk_summary: str | None
    risk_level: str | None
    matched_clause_ids: str | None
    status: str
    error_message: str | None
    created_at: str
    analyzed_at: str | None


class DocumentRepository:
    def __init__(self, database_path: str | None = None) -> None:
        self._db_path = database_path or get_settings().database_path

    async def create(
        self,
        user_id: str,
        original_filename: str,
        mime_type: str,
        extracted_text: str | None = None,
        status: str = "PENDING_OCR",
    ) -> DocumentRow:
        doc_id = str(uuid.uuid4())
        now = datetime.now(UTC).isoformat()
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA foreign_keys = ON")
            await conn.execute(
                """
                INSERT INTO documents (
                    id, user_id, original_filename, mime_type,
                    extracted_text, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_id, user_id, original_filename, mime_type, extracted_text, status, now),
            )
            await conn.commit()
        return await self.get_by_id(doc_id, user_id)

    async def get_by_id(self, doc_id: str, requesting_user_id: str) -> DocumentRow:
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM documents WHERE id = ? AND user_id = ?",
                (doc_id, requesting_user_id),
            ) as cursor:
                row = await cursor.fetchone()
        if not row:
            raise NotFoundError(f"Document '{doc_id}' not found")
        return _row_to_doc(row)

    async def get_all_for_user(self, user_id: str) -> list[DocumentRow]:
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ) as cursor:
                rows = await cursor.fetchall()
        return [_row_to_doc(row) for row in rows]

    async def update_status(
        self,
        doc_id: str,
        user_id: str,
        status: str,
        extracted_text: str | None = None,
        verified_text: str | None = None,
        risk_summary: str | None = None,
        risk_level: str | None = None,
        matched_clause_ids: list[str] | None = None,
        error_message: str | None = None,
    ) -> DocumentRow:
        now = datetime.now(UTC).isoformat()
        
        updates = ["status = ?"]
        params: list[Any] = [status]
        
        if extracted_text is not None:
            updates.append("extracted_text = ?")
            params.append(extracted_text)
        if verified_text is not None:
            updates.append("verified_text = ?")
            params.append(verified_text)
        if risk_summary is not None:
            updates.append("risk_summary = ?")
            params.append(risk_summary)
            updates.append("analyzed_at = ?")
            params.append(now)
        if risk_level is not None:
            updates.append("risk_level = ?")
            params.append(risk_level)
        if matched_clause_ids is not None:
            updates.append("matched_clause_ids = ?")
            params.append(json.dumps(matched_clause_ids))
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
            
        params.extend([doc_id, user_id])
        
        query = f"UPDATE documents SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
        
        async with aiosqlite.connect(self._db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA foreign_keys = ON")
            await conn.execute(query, params)
            await conn.commit()
            
        return await self.get_by_id(doc_id, user_id)


def _row_to_doc(row: aiosqlite.Row) -> DocumentRow:
    return DocumentRow(
        id=row["id"],
        user_id=row["user_id"],
        original_filename=row["original_filename"],
        mime_type=row["mime_type"],
        extracted_text=row["extracted_text"],
        verified_text=row["verified_text"],
        risk_summary=row["risk_summary"],
        risk_level=row["risk_level"],
        matched_clause_ids=row["matched_clause_ids"],
        status=row["status"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        analyzed_at=row["analyzed_at"],
    )
