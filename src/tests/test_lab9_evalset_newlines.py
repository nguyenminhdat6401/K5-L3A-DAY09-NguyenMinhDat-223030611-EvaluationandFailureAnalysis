import hashlib
import json

import pytest

from lab9 import evalset

pytestmark = pytest.mark.student


def test_lab9_generated_evalset_uses_lf(tmp_path, monkeypatch):
    source = tmp_path / "claims.jsonl"
    source.write_text(json.dumps({
        "claim_id": "C-001", "matrix_id": "T01",
        "expected": {"refund_vnd": 35000},
    }) + "\n", encoding="utf-8")
    items = tmp_path / "out" / "items.jsonl"
    monkeypatch.setattr(evalset, "ITEMS", items)
    monkeypatch.setattr(evalset, "LABELS", items.parent / "labels.json")
    evalset.build(source)
    raw = items.read_bytes()
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
    assert evalset.sha12(items) == hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()[:12]
