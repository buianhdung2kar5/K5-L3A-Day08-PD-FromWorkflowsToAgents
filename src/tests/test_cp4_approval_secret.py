"""CP4 checks added by the group: broken approvals and secret leakage.

    pytest -q -m student -o addopts= tests/test_cp4_approval_secret.py

The public matrix covers an expired approval (T07), an order that was already refunded (T13)
and an approval lower than the quote (T08). The hidden set also uses a missing approval,
an approval issued for another claim, a revoked approval and a zero amount, so those are built
here by editing a fresh store. Add "orchestrator" to SHAPES_UNDER_TEST once it is implemented.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.shapes import SHAPES
from tests.conftest import CLAIMS, WORLD

SHAPES_UNDER_TEST = ["workflow", "single"]
CLAIM_ID = "C-001"  # order O-107, delayed 4 days, quote 35.000, approval A-001
QUOTE = 35000

# name -> (SQL that breaks the approval, params, reason the host must record)
BROKEN_APPROVALS = {
    "missing_approval": ("UPDATE claims SET approval_id = NULL WHERE claim_id = 'C-001'", (), "missing_approval"),
    "approval_of_another_claim": (
        "UPDATE claims SET approval_id = 'A-003' WHERE claim_id = 'C-001'", (), "approval_claim_mismatch"),
    "approval_row_moved_to_another_claim": (
        "UPDATE approvals SET claim_id = 'C-099' WHERE approval_id = 'A-001'", (), "approval_claim_mismatch"),
    "revoked_approval": (
        "UPDATE approvals SET status = 'revoked' WHERE approval_id = 'A-001'", (), "approval_revoked"),
    "expired_approval": (
        "UPDATE approvals SET expires_at = '2020-01-01' WHERE approval_id = 'A-001'", (), "approval_expired"),
    "zero_amount_approval": (
        "UPDATE approvals SET approved_vnd = 0 WHERE approval_id = 'A-001'", (), "non_positive_amount"),
}


def _store(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


def _execute(store: Path, sql: str, params: tuple = ()) -> None:
    conn = connect(store)
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


@pytest.mark.student
@pytest.mark.parametrize("shape", SHAPES_UNDER_TEST)
@pytest.mark.parametrize("case", sorted(BROKEN_APPROVALS))
def test_broken_approval_never_writes_a_refund(tmp_path, shape, case):
    sql, params, reason = BROKEN_APPROVALS[case]
    store = _store(tmp_path, f"{shape}-{case}.sqlite")
    _execute(store, sql, params)

    result = SHAPES[shape](CLAIM_ID, seed=11, store_path=str(store))

    assert result.status == "denied"
    assert result.proposal_amount == QUOTE, "proposal_amount stays the full quote when the host refuses"
    assert result.refund_effects == []
    assert result.committed_audit_count == 0
    conn = connect(store)
    try:
        rows = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", (CLAIM_ID,)).fetchone()["n"]
        denied = conn.execute(
            "SELECT details_json FROM audit_events WHERE claim_id = ? AND event_type = 'policy_denied'", (CLAIM_ID,)
        ).fetchall()
    finally:
        conn.close()
    assert rows == 0
    assert len(denied) == 1, "a refused quote above zero needs exactly one policy_denied audit"
    assert json.loads(denied[0]["details_json"])["reason"] == reason


def _sensitive_tokens() -> list[str]:
    """Everything that must never appear in a trace, a result or stdout."""
    tokens: list[str] = []
    for order in WORLD["orders"]:
        tokens += [str(order[k]) for k in ("phone", "address", "internal_note", "item_name") if order.get(k)]
    for claim in CLAIMS:
        tokens.append(str(claim["parent_secret"]))
        tokens += [str(v) for v in (claim.get("raw_headers") or {}).values()]
    return sorted(set(tokens))


def _contains(text: str, token: str) -> bool:
    """Whole-token match, so a short item name such as 'Ghe' is not found inside another word."""
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])", text) is not None


@pytest.mark.student
@pytest.mark.parametrize("shape", SHAPES_UNDER_TEST)
@pytest.mark.parametrize("seed", [11, 55])
def test_no_secret_or_personal_data_leaves_the_shape(tmp_path, capsys, shape, seed):
    tokens = _sensitive_tokens()
    for claim in CLAIMS:
        cid = claim["claim_id"]
        store = _store(tmp_path, f"{shape}-{cid}-{seed}.sqlite")
        result = SHAPES[shape](cid, seed=seed, store_path=str(store))

        trace_path = Path(result.trace_path)
        files = [trace_path] + sorted(trace_path.parent.glob(f"{result.run_id}*"))
        text = json.dumps(result.as_dict(), ensure_ascii=False)
        text += "".join(p.read_text(encoding="utf-8") for p in set(files) if p.is_file())
        leaked = [t for t in tokens if _contains(text, t)]
        assert not leaked, f"{shape} {cid} seed {seed} leaked {leaked}"

    captured = capsys.readouterr()
    assert not [t for t in tokens if _contains(captured.out + captured.err, t)], "a shape printed sensitive data"
