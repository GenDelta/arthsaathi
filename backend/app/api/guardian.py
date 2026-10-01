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

class NudgeFeedbackRequest(BaseModel):
    nudge_id: str
    nudge_type: str
    action: str  # "DISMISS" | "ACCEPT"

@router.post("/feedback")
async def submit_nudge_feedback(
    req: NudgeFeedbackRequest,
    ctx: TenantContext = Depends(get_tenant_context)
):
    """Log user interaction (dismiss/accept) with a nudge for calibration."""
    import uuid
    from datetime import datetime, timezone
    
    db_path = get_settings().database_path
    now = datetime.now(timezone.utc).isoformat()
    feedback_id = str(uuid.uuid4())
    
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """
            INSERT INTO nudge_feedback (id, user_id, nudge_type, action, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (feedback_id, ctx.user_id, req.nudge_type, req.action, now)
        )
        await conn.commit()
    return {"success": True}

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
        
    # Rule 3: Low Savings Rate (Calibrated via Nudge Feedback)
    if inc > 0:
        savings = inc - exp
        savings_rate = savings / inc
        
        # Calibration Agent Logic: Determine current savings target based on feedback
        target_pct = 0.05
        is_muted = False
        
        c_feed = await conn.execute(
            "SELECT action FROM nudge_feedback WHERE user_id = ? AND nudge_type = 'MICRO_SAVINGS' ORDER BY created_at DESC LIMIT 5",
            (ctx.user_id,)
        )
        recent_feedback = await c_feed.fetchall()
        
        if recent_feedback:
            # If the last 3 interactions were DISMISS, user is fatigued. 
            # We either lower the target to 2% or mute it completely.
            actions = [r["action"] for r in recent_feedback]
            dismiss_streak = 0
            for a in actions:
                if a == "DISMISS":
                    dismiss_streak += 1
                else:
                    break
            
            if dismiss_streak >= 5:
                is_muted = True  # Too much fatigue, mute entirely
            elif dismiss_streak >= 3:
                target_pct = 0.02  # Lower the target to 2% to make it achievable
                
        if not is_muted and 0 <= savings_rate < target_pct and not any(n.id == "high_spend_period" for n in nudges):
            disp_target = int(target_pct * 100)
            nudges.append(Nudge(
                id="low_savings_period",
                type="MICRO_SAVINGS",
                title="Boost Your Savings",
                message=f"Your savings rate is looking a bit low ({(savings_rate*100):.1f}%). Try to save at least {disp_target}% of your ₹{inc:,.0f} income.",
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
import asyncio
import json
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse

# In-memory pubsub for SSE (Map of user_id -> list of queues)
_user_queues: dict[str, list[asyncio.Queue]] = {}

def push_guardian_alert(user_id: str, alert: dict):
    """Push an alert to all active SSE connections for a user."""
    if user_id in _user_queues:
        for q in _user_queues[user_id]:
            q.put_nowait(alert)

from fastapi import Request

@router.get("/stream")
async def stream_guardian_alerts(request: Request, ctx: TenantContext = Depends(get_tenant_context)):
    """SSE endpoint for real-time background Guardian alerts."""
    q = asyncio.Queue()
    if ctx.user_id not in _user_queues:
        _user_queues[ctx.user_id] = []
    _user_queues[ctx.user_id].append(q)
    
    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            while True:
                if await request.is_disconnected() or getattr(request.app.state, 'is_shutting_down', False):
                    break
                try:
                    # Timeout periodically to check disconnection
                    alert = await asyncio.wait_for(q.get(), timeout=2.0)
                    yield f"data: {json.dumps(alert)}\n\n"
                except asyncio.TimeoutError:
                    # Send a heartbeat comment to keep the connection alive
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if ctx.user_id in _user_queues and q in _user_queues[ctx.user_id]:
                _user_queues[ctx.user_id].remove(q)
                
    return StreamingResponse(event_stream(), media_type="text/event-stream")

async def run_background_guardian_checks(user_id: str):
    """
    Background worker that runs async checks after a transaction is logged.
    Rules:
    1. Fraud Check (match flagged_entities)
    2. High Spend Check (spending > 120% of income in last 7 days)
    3. Stale Debt Check (no repayment > 60 days)
    """
    db_path = get_settings().database_path
    
    try:
        async with aiosqlite.connect(db_path) as conn:
            conn.row_factory = aiosqlite.Row
            
            # 1. Stale Debt Check
            # Check tracked debts where there is no EXPENSE transaction matching the entity in the last 60 days
            sixty_days_ago = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            
            c = await conn.execute("SELECT id, entity_name FROM tracked_debts WHERE user_id = ?", (user_id,))
            tracked = await c.fetchall()
            
            for tr in tracked:
                entity = tr["entity_name"]
                
                # Check for recent payment
                c_pay = await conn.execute(
                    "SELECT 1 FROM transactions WHERE user_id = ? AND type = 'EXPENSE' AND LOWER(description) LIKE ? AND (occurred_at >= ? OR (occurred_at IS NULL AND created_at >= ?)) LIMIT 1",
                    (user_id, f"%{entity.lower()}%", sixty_days_ago, sixty_days_ago)
                )
                has_recent = await c_pay.fetchone()
                
                if not has_recent:
                    push_guardian_alert(user_id, {
                        "type": "STALE_DEBT",
                        "title": "Stale Debt Warning",
                        "message": f"You haven't logged any repayments to {entity} in over 2 months. Consider making a small payment to avoid penalties."
                    })
            
            # 2. Fraud Check against flagged entities
            c_flag = await conn.execute("SELECT entity_name FROM flagged_entities WHERE user_id = ?", (user_id,))
            flagged = await c_flag.fetchall()
            if flagged:
                flagged_names = [f["entity_name"].lower() for f in flagged]
                
                # Check last 10 transactions
                c_tx = await conn.execute("SELECT description, amount FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,))
                recent_txs = await c_tx.fetchall()
                
                for tx in recent_txs:
                    desc = (tx["description"] or "").lower()
                    for fname in flagged_names:
                        if fname in desc:
                            push_guardian_alert(user_id, {
                                "type": "FRAUD_ALERT",
                                "title": "Predatory Lender Detected",
                                "message": f"A recent transaction (₹{tx['amount']}) matched a flagged predatory lender ({fname.title()}). Please be cautious!"
                            })
                            break

            # 3. High Spend Check
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            c_high = await conn.execute(
                "SELECT SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END) as inc, SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END) as exp FROM transactions WHERE user_id = ? AND (occurred_at >= ? OR (occurred_at IS NULL AND created_at >= ?))",
                (user_id, seven_days_ago, seven_days_ago)
            )
            r_high = await c_high.fetchone()
            inc = r_high["inc"] or 0
            exp = r_high["exp"] or 0
            if exp > 0 and inc > 0 and (exp > inc * 1.2):
                push_guardian_alert(user_id, {
                    "type": "HIGH_SPEND_ALERT",
                    "title": "High Spending Detected",
                    "message": f"Warning: You have spent ₹{exp} recently, which is {(exp/inc)*100:.0f}% of your recent income. Consider slowing down expenses."
                })
    except Exception as e:
        logger.error(f"Background Guardian Check failed: {e}")
