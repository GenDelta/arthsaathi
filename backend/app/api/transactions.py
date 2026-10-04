"""Transactions API router for ArthSaathi.

Endpoints:
    GET  /api/transactions              — list & filter transactions with summary
    POST /api/transactions/upload-pdf   — parse a bank-statement PDF and persist
    POST /api/transactions/voice        — NLP voice-entry to transaction
    DELETE /api/transactions/{id}       — delete a single transaction
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import aiosqlite
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, BackgroundTasks
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.dependencies import TenantContext, get_tenant_context
from app.core.llm import get_llm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])

# ─── Helpers ──────────────────────────────────────────────────────────────────

from datetime import datetime, timezone, timedelta

def _utcnow() -> str:
    # Use IST (UTC+5:30) so string comparisons with YYYY-MM-DD work correctly
    # for Indian gig workers, aligning with frontend's local date filters.
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(tz=ist).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


async def _ensure_transactions_table(conn: aiosqlite.Connection) -> None:
    """Create the transactions table if it does not exist yet."""
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id           TEXT PRIMARY KEY,
            user_id      TEXT NOT NULL,
            type         TEXT NOT NULL,
            category     TEXT NOT NULL,
            amount       REAL NOT NULL,
            currency     TEXT NOT NULL DEFAULT 'INR',
            description  TEXT,
            occurred_at  TEXT,
            created_at   TEXT NOT NULL
        )
        """
    )
    await conn.commit()


def _row_to_dict(row: aiosqlite.Row) -> dict[str, Any]:
    return dict(row)


# ─── Pydantic models ──────────────────────────────────────────────────────────

class TransactionOut(BaseModel):
    id: str
    user_id: str
    type: str
    category: str
    amount: float
    currency: str
    description: str | None
    occurred_at: str | None
    created_at: str


class TransactionSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    count: int


class TransactionListResponse(BaseModel):
    transactions: list[TransactionOut]
    summary: TransactionSummary
    total: int
    page: int
    page_size: int
    total_pages: int


class UploadPdfResponse(BaseModel):
    inserted: int
    transactions: list[TransactionOut]


class VoiceRequest(BaseModel):
    text: str


class VoiceResponse(BaseModel):
    transaction: TransactionOut


class CategoryBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float


class BreakdownResponse(BaseModel):
    income: list[CategoryBreakdown]
    expense: list[CategoryBreakdown]


# ─── GET /api/transactions/breakdown ──────────────────────────────────────────

@router.get("/breakdown", response_model=BreakdownResponse)
async def get_breakdown(
    start_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    end_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    ctx: TenantContext = Depends(get_tenant_context),  # noqa: B008
) -> BreakdownResponse:
    """Get spending and income breakdown by category for a period."""
    db_path = get_settings().database_path
    clauses: list[str] = ["user_id = ?"]
    params: list[Any] = [ctx.user_id]

    if start_date:
        clauses.append("(occurred_at >= ? OR (occurred_at IS NULL AND created_at >= ?))")
        params.extend([start_date, start_date])

    if end_date:
        end_dt_full = end_date + "T23:59:59"
        clauses.append("(occurred_at <= ? OR (occurred_at IS NULL AND created_at <= ?))")
        params.extend([end_dt_full, end_dt_full])

    where = " AND ".join(clauses)
    
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await _ensure_transactions_table(conn)
        
        cursor = await conn.execute(
            f"SELECT type, category, SUM(amount) as total "
            f"FROM transactions WHERE {where} "
            f"GROUP BY type, category ORDER BY total DESC",
            params,
        )
        rows = await cursor.fetchall()

    income_total = sum(r["total"] for r in rows if r["type"] == "INCOME")
    expense_total = sum(r["total"] for r in rows if r["type"] == "EXPENSE")

    income_list = []
    expense_list = []

    for r in rows:
        amt = r["total"]
        if r["type"] == "INCOME":
            pct = (amt / income_total * 100) if income_total > 0 else 0
            income_list.append(CategoryBreakdown(category=r["category"], amount=round(amt, 2), percentage=round(pct, 1)))
        else:
            pct = (amt / expense_total * 100) if expense_total > 0 else 0
            expense_list.append(CategoryBreakdown(category=r["category"], amount=round(amt, 2), percentage=round(pct, 1)))

    return BreakdownResponse(income=income_list, expense=expense_list)


# ─── GET /api/transactions ────────────────────────────────────────────────────


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    type: str | None = Query(default=None, description="INCOME | EXPENSE | all"),  # noqa: A002
    category: str | None = Query(default=None),
    query: str | None = Query(default=None, description="Search transaction descriptions"),
    start_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    end_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    ctx: TenantContext = Depends(get_tenant_context),  # noqa: B008
) -> TransactionListResponse:
    """List transactions for the authenticated user with optional filters and pagination."""
    db_path = get_settings().database_path

    clauses: list[str] = ["user_id = ?"]
    params: list[Any] = [ctx.user_id]

    if type and type.upper() != "ALL":
        clauses.append("type = ?")
        params.append(type.upper())

    if category:
        clauses.append("category = ?")
        params.append(category.upper())

    if query:
        clauses.append("LOWER(description) LIKE ?")
        params.append(f"%{query.lower()}%")

    # Filter by occurred_at (ISO YYYY-MM-DD stored by parser) with created_at fallback
    if start_date:
        clauses.append("(occurred_at >= ? OR (occurred_at IS NULL AND created_at >= ?))")
        params.extend([start_date, start_date])

    if end_date:
        end_dt_full = end_date + "T23:59:59"
        clauses.append("(occurred_at <= ? OR (occurred_at IS NULL AND created_at <= ?))")
        params.extend([end_dt_full, end_dt_full])

    where = " AND ".join(clauses)

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        await _ensure_transactions_table(conn)

        # Total count + summary for ALL matching rows (not just current page)
        count_cursor = await conn.execute(
            f"SELECT COUNT(*), COALESCE(SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END),0), "
            f"COALESCE(SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END),0) "
            f"FROM transactions WHERE {where}",
            params,
        )
        total_count, total_income, total_expenses = await count_cursor.fetchone()

        # Paginated rows
        offset = (page - 1) * page_size
        page_cursor = await conn.execute(
            f"SELECT * FROM transactions WHERE {where} "
            f"ORDER BY occurred_at DESC, created_at DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        )
        rows = await page_cursor.fetchall()

    total_count = total_count or 0
    total_pages = max(1, -(-total_count // page_size))  # ceiling division

    tx_list = [TransactionOut(**_row_to_dict(r)) for r in rows]

    return TransactionListResponse(
        transactions=tx_list,
        summary=TransactionSummary(
            total_income=round(total_income or 0, 2),
            total_expenses=round(total_expenses or 0, 2),
            net_savings=round((total_income or 0) - (total_expenses or 0), 2),
            count=total_count,
        ),
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ─── POST /api/transactions/upload-pdf ───────────────────────────────────────

@router.post("/upload-pdf", response_model=UploadPdfResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    password: str | None = Form(default=None),
    background_tasks: BackgroundTasks = None,
    ctx: TenantContext = Depends(get_tenant_context),  # noqa: B008
) -> UploadPdfResponse:
    """Parse a bank-statement PDF and persist extracted transactions."""
    from app.services.pdf_parser import parse_bank_statement  # local import to keep startup fast

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        parsed = parse_bank_statement(file_bytes, password=password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not parsed:
        return UploadPdfResponse(inserted=0, transactions=[])

    parsed_txs = parsed.get("transactions", [])
    full_text = parsed.get("full_text", "")
    
    db_path = get_settings().database_path
    now = _utcnow()
    inserted_txs: list[TransactionOut] = []

    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        # PRIVACY CHECK 1: Cryptographic Account Binding
        account_number = parsed.get("account_number")
        if account_number:
            import hashlib
            secret = get_settings().jwt_secret
            hmac_hash = hashlib.sha256(f"{account_number}:{secret}".encode()).hexdigest()
            
            c_acct = await conn.execute("SELECT user_id FROM account_bindings WHERE account_hmac = ?", (hmac_hash,))
            existing_binding = await c_acct.fetchone()
            
            if existing_binding:
                if existing_binding["user_id"] != ctx.user_id:
                    raise HTTPException(
                        status_code=403,
                        detail="Privacy Check Failed: This bank account is already registered to another user."
                    )
            else:
                # Bind this account to the current user
                binding_id = str(uuid.uuid4())
                await conn.execute(
                    "INSERT INTO account_bindings (id, user_id, account_hmac, account_last4, created_at) VALUES (?, ?, ?, ?, ?)",
                    (binding_id, ctx.user_id, hmac_hash, account_number[-4:], datetime.now(timezone.utc).isoformat())
                )
        
        # PRIVACY CHECK 2: Name Verification (Fallback and Extra Security)
        cursor = await conn.execute(
            "SELECT legal_name FROM user_profiles WHERE user_id = ?",
            (ctx.user_id,)
        )
        row = await cursor.fetchone()
        if row and row["legal_name"]:
            legal_name = row["legal_name"]
            if legal_name.strip():
                header_text = full_text[:1500]
                # Pre-filter: if name isn't even in the top 1500, fast fail
                if legal_name.lower() not in header_text.lower():
                    raise HTTPException(
                        status_code=403,
                        detail=f"Privacy Check Failed: We could not find your registered bank statement name '{legal_name}' in this PDF. To protect your privacy, we only process your own statements."
                    )
                
                # LLM Verification: Ensure they are actually the account holder, not just a transaction recipient
                from app.core.llm import get_llm
                llm = get_llm(temperature=0.0)
                prompt = f"""You are a strict bank statement analyzer.
Extract the exact name of the PRIMARY ACCOUNT HOLDER from this bank statement header.
Return ONLY the name, nothing else. If you cannot find it, return 'UNKNOWN'.

Bank Statement Header:
{header_text}
"""
                response = await llm.ainvoke(prompt)
                extracted_name = str(response.content).strip().lower()
                
                # Check if the legal_name is part of the extracted name (e.g. "ankush dutta" in "mr. ankush dutta")
                # or vice-versa (e.g. "ankush" in "ankush dutta")
                name_parts = legal_name.lower().split()
                matches = any(part in extracted_name for part in name_parts if len(part) > 2)
                
                if not matches and extracted_name != "unknown":
                    raise HTTPException(
                        status_code=403,
                        detail=f"Privacy Check Failed: The account holder appears to be '{extracted_name.title()}', not you."
                    )

        await _ensure_transactions_table(conn)

        import hashlib
        seen_hashes = {}

        for item in parsed_txs:
            occurred_at = item.get("date") or now
            tx_type = item["type"]
            category = _normalise_category(item.get("category", "OTHER"), tx_type)
            amount = float(item["amount"])
            desc = item.get("description", "")

            # Create a deterministic fingerprint for this transaction
            base_string = f"{ctx.user_id}|{occurred_at}|{tx_type}|{amount}|{desc}"
            count = seen_hashes.get(base_string, 0)
            seen_hashes[base_string] = count + 1
            
            fingerprint = f"{base_string}|{count}"
            tx_id = hashlib.md5(fingerprint.encode("utf-8")).hexdigest()

            cursor = await conn.execute(
                "SELECT 1 FROM transactions WHERE id = ?", (tx_id,)
            )
            if await cursor.fetchone():
                continue

            await conn.execute(
                """
                INSERT INTO transactions (id, user_id, type, category, amount, currency, description, occurred_at, created_at)
                VALUES (?, ?, ?, ?, ?, 'INR', ?, ?, ?)
                """,
                (tx_id, ctx.user_id, tx_type, category, amount, desc, occurred_at, now)
            )

            inserted_txs.append(
                TransactionOut(
                    id=tx_id,
                    user_id=ctx.user_id,
                    type=tx_type,
                    category=category,
                    amount=amount,
                    currency="INR",
                    description=desc,
                    occurred_at=occurred_at,
                    created_at=now,
                )
            )

        await conn.commit()
        
        # Fire background guardian scan
        if inserted_txs and background_tasks:
            from app.api.guardian import run_background_guardian_checks
            background_tasks.add_task(run_background_guardian_checks, ctx.user_id)

    return UploadPdfResponse(inserted=len(inserted_txs), transactions=inserted_txs)

_INCOME_CATEGORIES = {"GIG_WAGE", "AGRICULTURAL_SALE", "OTHER_INCOME"}
_EXPENSE_CATEGORIES = {"FOOD", "TRANSPORT", "UTILITIES", "DEBT_REPAYMENT", "DISCRETIONARY", "HEALTHCARE", "OTHER_EXPENSE"}

_CATEGORY_ALIASES = {
    "SALARY": "OTHER_INCOME",
    "TRANSFER": "OTHER_INCOME",
    "INTEREST": "OTHER_INCOME",
    "REFUND": "OTHER_INCOME",
    "CASHBACK": "OTHER_INCOME",
    "LOAN_RECEIVED": "OTHER_INCOME",
    "RENT": "UTILITIES",
    "LOAN_REPAYMENT": "DEBT_REPAYMENT",
    "MEDICAL": "HEALTHCARE",
    "ENTERTAINMENT": "DISCRETIONARY",
    "EDUCATION": "DISCRETIONARY",
    "SHOPPING": "DISCRETIONARY",
    "FEE": "OTHER_EXPENSE",
    "CASH_WITHDRAWAL": "OTHER_EXPENSE",
    "UTILITY": "UTILITIES",
    "ATM": "OTHER_EXPENSE",
    "DEPOSIT": "OTHER_INCOME",
    "GIG": "GIG_WAGE",
    "GROCERY": "FOOD",
    "RESTAURANT": "FOOD",
    "OTHER": "OTHER_EXPENSE",
    "LOAN_RECEIVED": "OTHER_INCOME"
}

def _normalise_category(raw: str, tx_type: str) -> str:
    c = raw.upper().strip()
    if tx_type == "INCOME":
        if c in _INCOME_CATEGORIES:
            return c
        return _CATEGORY_ALIASES.get(c, "OTHER_INCOME")
    else:
        if c in _EXPENSE_CATEGORIES:
            return c
        return _CATEGORY_ALIASES.get(c, "OTHER_EXPENSE")


_VOICE_EXTRACTION_PROMPT = """
You are a financial extraction API. Extract the transaction details from the user's message.
Output ONLY raw JSON with no markdown formatting.

Categories must strictly be one of:
INCOME: GIG_WAGE, AGRICULTURAL_SALE, OTHER_INCOME, LOAN_RECEIVED
EXPENSE: FOOD, TRANSPORT, UTILITIES, DEBT_REPAYMENT, DISCRETIONARY, HEALTHCARE, OTHER_EXPENSE

*Note: If the user states they TOOK or RECEIVED a loan, the type MUST be INCOME and the category MUST be LOAN_RECEIVED. If they are PAYING OFF a loan, type is EXPENSE and category is DEBT_REPAYMENT.

JSON Schema:
{{
    "type": "INCOME" | "EXPENSE",
    "amount": float,
    "description": "Short clean summary",
    "category": "ONE OF THE CATEGORIES ABOVE"
}}

User Message: {text}
"""

@router.post("/voice", response_model=VoiceResponse)
async def voice_transaction(
    body: VoiceRequest,
    background_tasks: BackgroundTasks,
    ctx: TenantContext = Depends(get_tenant_context),  # noqa: B008
) -> VoiceResponse:
    """Convert a natural-language voice entry to a transaction using an LLM."""
    llm = get_llm(temperature=0.0)
    prompt = _VOICE_EXTRACTION_PROMPT.format(text=body.text)

    try:
        response = await llm.ainvoke(prompt)
        raw_json = response.content.strip()

        # Strip markdown code fences if the model wrapped the JSON
        if raw_json.startswith("```"):
            raw_json = re.sub(r"^```[a-z]*\n?", "", raw_json).rstrip("`").strip()

        extracted: dict[str, Any] = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        logger.warning("LLM returned non-JSON for voice input %r: %s", body.text, exc)
        raise HTTPException(
            status_code=422,
            detail="Could not parse LLM response as JSON. Try rephrasing your input.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("LLM call failed for voice transaction: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="LLM service unavailable.") from exc

    tx_type = str(extracted.get("type", "EXPENSE")).upper()
    if tx_type not in {"INCOME", "EXPENSE"}:
        tx_type = "EXPENSE"

    amount = float(extracted.get("amount", 0))
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Could not extract a valid amount.")

    description = str(extracted.get("description", body.text))[:500]
    raw_category = str(extracted.get("category", "OTHER"))
    category = _normalise_category(raw_category, tx_type)

    db_path = get_settings().database_path
    now = _utcnow()
    tx_id = _new_id()

    async with aiosqlite.connect(db_path) as conn:
        await _ensure_transactions_table(conn)
        await conn.execute(
            """
            INSERT INTO transactions
                (id, user_id, type, category, amount, currency, description, occurred_at, created_at)
            VALUES (?, ?, ?, ?, ?, 'INR', ?, ?, ?)
            """,
            (tx_id, ctx.user_id, tx_type, category, amount, description, now, now),
        )
        
        if raw_category.upper().strip() == "LOAN_RECEIVED":
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tracked_debts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            entity = description.lower().replace("loan from ", "").strip().title()
            if not entity or entity == "Loan":
                entity = "Unknown Lender"
            
            # Check if tracker already exists
            c_chk = await conn.execute("SELECT id FROM tracked_debts WHERE user_id = ? AND LOWER(entity_name) = ?", (ctx.user_id, entity.lower()))
            if not await c_chk.fetchone():
                debt_id = str(uuid.uuid4())
                await conn.execute(
                    "INSERT INTO tracked_debts (id, user_id, entity_name, total_amount, created_at) VALUES (?, ?, ?, ?, ?)",
                    (debt_id, ctx.user_id, entity, amount, now)
                )

        await conn.commit()

    # Trigger background async checks
    from app.api.guardian import run_background_guardian_checks
    background_tasks.add_task(run_background_guardian_checks, ctx.user_id)

    tx_out = TransactionOut(
        id=tx_id,
        user_id=ctx.user_id,
        type=tx_type,
        category=category,
        amount=amount,
        currency="INR",
        description=description,
        occurred_at=now,
        created_at=now,
    )
    logger.info("Voice transaction created: %s for user %s", tx_id, ctx.user_id)
    return VoiceResponse(transaction=tx_out)


# ─── DELETE /api/transactions/{transaction_id} ────────────────────────────────

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    ctx: TenantContext = Depends(get_tenant_context),  # noqa: B008
) -> dict[str, bool]:
    """Delete a transaction (only if it belongs to the requesting user)."""
    db_path = get_settings().database_path

    async with aiosqlite.connect(db_path) as conn:
        await _ensure_transactions_table(conn)
        # Verify ownership before deleting
        cursor = await conn.execute(
            "SELECT id FROM transactions WHERE id = ? AND user_id = ?",
            (transaction_id, ctx.user_id),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found or does not belong to this user.",
            )

        await conn.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?",
            (transaction_id, ctx.user_id),
        )
        await conn.commit()

    logger.info("Deleted transaction %s for user %s", transaction_id, ctx.user_id)
    return {"success": True}
