"""Scam Scanner API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from pydantic import BaseModel, Field

from app.core.dependencies import TenantContext, get_tenant_context
from app.core.exceptions import UnsupportedMediaTypeError
from app.repositories.document import DocumentRepository
from app.repositories.user import UserRepository
from app.services.ocr import MAX_FILE_SIZE_BYTES, extract_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scan-document", tags=["scam-scanner"])

# ─── Models ───────────────────────────────────────────────────────────────────

class ScanInitResponse(BaseModel):
    document_id: str
    status: str
    extracted_text: str | None


class VerifyRequest(BaseModel):
    verified_text: str = Field(..., min_length=1)


class VerifyResponse(BaseModel):
    document_id: str
    status: str


class ClauseMatchResult(BaseModel):
    clause_category: str
    explanation: str


class ScanStatusResponse(BaseModel):
    document_id: str
    status: str
    risk_level: str | None = None
    risk_summary: str | None = None
    error_message: str | None = None
    matched_clauses: list[ClauseMatchResult] = Field(default_factory=list)


# ─── Background Tasks ─────────────────────────────────────────────────────────

async def run_scam_analysis(doc_id: str, user_id: str) -> None:
    """Run the Scam Scan LangGraph asynchronously."""
    from app.agents.scam.graph import scam_graph

    doc_repo = DocumentRepository()
    user_repo = UserRepository()

    try:
        doc = await doc_repo.get_by_id(doc_id, user_id)
        user = await user_repo.get_by_id(user_id, user_id)

        initial_state = {
            "document_id": doc_id,
            "raw_text": doc.extracted_text or "",
            "verified_text": doc.verified_text,
            "matched_clauses": [],
            "risk_score": None,
            "risk_summary": None,
            "language": user.language_pref,
        }

        # Run the graph
        final_state = await scam_graph.ainvoke(initial_state)

        # Determine risk level
        risk_score = final_state.get("risk_score") or 0.0
        if risk_score >= 0.7:
            risk_level = "HIGH"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        matched_clause_ids = [c["id"] for c in final_state.get("matched_clauses", []) if "id" in c]

        await doc_repo.update_status(
            doc_id=doc_id,
            user_id=user_id,
            status="ANALYZED",
            risk_summary=final_state.get("risk_summary"),
            risk_level=risk_level,
            matched_clause_ids=matched_clause_ids,
        )

        lender_name = final_state.get("lender_name")
        if risk_level == "HIGH" and lender_name and lender_name.lower() != "null":
            import aiosqlite
            import uuid
            from datetime import datetime, timezone
            from app.core.config import get_settings
            
            db_path = get_settings().database_path
            async with aiosqlite.connect(db_path) as conn:
                await conn.execute(
                    "INSERT INTO flagged_entities (id, user_id, entity_name, source_document_id, detected_at) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), user_id, lender_name, doc_id, datetime.now(timezone.utc).isoformat())
                )
                await conn.commit()
            logger.info("Flagged entity %s saved to living memory for user %s", lender_name, user_id)

    except Exception as e:
        logger.exception("Failed to analyze document %s", doc_id)
        await doc_repo.update_status(
            doc_id=doc_id,
            user_id=user_id,
            status="FAILED",
            error_message=str(e),
        )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("", response_model=ScanInitResponse, status_code=status.HTTP_202_ACCEPTED)
async def init_scan(
    file: Annotated[UploadFile, File(...)],
    ctx: TenantContext = Depends(get_tenant_context),
) -> ScanInitResponse:
    """Upload a document image and extract text via OCR (Synchronous OCR phase)."""
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise UnsupportedMediaTypeError("Only PDF, JPEG, and PNG are supported")

    content = await file.read()
    
    # Check max size again just in case (though extract_text also does)
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise UnsupportedMediaTypeError(f"File exceeds max size of {MAX_FILE_SIZE_BYTES} bytes")
        
    extracted_text = extract_text(content)
    
    doc_repo = DocumentRepository()
    doc = await doc_repo.create(
        user_id=ctx.user_id,
        original_filename=file.filename or "upload",
        mime_type=file.content_type,
        extracted_text=extracted_text,
        status="PENDING_VERIFICATION",
    )
    
    return ScanInitResponse(
        document_id=doc.id,
        status=doc.status,
        extracted_text=doc.extracted_text,
    )


@router.post("/{document_id}/verify", response_model=VerifyResponse, status_code=status.HTTP_202_ACCEPTED)
async def verify_scan(
    document_id: str,
    body: VerifyRequest,
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(get_tenant_context),
) -> VerifyResponse:
    """Submit HITL verified text and trigger LangGraph analysis."""
    doc_repo = DocumentRepository()
    
    # Ensure doc exists
    doc = await doc_repo.get_by_id(document_id, ctx.user_id)
    
    doc = await doc_repo.update_status(
        doc_id=document_id,
        user_id=ctx.user_id,
        status="ANALYZING",
        verified_text=body.verified_text,
    )
    
    background_tasks.add_task(run_scam_analysis, document_id, ctx.user_id)
    
    return VerifyResponse(
        document_id=doc.id,
        status=doc.status,
    )


@router.get("", response_model=list[ScanStatusResponse])
async def get_history(
    ctx: TenantContext = Depends(get_tenant_context),
) -> list[ScanStatusResponse]:
    """Get all historical scans for the user."""
    doc_repo = DocumentRepository()
    docs = await doc_repo.get_all_for_user(ctx.user_id)
    
    responses = []
    for doc in docs:
        responses.append(ScanStatusResponse(
            document_id=doc.id,
            status=doc.status,
            risk_level=doc.risk_level,
            risk_summary=doc.risk_summary,
            error_message=doc.error_message,
            matched_clauses=[]  # omitting full clause fetch for the list view to stay fast
        ))
    return responses


@router.get("/{document_id}", response_model=ScanStatusResponse)
async def get_scan_status(
    document_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
) -> ScanStatusResponse:
    """Poll for scam analysis status."""
    import lancedb

    from app.core.config import get_settings
    
    doc_repo = DocumentRepository()
    doc = await doc_repo.get_by_id(document_id, ctx.user_id)
    
    matched_clauses = []
    if doc.matched_clause_ids:
        try:
            settings = get_settings()
            db = lancedb.connect(settings.lancedb_path)
            table = db.open_table("predatory_clauses")
            # Fetch the actual clause details using their IDs
            ids_str = ", ".join(f"'{cid}'" for cid in doc.matched_clause_ids)
            # LanceDB SQL filter
            results = table.search().where(f"id IN ({ids_str})").to_list()
            for r in results:
                matched_clauses.append(ClauseMatchResult(
                    clause_category=r["clause_category"],
                    explanation=r["explanation_template"]
                ))
        except Exception as e:
            logger.error("Failed to fetch matched clauses from LanceDB: %s", e)
    
    return ScanStatusResponse(
        document_id=doc.id,
        status=doc.status,
        risk_level=doc.risk_level,
        risk_summary=doc.risk_summary,
        error_message=doc.error_message,
        matched_clauses=matched_clauses,
    )
