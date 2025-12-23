"""Prompts for test case generation."""

DATASET_GENERATION_PROMPT = """You are an expert at creating eval datasets for AI agents.

Given a product description, generate a complete eval dataset with a name, description, and test cases.

Product Description:
{product_description}

Generate a JSON object with:
1. A short, kebab-case dataset name (e.g., "customer-support-bot", "doc-qa-agent")
2. A brief description of what the dataset tests
3. 5-10 diverse test cases covering different scenarios
4. EVERY case MUST include "expected_metadata" with "tool_calls" array

Output format:
```json
{{
  "name": "dataset-name",
  "description": "Brief description of what this dataset evaluates",
  "cases": [
    {{
      "name": "Single-turn example",
      "inputs": [
        {{"role": "user", "message": "User's request or question", "attachments": []}}
      ],
      "expected_outcome": "What the agent should do or respond with",
      "expected_metadata": {{
        "tool_calls": ["relevant_function_name"]
      }}
    }},
    {{
      "name": "Multi-turn conversation example",
      "inputs": [
        {{"role": "user", "message": "User's initial request", "attachments": []}},
        {{"role": "assistant", "message": "Agent's first response", "metadata": {{"tool_calls": ["search_docs"]}}}},
        {{"role": "user", "message": "User's follow-up question or clarification", "attachments": []}},
        {{"role": "assistant", "message": "Agent's second response"}},
        {{"role": "user", "message": "User's final input", "attachments": []}}
      ],
      "expected_outcome": "What the agent should do in its final response",
      "expected_metadata": {{
        "tool_calls": ["get_order_status"],
        "citations": [{{"file": "policy.pdf", "page": 5}}]
      }}
    }}
  ]
}}
```

## Guidelines

### Conversation Structure
- Include a mix of single-turn AND multi-turn conversations
- Multi-turn cases should have realistic back-and-forth dialogue
- The last message in inputs should always be from "user" (what the agent needs to respond to)
- Cover happy paths, edge cases, and error handling

### Writing Expected Outcomes

Expected outcomes describe what the USER should see in the response - the content, tone, and information provided. Do NOT mention internal implementation details like tool calls, function names, or API calls.

**Content focus** - Describe what information the response should contain:
- Good: "Should provide the refund amount ($49.99) and timeline (5-7 business days)"
- Bad: "Should call process_refund and return the amount" (mentions implementation)

**Behavioral focus** - Describe tone and approach:
- Good: "Should acknowledge the frustration empathetically and offer to help resolve the issue"
- Bad: "Should query the order database" (mentions implementation)

**Factual focus** - Include the ground truth:
- Good: "Should state that the return window is 30 days and requires original receipt"
- Bad: "Should look up the return policy" (mentions implementation)

**IMPORTANT:** Never mention tool calls, functions, or internal operations in expected_outcome. Those belong in expected_metadata only.

### Using Metadata

ALWAYS include `expected_metadata` for every case. This captures the INTERNAL actions the agent should take (separate from what the user sees).

**Tool calls** - What internal functions should the agent call?
- Include `"tool_calls": ["function_name"]` for each case
- Infer logical tool names: "check order" → `get_order_status`, "process refund" → `process_refund`
- Use snake_case for tool names

**Citations** - What sources should the agent reference internally?
- Include `"citations": [{{"file": "doc.pdf", "page": 5}}]` when the agent should cite documents

**Remember:**
- expected_outcome = what the user SEES (content, tone, facts)
- expected_metadata = what the agent DOES internally (tool calls, citations)

Only output the JSON object, no other text."""


def build_dataset_generation_prompt(product_description: str) -> str:
    """Build a prompt to generate a complete dataset from a product description.

    Args:
        product_description: Description of the product/agent to test

    Returns:
        Formatted prompt string
    """
    return DATASET_GENERATION_PROMPT.format(product_description=product_description)
