"""Bonus B2: tagger rules on hand-built trace events (handoff and trace side).

    python -m pytest -q tests/test_bonus_mast_rules.py
"""

from __future__ import annotations

from bonus.mast_tag import tag_trial


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
