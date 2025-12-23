"""Prompts for LLM-based evaluation judging."""

import json

JUDGE_PROMPT = """You are an expert evaluator judging whether an AI agent's output meets the expected outcome.

## Conversation Context
{conversation}

## Expected Outcome
{expected_outcome}
{expected_metadata_section}
## Actual Output
{actual_output}
{actual_metadata_section}
## Your Task
Evaluate whether the actual output satisfies the expected outcome. Consider:
1. Does the output achieve what was expected?
2. Are all the criteria in the expected outcome met?
3. Is the behavior appropriate given the conversation context?
4. If expected metadata is provided, does the actual metadata match? (e.g., correct tool calls, citations)

Respond with a JSON object in this exact format:
```json
{{
  "passed": true or false,
  "reasoning": "Your detailed explanation of why this passed or failed"
}}
```

Be strict but fair. Minor differences in wording are acceptable if the intent is met.
Only output the JSON object, nothing else."""


def format_conversation(inputs: list) -> str:
    """Format conversation inputs for the judge prompt.

    Args:
        inputs: List of message dicts with 'role', 'message', and optional 'metadata' keys

    Returns:
        Formatted conversation string
    """
    lines = []
    for msg in inputs:
        role = msg.get("role", "unknown").upper()
        message = msg.get("message", "")
        lines.append(f"{role}: {message}")
        # Include metadata if present
        metadata = msg.get("metadata")
        if metadata:
            lines.append(f"  [metadata: {json.dumps(metadata)}]")
    return "\n".join(lines)


def build_judge_prompt(
    inputs: list,
    expected_outcome: str,
    actual_output: str,
    expected_metadata: dict = None,
    actual_metadata: dict = None,
) -> str:
    """Build a judge prompt for evaluating an output.

    Args:
        inputs: Conversation inputs
        expected_outcome: What the agent should have done
        actual_output: What the agent actually produced
        expected_metadata: Expected metadata (citations, tool_calls, etc.)
        actual_metadata: Actual metadata from the agent response

    Returns:
        Formatted prompt string
    """
    conversation = format_conversation(inputs)

    # Format metadata sections
    expected_metadata_section = ""
    if expected_metadata:
        expected_metadata_section = f"\n## Expected Metadata\n```json\n{json.dumps(expected_metadata, indent=2)}\n```\n"

    actual_metadata_section = ""
    if actual_metadata:
        actual_metadata_section = f"\n## Actual Metadata\n```json\n{json.dumps(actual_metadata, indent=2)}\n```\n"

    return JUDGE_PROMPT.format(
        conversation=conversation,
        expected_outcome=expected_outcome,
        expected_metadata_section=expected_metadata_section,
        actual_output=actual_output,
        actual_metadata_section=actual_metadata_section,
    )
