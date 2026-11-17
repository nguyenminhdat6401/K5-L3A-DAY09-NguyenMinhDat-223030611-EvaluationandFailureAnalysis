from types import SimpleNamespace

import pytest

from lab9.graders import ReplyAmountCorrect


pytestmark = pytest.mark.student


@pytest.mark.parametrize(
    "text,amount,status,expected",
    [
        ("Dạ, đã hoàn 120.000đ.", 120000, "resolved", True),
        ("Dạ, đã hoàn 120.000đ.", 90000, "resolved", False),
        ("Đã hoàn phí 35,000 VND.", 35000, "resolved", True),
        ("Đơn chưa đủ điều kiện hoàn.", 0, "denied", True),
        ("Đã hoàn 35.000đ.", 0, "resolved", False),
        ("Đã xử lý xong.", 35000, "resolved", False),
    ],
)
def test_lab9_reply_amount(text, amount, status, expected):
    ctx = SimpleNamespace(
        output={
            "events": [{"kind": "reply", "payload": {"text": text}}],
            "snapshot": {"refund_vnd": amount},
            "result": {"status": status},
        }
    )
    assert ReplyAmountCorrect().evaluate(ctx).value is expected


def test_lab9_no_reply_is_explicitly_not_applicable():
    ctx = SimpleNamespace(
        output={
            "events": [],
            "snapshot": {"refund_vnd": 0},
            "result": {"status": "denied"},
        }
    )
    result = ReplyAmountCorrect().evaluate(ctx)
    assert result.value is True
    assert result.reason == "not_applicable_no_reply_event"

@pytest.mark.parametrize("payload", [{}, {"text": None}, {"text": ""}, {"text": "   "}])
def test_lab9_malformed_reply_fails(payload):
    ctx = SimpleNamespace(output={
        "events": [{"kind": "reply", "payload": payload}],
        "snapshot": {"refund_vnd": 0},
        "result": {"status": "denied"},
    })
    assert ReplyAmountCorrect().evaluate(ctx).value is False
