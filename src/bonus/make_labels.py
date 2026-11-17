"""Write bonus/labels.json: the MAST group of every failed trial, set by the injected defect.

Labels come from how each variant was built (see broken_shapes.py), not from the tagger.
The swarm trial is labelled from the reference weakness documented in src/README.md: it
trusts the ticket delay over the order row, so nothing verified the value.

    python -m bonus.make_labels --benchmark reports/bonus_benchmark.json --out bonus/labels.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Written by hand from the design of each variant.
DEFECT_GROUP = {
    "handoff_drops_delay": "FC2",  # information lost between two steps
    "stale_policy": "FC1",  # the step ignored which policy is current
    "ignores_host_result": "FC3",  # the outcome was never checked
    "swarm": "FC3",  # ticket delay accepted without comparing it to the order row
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", default="reports/bonus_benchmark.json")
    ap.add_argument("--out", default="bonus/labels.json")
    args = ap.parse_args()
    trials = json.loads(Path(args.benchmark).read_text(encoding="utf-8"))["trials"]
    labels = {
        t["run_id"]: DEFECT_GROUP[t["shape"]]
        for t in trials
        if t.get("passed") is False and t["shape"] in DEFECT_GROUP
    }
    body = {
        "source": "group of the defect injected into each variant (hand-written mapping), not tagger output",
        "labels": labels,
    }
    Path(args.out).write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {len(labels)} labels to {args.out}")


if __name__ == "__main__":
    main()
