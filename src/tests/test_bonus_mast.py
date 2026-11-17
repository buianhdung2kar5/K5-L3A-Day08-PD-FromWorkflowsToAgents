"""Bonus B2: MAST tagger rules and the broken variants they are tested against.

    python -m pytest -q tests/test_bonus_mast.py
"""

from __future__ import annotations

import pytest

from bonus import broken_shapes
from bonus.mast_tag import cohens_kappa, load_events, tag_trial
from lab8.db import connect, init_store
from tests.conftest import CLAIMS, WORLD

VARIANTS = {
    "handoff_drops_delay": ("FC2", broken_shapes.handoff_drops_delay),
    "stale_policy": ("FC1", broken_shapes.stale_policy),
    "ignores_host_result": ("FC3", broken_shapes.ignores_host_result),
}


def _store(tmp_path, name):
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


def _wrong(result, claim) -> bool:
    expected = claim["expected"]
    return result.status != expected["status"] or result.proposal_amount != expected["proposal_amount"]


@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_each_variant_fails_somewhere_and_is_tagged_with_its_group(tmp_path, monkeypatch, variant):
    group, run_claim = VARIANTS[variant]
    monkeypatch.chdir(tmp_path)
    failed = 0
    for claim in CLAIMS:
        store = _store(tmp_path, f"{variant}-{claim['claim_id']}.sqlite")
        result = run_claim(claim["claim_id"], seed=11, store_path=str(store))
        if not _wrong(result, claim):
            continue
        failed += 1
        trial = {"status": result.status, "run_id": result.run_id}
        tag = tag_trial(trial, load_events(result.trace_path))
        assert tag["category"] == group, f"{variant} {claim['claim_id']}: {tag}"
    assert failed >= 1, f"{variant} never produced a wrong result, so the tagger was not exercised"


def test_a_correct_run_is_not_tagged(tmp_path, monkeypatch):
    from lab8.shapes import SHAPES

    monkeypatch.chdir(tmp_path)
    for claim in CLAIMS:
        store = _store(tmp_path, f"wf-{claim['claim_id']}.sqlite")
        result = SHAPES["workflow"](claim["claim_id"], seed=11, store_path=str(store))
        assert not _wrong(result, claim)
        tag = tag_trial({"status": result.status}, load_events(result.trace_path))
        assert tag["category"] == "unclassified"


def test_override_event_is_verification_failure_and_missing_trace_is_system_design():
    events = [{"kind": "model_override", "payload": {"delay_days": 5}}, {"kind": "quote", "payload": {}}]
    assert tag_trial({"status": "resolved"}, events)["category"] == "FC3"
    assert tag_trial({"status": "error"}, [])["category"] == "FC1"


def test_handoff_that_matches_the_order_row_is_not_misalignment():
    events = [
        {"kind": "order", "payload": {"visible": True, "delay_days": 4}},
        {"kind": "handoff", "payload": {"facts": {"delay_days": 4}}},
    ]
    assert tag_trial({"status": "denied"}, events)["category"] == "unclassified"


def test_cohens_kappa_known_values():
    assert cohens_kappa(["FC1", "FC2"], ["FC1", "FC2"]) == 1.0
    assert cohens_kappa(["FC1", "FC1", "FC2", "FC2"], ["FC1", "FC2", "FC1", "FC2"]) == 0.0
