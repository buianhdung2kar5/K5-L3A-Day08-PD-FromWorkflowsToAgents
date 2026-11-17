"""Deliberately broken shapes for the MAST tagging bonus (B2).

Each variant copies the workflow flow and injects exactly one defect. They are test
fixtures for the tagger, not candidates for submission. The host (durability.issue_refund)
is still the only writer, so none of them can bypass approval or the per-order cap.

    handoff_drops_delay   the handoff to the quote step loses delay_days      (inter-agent)
    stale_policy          the quote also reads superseded policies            (spec)
    ignores_host_result   reports resolved even when the host refused         (verification)
"""

from __future__ import annotations

import json

from lab8.compensation import quote as quote_order
from lab8.config_loader import as_of
from lab8.db import connect
from lab8.durability import issue_refund
from lab8.runtime import dispatch
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import _policy_dict
from lab8.trace import Trace


def _run(shape: str, claim_id: str, seed: int, store_path: str, crash_at: str | None) -> RunResult:
    conn = connect(store_path)
    try:
        return _flow(conn, shape, claim_id, seed, crash_at)
    finally:
        conn.close()


def _finish(conn, shape, claim_id, seed, status, amount, budget, trace, reason=None) -> RunResult:
    return finish(
        conn, shape=shape, claim_id=claim_id, seed=seed, status=status,
        proposal_amount=amount, budget=budget, trace=trace, error_reason=reason,
    )


def _flow(conn, shape: str, claim_id: str, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(shape, claim_id, seed))

    claim = dispatch(conn, budget, "get_claim_view", {"claim_id": claim_id}, worker=False)
    if not claim.get("found"):
        return _finish(conn, shape, claim_id, seed, "failed", 0, budget, trace, "unknown_claim")
    if not claim.get("order_id"):
        return _finish(conn, shape, claim_id, seed, "needs_info", 0, budget, trace)
    scope = dispatch(
        conn, budget, "lookup_order",
        {"order_id": claim["order_id"], "principal_id": claim["principal_id"]}, worker=False,
    )
    if not scope.get("visible"):
        return _finish(conn, shape, claim_id, seed, "escalated", 0, budget, trace)
    order = dict(scope["order"])
    trace.add("order", {"visible": True, "delay_days": int(order["delay_days"])})

    if shape == "handoff_drops_delay":
        # Defect: the facts handed to the quote step omit the delay, which falls back to 0.
        trace.add("handoff", {"facts": {"delay_days": 0}})
        order["delay_days"] = 0

    if shape == "stale_policy":
        # Defect: every policy row is read, including superseded ones, and all count as current.
        rows = conn.execute("SELECT * FROM policies").fetchall()
        policies = [{**_policy_dict(row), "is_current": True} for row in rows]
        stale = [p["policy_id"] for p in policies if not _policy_dict_current(conn, p["policy_id"])]
        trace.add("policy_used", {"policy_ids": [p["policy_id"] for p in policies], "non_current": stale})
        q = quote_order(order, policies, as_of=as_of())
        amount, reason = int(q.amount_vnd), q.reason
    else:
        q = dispatch(conn, budget, "compute_compensation", {"order": order}, worker=False)
        amount, reason = int(q["amount_vnd"]), q.get("reason")
    trace.add("quote", {"amount_vnd": amount, "reason": reason})
    if amount <= 0:
        return _finish(conn, shape, claim_id, seed, "denied", 0, budget, trace)

    result = issue_refund(conn, claim_id, amount, crash_at=crash_at)
    trace.add("host", {"ok": result["ok"], "reason": result["reason"], "conflict": result["conflict"]})
    if result["ok"]:
        return _finish(conn, shape, claim_id, seed, "resolved", amount, budget, trace)
    if shape == "ignores_host_result":
        # Defect: the host's refusal is never checked before reporting success.
        return _finish(conn, shape, claim_id, seed, "resolved", amount, budget, trace)
    status = "failed" if result["conflict"] else "denied"
    return _finish(conn, shape, claim_id, seed, status, amount, budget, trace, result["reason"])


def _policy_dict_current(conn, policy_id: str) -> bool:
    row = conn.execute("SELECT is_current FROM policies WHERE policy_id = ?", (policy_id,)).fetchone()
    return bool(row["is_current"])


def handoff_drops_delay(claim_id, *, seed, store_path, crash_at=None):
    return _run("handoff_drops_delay", claim_id, seed, store_path, crash_at)


def stale_policy(claim_id, *, seed, store_path, crash_at=None):
    return _run("stale_policy", claim_id, seed, store_path, crash_at)


def ignores_host_result(claim_id, *, seed, store_path, crash_at=None):
    return _run("ignores_host_result", claim_id, seed, store_path, crash_at)
