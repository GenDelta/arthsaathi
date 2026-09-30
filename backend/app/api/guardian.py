"""Guardian API router for ArthSaathi.

Generates deterministic financial nudges and insights based on transaction history.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiosqlite
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.dependencies import TenantContext, get_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guardian", tags=["guardian"])

# ─── Models ───────────────────────────────────────────────────────────────────

class Nudge(BaseModel):
    id: str
    type: str  # "GUARDIAN_ALERT" | "MICRO_SAVINGS" | "INFO"
    title: str
    message: str
    actionLabel: str

class NudgesResponse(BaseModel):
    nudges: list[Nudge]

class TrackDebtRequest(BaseModel):
    entity_name: str
    total_amount: float

# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/track-debt")
async def track_debt(
    req: TrackDebtRequest,
    ctx: TenantContext = Depends(get_tenant_context)  # noqa: B008
):
    """Start tracking a specific informal or formal debt entity."""
    import uuid
    db_path = get_settings().database_path
    async with aiosqlite.connect(db_path) as conn:
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
        debt_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO tracked_debts (id, user_id, entity_name, total_amount, created_at) VALUES (?, ?, ?, ?, ?)",
            (debt_id, ctx.user_id, req.entity_name, req.total_amount, datetime.utcnow().isoformat())
        )
        await conn.commit()
    return {"success": True, "id": debt_id}

@router.get("/nudges", response_model=NudgesResponse)
async def get_nudges(
    start_date: str | None = None,
    end_date: str | None = None,
    ctx: TenantContext = Depends(get_tenant_context)  # noqa: B008
) -> NudgesResponse:
    """Generate dynamic nudges based on user's selected date period."""
    db_path = get_settings().database_path
    
    nudges: list[Nudge] = []
    
    clauses: list[str] = ["user_id = ?"]
    params: list[Any] = [ctx.user_id]

    if start_date:
        clauses.append("(occurred_at >= ? OR (occurred_at IS NULL AND created_at >= ?))")
        params.extend([start_date, start_date])
    if end_date:
        clauses.append("(occurred_at <= ? OR (occurred_at IS NULL AND created_at <= ?))")
        params.extend([end_date, end_date + "T23:59:59"])

    where = " AND ".join(clauses)
    
    async with aiosqlite.connect(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, type TEXT NOT NULL,
                category TEXT NOT NULL, amount REAL NOT NULL, currency TEXT NOT NULL DEFAULT 'INR',
                description TEXT, occurred_at TEXT, created_at TEXT NOT NULL
            )
            """
        )
        
        # Query: Period Totals
        c = await conn.execute(
            f"""
            SELECT 
                COALESCE(SUM(CASE WHEN type='INCOME' THEN amount ELSE 0 END), 0) as inc,
                COALESCE(SUM(CASE WHEN type='EXPENSE' THEN amount ELSE 0 END), 0) as exp
            FROM transactions WHERE {where}
            """,
            params
        )
        row = await c.fetchone()
        inc, exp = row["inc"], row["exp"]
        
        # Query: Debt repayment in period
        c_debt = await conn.execute(
            f"""
            SELECT COALESCE(SUM(amount), 0) as debt
            FROM transactions 
            WHERE category = 'DEBT_REPAYMENT' AND {where}
            """,
            params
        )
        row_debt = await c_debt.fetchone()
        debt = row_debt["debt"]

        # Query: Specific Tracked Debts
        # Ensure tracked_debts table exists first (in case track_debt hasn't been called)
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
        c_tracked = await conn.execute(
            "SELECT id, entity_name, total_amount FROM tracked_debts WHERE user_id = ?",
            (ctx.user_id,)
        )
        tracked_rows = await c_tracked.fetchall()
        
        tracked_progress = []
        for tr in tracked_rows:
            entity = tr["entity_name"]
            
            # Additional loans taken (INCOME)
            c_inc = await conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as additional FROM transactions WHERE user_id = ? AND type = 'INCOME' AND LOWER(description) LIKE ?",
                (ctx.user_id, f"%{entity.lower()}%")
            )
            r_inc = await c_inc.fetchone()
            
            # Total paid all time
            c_tot = await conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as paid FROM transactions WHERE user_id = ? AND type = 'EXPENSE' AND LOWER(description) LIKE ?",
                (ctx.user_id, f"%{entity.lower()}%")
            )
            r_tot = await c_tot.fetchone()
            
            # Total paid in this period
            c_per = await conn.execute(
                f"SELECT COALESCE(SUM(amount), 0) as paid FROM transactions WHERE type = 'EXPENSE' AND LOWER(description) LIKE ? AND {where}",
                [f"%{entity.lower()}%"] + params
            )
            r_per = await c_per.fetchone()
            
            tracked_progress.append({
                "id": tr["id"],
                "entity": entity,
                "target": tr["total_amount"] + r_inc["additional"],
                "paid_total": r_tot["paid"],
                "paid_period": r_per["paid"]
            })

    # Rule 0: Tracked Debts
    for tp in tracked_progress:
        pct = (tp["paid_total"] / tp["target"]) * 100 if tp["target"] > 0 else 0
        nudges.append(Nudge(
            id=f"tracked_debt_{tp['id']}",
            type="INFO",
            title=f"Debt Progress: {tp['entity'].title()}",
            message=f"You've paid ₹{tp['paid_period']:,.0f} to {tp['entity'].title()} in this period. Overall progress: ₹{tp['paid_total']:,.0f} / ₹{tp['target']:,.0f} ({pct:.0f}%).",
            actionLabel="View Details"
        ))

    # Rule 1: High Spending Alert (Expenses > 70% of income)
    if inc > 0 and exp > (0.7 * inc):
        pct = int((exp / inc) * 100)
        nudges.append(Nudge(
            id="high_spend_period",
            type="GUARDIAN_ALERT",
            title="High Spending Detected",
            message=f"You've spent {pct}% of your income in this period (₹{exp:,.0f} out of ₹{inc:,.0f}).",
            actionLabel="Review"
        ))
        
    # Rule 2: Dry spell (No income, but had expenses)
    if inc == 0 and exp > 0:
        nudges.append(Nudge(
            id="dry_spell_period",
            type="GUARDIAN_ALERT",
            title="Dry Spell Detected",
            message=f"No income recorded in this period, but you had ₹{exp:,.0f} in expenses.",
            actionLabel="View Schemes"
        ))
        
    # Rule 3: Low Savings Rate (< 5%)
    if inc > 0:
        savings = inc - exp
        savings_rate = savings / inc
        if 0 <= savings_rate < 0.05 and not any(n.id == "high_spend_period" for n in nudges):
            nudges.append(Nudge(
                id="low_savings_period",
                type="MICRO_SAVINGS",
                title="Boost Your Savings",
                message=f"Your savings rate is looking a bit low ({(savings_rate*100):.1f}%). Try to save at least 5% of your ₹{inc:,.0f} income.",
                actionLabel="Save Now"
            ))
            
    # Rule 4: Debt tracking
    if debt > 0:
        nudges.append(Nudge(
            id="debt_track_period",
            type="INFO",
            title="Debt Repayment On Track",
            message=f"You've paid ₹{debt:,.0f} towards your loans in this period. Keep it up!",
            actionLabel="View Details"
        ))

    # Fallback if no rules hit
    if not nudges and inc == 0 and exp == 0:
        nudges.append(Nudge(
            id="welcome_log",
            type="INFO",
            title="Welcome to Guardian",
            message="Upload a bank statement or use voice logs to start getting personalized financial insights.",
            actionLabel="Upload PDF"
        ))

    return NudgesResponse(nudges=nudges)
