"""Tag failed benchmark trials with a MAST failure category (bonus B2).

Reads a benchmark report and the trace file of every trial, and assigns each failed
trial to one of the three MAST groups using explicit rules on the trace events. It never
looks at the shape name, so the rules must work from evidence in the trace alone.

    python -m bonus.mast_tag --benchmark reports/bonus_benchmark.json \
        --labels bonus/labels.json --out reports/bonus_mast.json

Groups (MAST, NeurIPS 2025): FC1 system design, FC2 inter-agent misalignment,
FC3 task verification and termination.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

CATEGORIES = ("FC1", "FC2", "FC3", "unclassified")
NAMES = {
    "FC1": "system design issues",
    "FC2": "inter-agent misalignment",
    "FC3": "task verification and termination",
    "unclassified": "no rule matched",
}


def load_events(trace_path: str | Path) -> list[dict]:
    path = Path(trace_path)
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("events", [])


def _first(events: list[dict], kind: str) -> dict | None:
    return next((e["payload"] for e in events if e.get("kind") == kind), None)


def _tag(category: str, mode: str, reason: str) -> dict:
    return {"category": category, "mode": mode, "reason": reason}


def tag_trial(trial: dict, events: list[dict]) -> dict:
    """Return {category, mode, reason} for one failed trial. Rules run in this order."""
    if trial.get("status") == "error" or not events:
        return _tag("FC1", "disobey_task_specification", "no valid trace or the shape raised an error")

    # A model or ticket value replaced a structured value without being checked against it.
    override = _first(events, "model_override")
    if override is not None:
        return _tag(
            "FC3",
            "incorrect_verification",
            f"model_override {override} was accepted without comparing it to the order row",
        )

    # Facts handed to a later step disagree with what the order lookup returned.
    handoff, order = _first(events, "handoff"), _first(events, "order")
    if handoff and order and "delay_days" in (handoff.get("facts") or {}) and "delay_days" in order:
        if handoff["facts"]["delay_days"] != order["delay_days"]:
            return _tag(
                "FC2",
                "information_withholding",
                f"handoff facts delay_days={handoff['facts']['delay_days']} but order lookup "
                f"returned {order['delay_days']}",
            )

    # The quote used a policy that is not current.
    policy = _first(events, "policy_used")
    if policy and policy.get("non_current"):
        return _tag(
            "FC1", "disobey_task_specification", f"quote read non-current policies {policy['non_current']}"
        )

    # The host refused but the shape reported success.
    host = _first(events, "host")
    if host is not None and host.get("ok") is False and trial.get("status") == "resolved":
        return _tag(
            "FC3",
            "no_or_incomplete_verification",
            f"host refused ({host.get('reason')}) but the shape reported resolved",
        )

    return _tag("unclassified", "none", "no rule matched the trace")


def cohens_kappa(a: list[str], b: list[str]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum((ca[c] / n) * (cb[c] / n) for c in set(a) | set(b))
    return 1.0 if expected == 1.0 else (observed - expected) / (1.0 - expected)


def _tagged(trial: dict, trace_dir: str) -> bool:
    events = load_events(Path(trace_dir) / f"{trial['run_id']}.json")
    return tag_trial(trial, events)["category"] != "unclassified"


def run(benchmark: str, labels_path: str | None, trace_dir: str, clean_shapes: set[str]) -> dict:
    report = json.loads(Path(benchmark).read_text(encoding="utf-8"))
    tagged: list[dict] = []
    table: dict[str, Counter] = {}
    for trial in report["trials"]:
        if trial.get("passed") is not False:
            continue
        tag = tag_trial(trial, load_events(Path(trace_dir) / f"{trial['run_id']}.json"))
        tagged.append(
            {
                "run_id": trial["run_id"],
                "shape": trial["shape"],
                "claim_id": trial["claim_id"],
                "seed": trial["seed"],
                "benchmark_reason": trial["reason"],
                **tag,
            }
        )
        table.setdefault(trial["shape"], Counter())[tag["category"]] += 1

    # A passing trial of a shape without an injected defect must not be tagged (specificity).
    # A passing trial of a broken variant may still carry the defect signature: the defect
    # existed but did not change that claim's outcome. Those are reported as latent, not as errors.
    passing = [t for t in report["trials"] if t.get("passed") is True]
    clean = [t for t in passing if t["shape"] in clean_shapes]
    false_alarms = [t["run_id"] for t in clean if _tagged(t, trace_dir)]
    latent = Counter(t["shape"] for t in passing if t["shape"] not in clean_shapes and _tagged(t, trace_dir))

    out: dict = {
        "source": benchmark,
        "failed_trials": len(tagged),
        "by_shape_and_category": {s: dict(c) for s, c in sorted(table.items())},
        "clean_shapes": sorted(clean_shapes),
        "clean_passing_trials_checked": len(clean),
        "clean_passing_trials_wrongly_tagged": len(false_alarms),
        "passing_trials_with_latent_defect": dict(latent),
        "tags": tagged,
    }
    if labels_path:
        labels = json.loads(Path(labels_path).read_text(encoding="utf-8"))
        rows = [(t, labels["labels"][t["run_id"]]) for t in tagged if t["run_id"] in labels["labels"]]
        hand = [h for _, h in rows]
        auto = [t["category"] for t, _ in rows]
        out["agreement"] = {
            "label_source": labels.get("source"),
            "labeled_trials": len(rows),
            "accuracy": sum(x == y for x, y in zip(hand, auto)) / len(rows) if rows else None,
            "cohens_kappa": cohens_kappa(hand, auto),
            "disagreements": [t["run_id"] for t, h in rows if h != t["category"]],
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark", default="reports/bonus_benchmark.json")
    ap.add_argument("--labels", default="bonus/labels.json")
    ap.add_argument("--traces", default="traces")
    ap.add_argument("--out", default="reports/bonus_mast.json")
    ap.add_argument("--clean-shapes", default="workflow", help="shapes with no injected defect")
    args = ap.parse_args()
    result = run(
        args.benchmark,
        args.labels if Path(args.labels).is_file() else None,
        args.traces,
        set(args.clean_shapes.split(",")),
    )
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"failed trials: {result['failed_trials']}")
    for shape, cats in result["by_shape_and_category"].items():
        print(f"  {shape:22s} {cats}")
    print(
        f"clean passing trials wrongly tagged: {result['clean_passing_trials_wrongly_tagged']}"
        f"/{result['clean_passing_trials_checked']}; latent defects in passing trials: "
        f"{result['passing_trials_with_latent_defect']}"
    )
    if "agreement" in result:
        a = result["agreement"]
        print(f"agreement with labels: accuracy {a['accuracy']:.3f}, kappa {a['cohens_kappa']:.3f} on {a['labeled_trials']} trials")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
