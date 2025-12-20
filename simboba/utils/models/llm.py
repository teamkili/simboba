"""LLM client using LiteLLM for multi-provider support."""

import json
from typing import Optional

import litellm


class LLMClient:
    """Wrapper for LLM calls using LiteLLM.

    Supports any model that LiteLLM supports:
    - OpenAI: gpt-4, gpt-4o, gpt-4o-mini, gpt-3.5-turbo
    - Anthropic: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-sonnet-4-20250514
    - Google: gemini/gemini-pro
    - Local: ollama/llama2, ollama/mistral
    - And many more: https://docs.litellm.ai/docs/providers

    API keys are read from environment variables automatically:
    - OPENAI_API_KEY for OpenAI models
    - ANTHROPIC_API_KEY for Anthropic models
    - etc.
    """

    DEFAULT_MODEL = "gemini/gemini-3-flash-preview"

    def __init__(self, model: Optional[str] = None):
        """Initialize the LLM client.

        Args:
            model: Model identifier (e.g., "gpt-4", "claude-sonnet-4-20250514")
                   Defaults to DEFAULT_MODEL if not specified.
        """
        self.model = model or self.DEFAULT_MODEL

    def generate(self, prompt: str, max_tokens: int = 4096) -> str:
        """Generate a response from the model.

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            The model's response text
        """
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def generate_json(self, prompt: str, max_tokens: int = 4096) -> dict:
        """Generate a JSON response from the model.

        Args:
            prompt: The prompt to send (should request JSON output)
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response

        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        response = self.generate(prompt, max_tokens)
        return self.parse_json_response(response)

    @staticmethod
    def parse_json_response(response: str) -> dict:
        """Parse a JSON response, handling markdown code blocks.

        Args:
            response: Raw response text

        Returns:
            Parsed JSON object
        """
        text = response.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)
