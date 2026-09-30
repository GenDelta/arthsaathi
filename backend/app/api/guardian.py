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

# ─── Endpoints ────────────────────────────────────────────────────────────────

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
