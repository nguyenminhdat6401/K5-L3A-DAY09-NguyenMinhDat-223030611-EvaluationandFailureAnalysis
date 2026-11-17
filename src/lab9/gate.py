"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    import math
    from collections import Counter
    from lab9.graders import GRADERS
    from lab9.eval import aggregate

    problems = []

    def finite(value):
        return isinstance(value, (int, float)) and math.isfinite(value)

    def inspect(report, name):
        rows = report.get("rows")
        manifest = report.get("manifest", {})
        metrics = report.get("metrics", {})
        if not isinstance(rows, list) or not isinstance(metrics, dict):
            problems.append(f"{name}: malformed rows or metrics")
            return None
        if report.get("evaluator_failures"):
            problems.append(f"{name}: evaluator_failures")
        seeds = manifest.get("seeds", [])
        items = manifest.get("items")
        if (not isinstance(seeds, list) or not seeds
                or any(type(seed) is not int for seed in seeds)
                or len(set(seeds)) != len(seeds)):
            problems.append(f"{name}: invalid manifest seeds")
            return None
        if type(items) is not int or items < 1:
            problems.append(f"{name}: invalid item count")
            return None
        if len(rows) != items * len(seeds):
            problems.append(f"{name}: row count differs from items x seeds")
        keys, tags = [], {}
        graded = [m["id"] for m in spec.get("metrics", []) if m["id"] in GRADERS]
        invalid_rows = False
        for row in rows:
            if not isinstance(row, dict):
                problems.append(f"{name}: malformed row")
                invalid_rows = True
                continue
            item, seed = row.get("item_id"), row.get("seed")
            if not isinstance(item, str) or not item or type(seed) is not int:
                problems.append(f"{name}: invalid item/seed")
                invalid_rows = True
                continue
            keys.append((item, seed))
            if seed not in seeds:
                problems.append(f"{name}: row seed outside manifest")
            slices = row.get("slices", [])
            if (not isinstance(slices, list)
                    or any(not isinstance(tag, str) for tag in slices)
                    or len(slices) != len(set(slices))):
                problems.append(f"{name}: invalid slice tags")
                invalid_rows = True
            else:
                normalized = frozenset(slices)
                if item in tags and tags[item] != normalized:
                    problems.append(f"{name}: inconsistent slice tags across seeds")
                tags[item] = normalized
            for metric in graded:
                value = row.get(metric)
                if not finite(value) or value not in (0, 1):
                    problems.append(f"{name}: missing/invalid row metric {metric}")
                    invalid_rows = True
            if "cost" in row and (not finite(row["cost"]) or row["cost"] < 0):
                problems.append(f"{name}: invalid row cost")
                invalid_rows = True
        counts = Counter(keys)
        if any(count != 1 for count in counts.values()):
            problems.append(f"{name}: duplicate item/seed rows")
        item_ids = {item for item, _ in keys}
        if len(item_ids) != items:
            problems.append(f"{name}: item count differs from manifest")
        expected = {(item, seed) for item in item_ids for seed in seeds}
        if set(keys) != expected:
            problems.append(f"{name}: incomplete item/seed grid")
        for metric in spec.get("metrics", []):
            mid = metric["id"]
            if mid not in metrics or not finite(metrics[mid]):
                problems.append(f"{name}: missing/nonfinite summary metric {mid}")
        for mid, value in metrics.items():
            if not finite(value):
                problems.append(f"{name}: nonfinite summary metric {mid}")
        # Independently recompute supplied summaries from rows when available.
        if not invalid_rows and all("cost" in row for row in rows):
            calculated = aggregate(rows, graded, k_values=spec.get("pass_k", []))
            for mid, value in metrics.items():
                if mid in calculated and finite(value) and finite(calculated[mid]):
                    if not math.isclose(value, calculated[mid], abs_tol=0.000051, rel_tol=1e-9):
                        problems.append(f"{name}: summary disagrees with rows: {mid}")
        return set(keys), tags, set(seeds)

    current = inspect(pr, "PR")
    reference = inspect(base, "baseline")
    if current is not None and reference is not None:
        if current[0] != reference[0] or current[2] != reference[2]:
            problems.append("PR item/seed grid differs from baseline")
        if current[1] != reference[1]:
            problems.append("PR slice tags differ from baseline")
        if "seeds" in spec and current[2] != set(spec["seeds"]):
            problems.append("report seeds differ from metric spec")

    def ratchet_entries(old_entries, new_entries, key, label):
        old = {key(entry): entry for entry in old_entries}
        new = {key(entry): entry for entry in new_entries}
        if len(new) != len(new_entries):
            problems.append(f"ratchet: duplicate {label}")
        for identifier, previous in old.items():
            if identifier not in new:
                problems.append(f"ratchet: removed {label} {identifier}")
                continue
            updated = new[identifier]
            if previous.get("blocking") and not updated.get("blocking"):
                problems.append(f"ratchet: disabled blocking {label} {identifier}")
            before = previous.get("threshold", {}) if label == "metric" else previous
            after = updated.get("threshold", {}) if label == "metric" else updated
            for threshold in ("min", "max", "max_increase"):
                if threshold in before:
                    value = after.get(threshold)
                    if (not finite(value)
                            or (threshold == "min" and value < before[threshold])
                            or (threshold != "min" and value > before[threshold])):
                        problems.append(f"ratchet: loosened {label} {identifier}/{threshold}")
            if before.get("no_significant_drop") and not after.get("no_significant_drop"):
                problems.append(f"ratchet: removed no_significant_drop {label} {identifier}")
            if label == "metric":
                for field in ("kind", "grader", "level"):
                    if field in previous and updated.get(field) != previous[field]:
                        problems.append(f"ratchet: changed {field} for {identifier}")

    if base_spec is not None and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        ratchet_entries(base_spec.get("metrics", []), spec.get("metrics", []),
                        lambda entry: entry["id"], "metric")
        ratchet_entries(base_spec.get("slices", []), spec.get("slices", []),
                        lambda entry: (entry["name"], entry["metric"]), "slice")
    return list(dict.fromkeys(problems))


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    import math

    blocked, lines = [], []
    bootstrap = spec.get("bootstrap", {})
    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        identifier = f"slice:{name}/{metric}"
        current = per_item(pr, metric, slice_name=name)
        reference = per_item(base, metric, slice_name=name)
        problems = []
        note = ""
        value = None

        if not current or not reference:
            problems.append("empty_slice")
        elif set(current) != set(reference):
            problems.append("slice_item_mismatch")
        elif not all(math.isfinite(v) for v in [*current.values(), *reference.values()]):
            problems.append("nonfinite_slice_value")
        else:
            keys = sorted(current)
            value = sum(current.values()) / len(current)
            if "min" in rule and value < rule["min"]:
                problems.append("below_floor")
            if rule.get("no_significant_drop"):
                if len(keys) < 2 and any(current[k] != reference[k] for k in keys):
                    problems.append("insufficient_paired_items")
                else:
                    delta, low, high = stats.paired_bootstrap(
                        [current[k] for k in keys],
                        [reference[k] for k in keys],
                        n_resamples=bootstrap.get("n_resamples", 1000),
                        rng=bootstrap.get("rng", 2027),
                        confidence=bootstrap.get("confidence", 0.95),
                    )
                    note = f"delta={delta:+.3f} CI [{low:+.3f}, {high:+.3f}]"
                    if high < 0:
                        problems.append("significant_drop")

        if problems and rule.get("blocking"):
            blocked.append(identifier)
        verdict = "BLOCK" if problems and rule.get("blocking") else "warn" if problems else "ok"
        lines.append(f"  {identifier} value={value} {note} {verdict} {';'.join(problems)}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
