import json
from pathlib import Path

from lab8.shapes.orchestrator import run_claim


def test_orchestrator_traces_a_read_only_handoff(
    public_db, tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)

    result = run_claim("C-001", seed=11, store_path=str(public_db))

    assert result.status == "resolved"
    trace_json = Path(result.trace_path).read_text(encoding="utf-8")
    trace = json.loads(trace_json)
    assert trace["run_id"] == result.run_id

    (handoff,) = [
        event["payload"] for event in trace["events"] if event["kind"] == "handoff"
    ]
    assert handoff["claim_id"] == result.claim_id
    assert handoff["allowed_tools"] == ["lookup_order", "compute_compensation"]
    assert handoff["facts"] == {}

    console = capsys.readouterr()
    for source in (trace_json, console.out, console.err):
        assert "CANARY_SECRET_" not in source
