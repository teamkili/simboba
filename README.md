# simboba

[![PyPI](https://img.shields.io/pypi/v/simboba)](https://pypi.org/project/simboba/)

```
     ( )
   .-~~~-.
  /       \
  |  ===  |
  | ::::: |
  |_:::::_|
    '---'
```

Lightweight tool to manage datasets and evals for your AI product. Supports LLM as a judge, tool calling and multi-turn conversations. Run evals as Python scripts, track results as git-friendly JSON files, view in a web UI. Designed for 1-click setup with your favourite AI coding tool.

## Installation

```bash
pip install simboba
```

## Quickstart

**1. Dataset** — Create `boba-evals/datasets/my-first-eval.json`:

```json
{
  "name": "my-first-eval",
  "cases": [
    {
      "name": "Basic greeting",
      "inputs": [{"role": "user", "message": "Hello"}],
      "expected_outcome": "Friendly greeting response"
    }
  ]
}
```

**2. Eval script** — Create `boba-evals/test.py`:

```python
from simboba import Boba, MessageInput

boba = Boba()

def agent(inputs: list[MessageInput]) -> str:
    # inputs is the full conversation history
    # For simple cases: message = inputs[-1].message
    return "Hi there! How can I help?"

if __name__ == "__main__":
    result = boba.run(agent, dataset="my-first-eval")
    print(f"{result['passed']}/{result['total']} passed")
```

**3. Run**:

```bash
ANTHROPIC_API_KEY=sk-ant-... boba run
```

**4. Output**:

```
  + Basic greeting
Results: 1/1 passed (100.0%)
```

That's it! Run `boba serve` to view results in the web UI.

---

## Quick Reference

```bash
boba init          # Create boba-evals/ folder with templates
boba magic         # Prompt for your AI tool to set up and run your first eval
boba run           # Run your evals (handles Docker automatically)
boba baseline      # Save run as baseline for regression detection
boba serve         # View results at http://localhost:8787
```

## Commands

| Command                       | Description                                                        |
| ----------------------------- | ------------------------------------------------------------------ |
| `boba init`                   | Create `boba-evals/` folder with starter templates                 |
| `boba magic`                  | Print detailed prompt for AI coding assistant                      |
| `boba run [script]`           | Run eval script (default: `test.py`). Handles Docker automatically |
| `boba baseline`               | Save a run as baseline for regression detection                    |
| `boba serve`                  | Start web UI to view results                                       |
| `boba datasets`               | List all datasets                                                  |
| `boba generate "description"` | Generate a dataset from a description                              |
| `boba reset`                  | Clear run history (keeps datasets and baselines)                   |

## Instructions for AI coding assistants

If you are helping a user set up Boba, plese use the following instructions to guide you:

1. Boba helps users set up and run their first set of evals within a few minutes.
2. Start by creating a dataset. Before creating this dataset, it is vital that you understand the user's product and what it does. If they have multiple flows in the product, we suggest asking the user to pick one of the flow and creating a dataset for this. When creating a dataset, look at schemas.py to understand the structure that you need to follow. You can also look at prompts/generation.py for an example of how to create a dataset. You can creating a dataset by giving a user a high quality prompt that they can run with boba generate. Alternatively, you can create the dataset yourself. Pay close attention to what you need in the expected output and expected metadata fields.
3. Once you create a dataset, you can run evals as simple python scripts. Before doing so, please write a setup.py file for fixtures. To do this, please study the user's app and set up everything required to run the eval. This is usually some combination of: creating or using a user, using a project or team and any other set up before you can call the functions you want to evaluate. This setup.py file will be used before all tests.
4. After you write setup.py, if the user is just getting started, write a simple eval script that allows them to evaluate some part of their app. Keep this small and concise so that the user understands how things work, and can expand from there.
5. Once you run the first eval, you can help the user by extending evals to cover more logic in their product and help them create baselines.

## How It Works

The CLI and Python API work together:

```
boba run test.py  →  executes your script  →  which calls boba.eval() or boba.run()
```

- **CLI** (`boba run`): Handles Docker detection, environment setup, script execution
- **Python API** (`Boba` class): Runs evaluations, stores results, compares to baselines

## Writing Evals

Evals are Python scripts. Edit `boba-evals/test.py`:

```python
from simboba import Boba, AgentResponse
from setup import get_context, cleanup

boba = Boba()

def agent(inputs: list[MessageInput]) -> str:
    """Call your agent with conversation history and return its response."""
    ctx = get_context()
    # inputs contains the full conversation history
    # Each input has: role, message, attachments (optional), metadata (optional)
    last_message = inputs[-1].message if inputs else ""
    response = requests.post(
        "http://localhost:8000/api/chat",
        json={"user_id": ctx["user_id"], "message": last_message},
    )
    return response.json()["response"]

if __name__ == "__main__":
    try:
        # Option 1: Single eval
        boba.eval(
            input="Hello",
            output="Hi there!",  # Call your agent directly for single evals
            expected="Should greet the user",
        )

        # Option 2: Run against a dataset
        # boba.run(agent, dataset="my-dataset")

        print("Done! Run 'boba serve' to view results.")
    finally:
        cleanup()
```

### Agent Input and Return Types

Your agent function receives the full conversation history and can return:

- **`str`** - Simple text response
- **`AgentResponse`** - Response with metadata (citations, tool_calls, etc.)

```python
from simboba import AgentResponse, MessageInput

# Simple agent - returns string
def simple_agent(inputs: list[MessageInput]) -> str:
    # Get the last message for simple use cases
    message = inputs[-1].message if inputs else ""
    return "Hello!"

# Agent with metadata - returns AgentResponse
def rag_agent(inputs: list[MessageInput]) -> AgentResponse:
    # Use full conversation history for context
    message = inputs[-1].message if inputs else ""
    docs = search_documents(message)
    response = generate_response(message, docs)
    return AgentResponse(
        output=response,
        metadata={
            "citations": [{"file": d.name, "page": d.page} for d in docs],
            "tool_calls": ["search_documents"],
        }
    )
```

## Metadata Checking

Metadata (citations, tool_calls, etc.) is always passed to the LLM judge when provided. For strict deterministic checks, add a `metadata_checker` function.

### With boba.eval()

```python
# Mode 1: No metadata - LLM judges output only
boba.eval(input="Hello", output="Hi!", expected="Should greet")

# Mode 2: LLM evaluates output + metadata together
boba.eval(
    input="What's my order status?",
    output="Your order #123 is shipped.",
    expected="Should look up order status",
    expected_metadata={"tool_calls": ["get_orders"]},
    actual_metadata={"tool_calls": ["get_orders"]},
)

# Mode 3: LLM evaluates + deterministic check (both must pass)
def check_tool_calls(expected, actual):
    if not expected or not actual:
        return True
    return set(expected.get("tool_calls", [])) == set(actual.get("tool_calls", []))

boba.eval(
    input="What's my order status?",
    output="Your order #123 is shipped.",
    expected="Should look up order status",
    expected_metadata={"tool_calls": ["get_orders"]},
    actual_metadata={"tool_calls": ["get_orders"]},
    metadata_checker=check_tool_calls,
)
```

### With boba.run()

Use `AgentResponse` to return metadata from your agent:

```python
from simboba import Boba, AgentResponse, MessageInput

boba = Boba()

def my_agent(inputs: list[MessageInput]) -> AgentResponse:
    # inputs is the full conversation history
    response = call_my_llm(inputs)
    return AgentResponse(
        output=response.text,
        metadata={"tool_calls": response.tool_calls}
    )

def check_tool_calls(expected, actual):
    if not expected or not actual:
        return True
    return set(expected.get("tool_calls", [])) == set(actual.get("tool_calls", []))

result = boba.run(
    agent=my_agent,
    dataset="my-dataset",
    metadata_checker=check_tool_calls,
)
```

When using `metadata_checker`:

- LLM still sees metadata for context/reasoning
- Your function runs as an additional gate
- Case passes only if **both** LLM judgment and metadata check pass
- Results include `metadata_passed` field for visibility

## Regression Detection

Track regressions across code changes:

```bash
# Run evals and compare to baseline
boba run
# Output shows regressions: "REGRESSIONS: 2 cases now failing"

# Save current results as new baseline
boba baseline
# Commit to git for tracking
git add boba-evals/baselines/
git commit -m "Update eval baseline"
```

## Creating Datasets

### Dataset JSON Structure

Datasets are stored as JSON files in `boba-evals/datasets/`:

```json
{
  "id": "customer-support",
  "name": "customer-support",
  "description": "Customer support chatbot test cases",
  "cases": [
    {
      "id": "case-001",
      "name": "Order status inquiry",
      "inputs": [
        {"role": "user", "message": "What's the status of order #12345?"}
      ],
      "expected_outcome": "Agent should look up and report order status",
      "expected_metadata": {"tool_calls": ["get_order_status"]}
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "case_count": 1
}
```

### Via CLI

```bash
boba generate "A customer support chatbot for an e-commerce site"
```

### Via Web UI

1. `boba serve`
2. Click "New Dataset" -> "Generate with AI"
3. Enter a description of your agent and we'll create test cases for you.

### Via Python

```python
# Create dataset file manually or use the API
from simboba import Boba
boba = Boba()
boba.run(agent, dataset="my-dataset")  # Uses dataset from boba-evals/datasets/
```

## Test Fixtures (setup.py)

Edit `boba-evals/setup.py` to create test data your agent needs:

```python
def get_context():
    """Create test fixtures, return context dict."""
    user = create_test_user(email="eval@test.com")
    return {
        "user_id": user.id,
        "api_token": user.generate_token(),
    }

def cleanup():
    """Clean up test data after evals."""
    delete_test_users()
```

## Environment Variables

Boba loads `.env` automatically. Set your LLM API key for judging (Claude Haiku 4.5 is the default):

```bash
ANTHROPIC_API_KEY=sk-ant-...   # Required for default model (Claude)
OPENAI_API_KEY=sk-...          # For OpenAI models
GEMINI_API_KEY=...             # For Gemini models
```

> **Note:** Without an API key, boba falls back to a simple keyword-matching judge which is less accurate.

## Project Structure

```
your-project/
├── boba-evals/
│   ├── datasets/           # Dataset JSON files (git tracked)
│   ├── baselines/          # Baseline results (git tracked)
│   ├── runs/               # Run history (gitignored)
│   ├── files/              # Uploaded attachments
│   ├── setup.py            # Test fixtures
│   ├── test.py        # Your eval script
│   ├── settings.json       # Configuration
│   └── .boba.yaml          # Runtime config (docker vs local)
└── ...
```

## Future Updates

- **File Uploads** - Allow uploads via UI to help create datasets
- **Eval methods** - Built-in evaluation strategies beyond LLM-as-judge
- **Cloud storage** - Sync datasets and runs to the cloud for team collaboration

## Development

To work on the web UI:

```bash
cd frontend
npm install
npm run dev      # Dev server with hot reload (proxies to localhost:8787)
npm run build    # Build to simboba/static/
```

Run `boba serve` in another terminal to start the backend.

## License

MIT
