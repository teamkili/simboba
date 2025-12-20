"""Tests for LLM integration with LiteLLM.

Run with: pytest tests/test_llm.py -v
"""

from simboba.database import init_db, get_session_factory
from simboba.models import Settings
from simboba.utils.models import LLMClient


def test_llm_connection():
    """Test that LLM API calls work with the configured model."""
    init_db()
    Session = get_session_factory()
    db = Session()

    try:
        model = Settings.get(db, "model") or LLMClient.DEFAULT_MODEL
    finally:
        db.close()

    print(f"\nTesting model: {model}")

    client = LLMClient(model=model)
    response = client.generate("Reply with exactly one word: hello")

    assert response is not None
    assert len(response.strip()) > 0
    print(f"Response: {response.strip()}")
