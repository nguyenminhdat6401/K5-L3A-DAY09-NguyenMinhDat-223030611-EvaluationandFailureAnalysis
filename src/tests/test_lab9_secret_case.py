from types import SimpleNamespace

import pytest

from lab8.shapes import SHAPES
from lab9.graders import SecretLeak
from lab9.trace_case import investigate
from lab9.variant_agent import make_shape


pytestmark = pytest.mark.student


@pytest.mark.parametrize("leaky", [False, True])
def test_lab9_secret_trace_c001(leaky):
    name = "audit_secret_leaky" if leaky else "audit_secret_clean"
    bugs = {"no_override"}
    if leaky:
        bugs.add("leaky_trace")

    # Register an isolated test variant; leave supplied variants unchanged.
    previous = SHAPES.get(name)
    SHAPES[name] = make_shape(name, bugs)

    try:
        case = investigate(name, "C-001", 11)
        ctx = SimpleNamespace(
            output=case["trial"],
            expected_output=case["label"],
        )

        detected = SecretLeak().evaluate(ctx).value
        assert detected is leaky

        if leaky:
            positions = [
                index
                for index, event in enumerate(
                    case["trial"]["events"], start=1
                )
                if event.get("kind") == "debug_claim_row"
            ]
            assert positions
            # Print only event positions, never payload or secret.
            print(
                f"FM-01: {name} C-001@11; "
                f"debug_claim_row steps={positions}; detected=True"
            )
        else:
            print(f"FM-01: {name} C-001@11; detected=False")
    finally:
        if previous is None:
            SHAPES.pop(name, None)
        else:
            SHAPES[name] = previous