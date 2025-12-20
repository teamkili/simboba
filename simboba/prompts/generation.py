"""Prompts for test case generation."""

DATASET_GENERATION_PROMPT = """You are an expert at creating eval datasets for AI agents.

Given a product description, generate a complete eval dataset with a name, description, and test cases.

Product Description:
{product_description}

Generate a JSON object with:
1. A short, kebab-case dataset name (e.g., "customer-support-bot", "doc-qa-agent")
2. A brief description of what the dataset tests
3. 5-10 diverse test cases covering different scenarios

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
      "expected_outcome": "What the agent should do or respond with"
    }},
    {{
      "name": "Multi-turn conversation example",
      "inputs": [
        {{"role": "user", "message": "User's initial request", "attachments": []}},
        {{"role": "assistant", "message": "Agent's first response"}},
        {{"role": "user", "message": "User's follow-up question or clarification", "attachments": []}},
        {{"role": "assistant", "message": "Agent's second response"}},
        {{"role": "user", "message": "User's final input", "attachments": []}}
      ],
      "expected_outcome": "What the agent should do in its final response"
    }}
  ]
}}
```

Guidelines:
- Create diverse scenarios covering happy paths, edge cases, and error handling
- IMPORTANT: Include a mix of single-turn AND multi-turn conversations
- Multi-turn cases should have realistic back-and-forth dialogue
- The last message in inputs should always be from "user" (what the agent needs to respond to)
- Expected outcomes should be specific and testable
- Test different capabilities the agent should have

Only output the JSON object, no other text."""


GENERATION_PROMPT = """You are an expert at creating realistic test cases for AI agent evaluations.

Given a description of an agent/app, generate {num_cases} diverse test conversations with expected outcomes.

Agent/App Description:
{agent_description}

Complexity level: {complexity}

For each test case, generate:
1. A realistic conversation (array of messages between user and assistant)
2. An expected outcome description (what the agent should do/achieve)

Output your response as a JSON array with this exact format:
```json
[
  {{
    "name": "Brief descriptive name for this test case",
    "inputs": [
      {{"role": "user", "message": "User's first message", "attachments": []}},
      {{"role": "assistant", "message": "Assistant's response", "attachments": []}},
      {{"role": "user", "message": "User's follow-up", "attachments": []}}
    ],
    "expected_outcome": "Clear description of what the agent should do. Include multiple criteria separated by periods if needed."
  }}
]
```

Guidelines:
- Create diverse scenarios that test different aspects of the agent
- Include edge cases and challenging situations
- Make conversations realistic and natural
- Expected outcomes should be specific and testable
- For "simple" complexity: straightforward single-turn or short exchanges
- For "complex" complexity: multi-turn conversations with nuance
- For "mixed" complexity: variety of both

Generate exactly {num_cases} test cases. Only output the JSON array, no other text."""


GENERATION_PROMPT_WITH_FILES = """You are an expert at creating realistic test cases for AI agent evaluations.

Given a description of an agent/app and reference documents, generate {num_cases} diverse test conversations with expected outcomes based on the actual document content.

Agent/App Description:
{agent_description}

Complexity level: {complexity}

Reference Documents:
{file_contents}

For each test case, generate:
1. A realistic conversation where a user asks about content from the documents
2. An expected outcome description (what the agent should do/achieve)
3. A source reference pointing to where in the document the answer can be found

Output your response as a JSON array with this exact format:
```json
[
  {{
    "name": "Brief descriptive name for this test case",
    "inputs": [
      {{"role": "user", "message": "User's question about the document", "attachments": [{{"file": "filename.pdf"}}]}}
    ],
    "expected_outcome": "Clear description of what the agent should answer based on the document.",
    "expected_source": {{
      "file": "filename.pdf",
      "page": 1,
      "excerpt": "Relevant quote from the document (optional but helpful)"
    }}
  }}
]
```

Guidelines:
- Create questions that test understanding of the actual document content
- Include a mix of straightforward lookups and questions requiring synthesis
- Expected outcomes should be verifiable against the document
- Always include expected_source with the correct file and page number
- The excerpt field is optional but helps with quick verification
- For "simple" complexity: direct questions with answers on a single page
- For "complex" complexity: questions requiring information from multiple pages
- For "mixed" complexity: variety of both

Generate exactly {num_cases} test cases. Only output the JSON array, no other text."""


def build_dataset_generation_prompt(product_description: str) -> str:
    """Build a prompt to generate a complete dataset from a product description.

    Args:
        product_description: Description of the product/agent to test

    Returns:
        Formatted prompt string
    """
    return DATASET_GENERATION_PROMPT.format(product_description=product_description)


def build_generation_prompt(agent_description: str, num_cases: int, complexity: str) -> str:
    """Build a generation prompt for creating test cases.

    Args:
        agent_description: Description of the agent being tested
        num_cases: Number of test cases to generate
        complexity: Complexity level (simple, complex, mixed)

    Returns:
        Formatted prompt string
    """
    return GENERATION_PROMPT.format(
        num_cases=num_cases,
        agent_description=agent_description,
        complexity=complexity,
    )


def build_generation_prompt_with_files(
    agent_description: str,
    num_cases: int,
    complexity: str,
    file_contents: str
) -> str:
    """Build a generation prompt that includes file contents.

    Args:
        agent_description: Description of the agent being tested
        num_cases: Number of test cases to generate
        complexity: Complexity level (simple, complex, mixed)
        file_contents: Formatted file contents to include

    Returns:
        Formatted prompt string
    """
    return GENERATION_PROMPT_WITH_FILES.format(
        num_cases=num_cases,
        agent_description=agent_description,
        complexity=complexity,
        file_contents=file_contents,
    )
