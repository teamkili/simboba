"""Prompts for LLM-based evaluation judging."""

JUDGE_PROMPT = """You are an expert evaluator judging whether an AI agent's output meets the expected outcome.

## Conversation Context
{conversation}

## Expected Outcome
{expected_outcome}

## Actual Output
{actual_output}

## Your Task
Evaluate whether the actual output satisfies the expected outcome. Consider:
1. Does the output achieve what was expected?
2. Are all the criteria in the expected outcome met?
3. Is the behavior appropriate given the conversation context?

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
        inputs: List of message dicts with 'role' and 'message' keys

    Returns:
        Formatted conversation string
    """
    lines = []
    for msg in inputs:
        role = msg.get("role", "unknown").upper()
        message = msg.get("message", "")
        lines.append(f"{role}: {message}")
    return "\n".join(lines)


def build_judge_prompt(inputs: list, expected_outcome: str, actual_output: str) -> str:
    """Build a judge prompt for evaluating an output.

    Args:
        inputs: Conversation inputs
        expected_outcome: What the agent should have done
        actual_output: What the agent actually produced

    Returns:
        Formatted prompt string
    """
    conversation = format_conversation(inputs)
    return JUDGE_PROMPT.format(
        conversation=conversation,
        expected_outcome=expected_outcome,
        actual_output=actual_output,
    )
