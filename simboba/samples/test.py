"""
Eval: Test your agent against a dataset.

USAGE:
    boba run          # Run evals
    boba serve        # View results in UI
"""

from simboba import Boba, MessageInput
from setup import get_context, cleanup


boba = Boba()


# =============================================================================
# DATASET TO TEST - Change this to your dataset name
# =============================================================================
DATASET = "my-dataset"  # Change this!


# =============================================================================
# AGENT FUNCTION
# =============================================================================

def agent(inputs: list[MessageInput]) -> str:
    """
    Call your agent with the conversation inputs and return its response.

    Args:
        inputs: Full conversation history as list[MessageInput].
                Each MessageInput has: role, message, attachments (optional), metadata (optional)

    Replace this with your actual agent call.
    """
    ctx = get_context()

    # Get the last user message (most common use case)
    last_message = inputs[-1].message if inputs else ""

    # -------------------------------------------------------------------------
    # OPTION 1: HTTP API
    # -------------------------------------------------------------------------
    # import requests
    # response = requests.post(
    #     "http://localhost:8000/api/chat",
    #     headers={"Authorization": f"Bearer {ctx['api_token']}"},
    #     json={"user_id": ctx["user_id"], "message": last_message},
    # )
    # response.raise_for_status()
    # return response.json()["response"]

    # -------------------------------------------------------------------------
    # OPTION 2: Direct Python call (with full history)
    # -------------------------------------------------------------------------
    # from myapp.agent import run
    # return run(user_id=ctx["user_id"], messages=inputs)

    # -------------------------------------------------------------------------
    # PLACEHOLDER - Replace with your agent call
    # -------------------------------------------------------------------------
    raise NotImplementedError(
        "Connect your agent here. Update the agent() function above."
    )


# =============================================================================
# RUN EVALS
# =============================================================================

if __name__ == "__main__":
    try:
        print(f"Running evals against dataset: {DATASET}")
        print("")

        result = boba.run(agent, dataset=DATASET)

        print("")
        print("=" * 50)
        print(f"Score: {result['score']:.1f}%")
        print(f"Passed: {result['passed']}/{result['total']}")
        if result['regressions']:
            print(f"Regressions: {len(result['regressions'])}")
        if result['fixes']:
            print(f"Fixes: {len(result['fixes'])}")
        print("=" * 50)
        print("")
        print("Run 'boba serve' to view detailed results.")

    finally:
        cleanup()
