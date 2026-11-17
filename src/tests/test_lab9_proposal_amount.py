from types import SimpleNamespace

import pytest

from lab9.graders import ProposalAmountCorrect

pytestmark = pytest.mark.student


@pytest.mark.parametrize("proposal,expected,correct", [
    (35000, 35000, True),
    (0, 35000, False),
    (120000, 150000, False),
    (0, 0, True),
    (None, 35000, False),
    ("35000", 35000, False),
    (False, 0, False),
])
def test_lab9_full_proposal(proposal, expected, correct):
    ctx = SimpleNamespace(
        output={"result": {"proposal_amount": proposal}},
        expected_output={"proposal_amount": expected},
    )
    assert ProposalAmountCorrect().evaluate(ctx).value is correct
