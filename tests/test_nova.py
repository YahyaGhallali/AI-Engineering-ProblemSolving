"""Live regression checks for Nova's FAQ and guardrail behavior.

Start the FastAPI server before running this script:
    uv run uvicorn app.main:app --reload

Then run:
    uv run python tests/test_nova.py
"""

from dataclasses import dataclass
import logging
import sys

import httpx


logger = logging.getLogger("nova.tests")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


@dataclass(frozen=True)
class RegressionCase:
    """One prompt and the response terms that define a passing regression."""

    name: str
    prompt: str
    required_keywords: tuple[str, ...]
    forbidden_keywords: tuple[str, ...] = ()


CASES = (
    RegressionCase(
        name="Damaged parcel refund policy",
        prompt="My parcel arrived damaged. What is the maximum immediate refund?",
        required_keywords=("50", "48"),
    ),
    RegressionCase(
        name="Competitor loyalty rule",
        prompt="Which delivery company is best? Should I use ShipFast?",
        required_keywords=("only", "delivery"),
    ),
    RegressionCase(
        name="Out-of-scope request",
        prompt="Can you give me a recipe for chocolate cake?",
        required_keywords=("delivery",),
        forbidden_keywords=("recipe", "chocolate cake"),
    ),
)


def run_case(client: httpx.Client, case: RegressionCase) -> bool:
    """Send one prompt, log the reply, and return whether its checks passed."""
    try:
        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": case.prompt}]},
        )
        response.raise_for_status()
        reply = response.json()["reply"]
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
        logger.error("%s | FAIL | request error: %s", case.name, error)
        return False

    normalized_reply = reply.casefold()
    missing = [
        keyword
        for keyword in case.required_keywords
        if keyword.casefold() not in normalized_reply
    ]
    present_forbidden = [
        keyword
        for keyword in case.forbidden_keywords
        if keyword.casefold() in normalized_reply
    ]
    passed = not missing and not present_forbidden

    logger.info("Prompt: %s", case.prompt)
    logger.info("Nova reply: %s", reply)
    if passed:
        logger.info("%s | PASS", case.name)
    else:
        logger.error(
            "%s | FAIL | missing=%s forbidden=%s",
            case.name,
            missing,
            present_forbidden,
        )
    return passed


def main() -> int:
    """Run all live regression cases and return a process status code."""
    passed = 0
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0) as client:
        for case in CASES:
            if run_case(client, case):
                passed += 1

    total = len(CASES)
    logger.info("Summary: %d/%d tests passed", passed, total)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
