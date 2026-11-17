import pytest

from lab9.trace_case import investigate


@pytest.mark.student
@pytest.mark.parametrize(
    "shape, expected_pass, expected_refund",
    [
        ("fixed", True, 0),
        ("seeded_regression", False, 20000),
    ],
)
def test_lab9_ticket_trust_c002(shape, expected_pass, expected_refund):
    case = investigate(shape, "C-002", 11)
    trial = case["trial"]
    label = case["label"]

    # Đáp án đúng của claim không thay đổi theo variant.
    assert label["status"] == "denied"
    assert label["refund_vnd"] == 0

    # Kiểm tra effect thực tế, không chỉ đọc câu trả lời.
    assert trial["snapshot"]["refund_vnd"] == expected_refund
    assert trial["lab8_pass"] is expected_pass

    if expected_pass:
        assert trial["snapshot"]["refund_count"] == 0
        assert trial["result"]["status"] == "denied"
    else:
        assert trial["snapshot"]["refund_count"] == 1
        assert trial["result"]["status"] == "resolved"
        assert trial["snapshot"]["refund_vnd"] != label["refund_vnd"]