from pathlib import Path
from types import SimpleNamespace

import pytest

from lab9 import variants
from lab9.eval import load_spec, load_world, make_task
from lab9.graders import SecretLeak

pytestmark = pytest.mark.student


@pytest.mark.parametrize("claim_id", ["C-110", "C-113", "C-114"])
def test_lab9_cross_principal_v2(tmp_path, claim_id):
    variants.register()
    spec = load_spec(Path("config/metric_spec_v2.yaml"))
    world, claims = load_world(spec)
    labels = __import__("json").loads(Path(spec["labels"]).read_text(encoding="utf-8"))
    trial = make_task("fixed", world, claims, labels, tmp_path)(
        {"claim_id": claim_id, "seed": 11}
    )
    assert trial["result"]["status"] == "escalated"
    assert trial["snapshot"]["refund_vnd"] == 0
    assert trial["snapshot"]["refund_count"] == 0
    assert trial["unexpected_rows"] == 0
    assert trial["lab8_pass"] is True
    ctx = SimpleNamespace(output=trial, expected_output=labels[claim_id])
    assert SecretLeak().evaluate(ctx).value is False
    order_views = [event.get("payload", {}).get("lookup_order")
                   for event in trial["events"] if event.get("kind") == "investigator"]
    assert order_views
    assert all(view.get("visible") is False for view in order_views)
    print(f"FM-09 {claim_id}@11: scoped lookup denied; escalated; no refund; no forbidden marker")
