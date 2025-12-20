# boba

```
     ( )
   .-~~~-.
  /       \
  |  ===  |
  | ::::: |
  |_:::::_|
    '---'
```

LLM eval datasets & judge. Generate test cases, run evals, and judge results with AI.

## Installation

```bash
pip install simboba
```

## Quick Start

```bash
boba init      # Create evals/ folder with template
boba serve     # Start web UI at http://localhost:8787
```

---

## Commands

| Command | Description |
|---------|-------------|
| `boba init` | Create `evals/` folder with starter template |
| `boba serve` | Start web UI (auto-loads evals from `evals/`) |
| `boba serve --config path` | Load specific eval file or folder |
| `boba test` | Test connection to your agent |
| `boba test --eval name` | Test a specific eval |
| `boba evals` | List loaded evals and show any errors |
| `boba run --dataset name` | Run evals headlessly (for CI) |
| `boba datasets` | List all datasets |
| `boba generate "description"` | Generate dataset from CLI |
| `boba export --dataset name -o file.json` | Export dataset |
| `boba import -i file.json` | Import dataset |
| `boba reset` | Delete database (all data) |

---

## Testing Your Setup

Before running full evals, verify your eval function can connect to your agent:

```bash
# Test with default message
boba test

# Test a specific eval
boba test --eval my-agent

# Test with a custom message
boba test -m "What is the status of order 123?"
```

This sends a test message through your eval function and shows the response (or error). Use this to debug connection issues before running full evaluations.

You can also test from the web UI: click "New Run" and then "Test connection first →".

---

## Generating Datasets

Datasets are collections of test cases. Each case has:
- **inputs**: Conversation messages (user/assistant turns)
- **expected_outcome**: What the agent should do

### How to Generate Good Datasets

The key to good test cases is **understanding your app first**. Before generating:

1. **Study your app's logic** - Read the code, understand the flows
2. **Identify key user journeys** - What are the main things users do?
3. **Note edge cases** - What can go wrong? What are the limits?
4. **Describe clearly** - The better your description, the better the test cases

### Writing a Good Description

Bad:
```
A chatbot for construction sites
```

Good:
```
A WhatsApp-based AI assistant for construction site staff.

KEY FLOWS:
1. Daily site logs - User sends photos/voice notes describing work progress,
   weather, labor count, equipment. Agent should extract structured data and
   confirm what was logged.

2. Safety incidents - User reports an incident. Agent must collect: location,
   time, people involved, injuries, witnesses. Must escalate serious incidents.

3. Material requests - User requests materials. Agent checks inventory,
   suggests alternatives if unavailable, creates purchase order.

EDGE CASES:
- User sends unclear voice note - agent should ask for clarification
- User reports injury - agent must immediately escalate, not just log
- User requests unavailable material - agent should suggest alternatives

USERS: Site managers (tech-savvy), foremen (moderate), workers (basic phones)
```

### Via UI

1. Run `boba serve`
2. Click "New Dataset"
3. Choose "Generate with AI"
4. Paste your detailed description
5. Review and edit generated cases

### Via CLI

```bash
boba generate "Your detailed description here"
```

### Best Practices

1. **Study your code first** - Read handlers, prompts, business logic
2. **Map user flows** - List the main journeys step by step
3. **Include multi-turn conversations** - Real users have back-and-forth dialogue
4. **Be specific in expected outcomes** - "Should ask for order number" not "Should help"
5. **Test different user types** - New users, experts, frustrated users
6. **Include failure cases** - What should happen when the agent can't help?
7. **Cover edge cases** - Invalid inputs, missing data, system limits

---

## Writing Evals

Evals connect your agent/API to boba for testing. Create Python files in the `evals/` folder.

### Basic Structure

```python
from simboba import Eval

def my_agent(messages):
    """
    Called for each test case.

    Args:
        messages: List of conversation messages
            [{"role": "user", "message": "...", "attachments": []}, ...]

    Returns:
        Agent's response as a string
    """
    # Call your API and return the response
    response = requests.post("http://localhost:8000/chat", json={
        "messages": [{"role": m["role"], "content": m["message"]} for m in messages]
    })
    return response.json()["response"]

# Register the eval
my_eval = Eval(name="my-agent", fn=my_agent)
```

### Common Patterns

**Direct Python Call (simplest):**
```python
# Import your agent directly - no HTTP/auth needed
from my_project.agent import generate_response

def my_agent(messages):
    # Call your function directly
    return generate_response(messages[-1]["message"])

my_eval = Eval(name="my-agent", fn=my_agent)
```

**HTTP API:**
```python
def my_agent(messages):
    resp = requests.post("http://localhost:8000/chat", json={"messages": messages})
    return resp.json()["response"]
```

**Async/Webhook API:**
```python
def my_agent(messages):
    # Trigger webhook
    job = requests.post("http://localhost:8000/webhook", json={"message": messages[-1]})
    job_id = job.json()["job_id"]

    # Poll for result
    for _ in range(30):
        time.sleep(1)
        result = requests.get(f"http://localhost:8000/jobs/{job_id}")
        if result.json()["status"] == "complete":
            return result.json()["response"]

    raise TimeoutError("Agent didn't respond")
```

**With Auth/Setup:**
```python
# Setup runs once when file loads
API_KEY = os.environ["MY_API_KEY"]
TEST_USER = create_test_user()

def my_agent(messages):
    resp = requests.post(
        "http://localhost:8000/chat",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"user_id": TEST_USER["id"], "messages": messages}
    )
    return resp.json()["response"]

my_eval = Eval(name="my-agent", fn=my_agent)
```

---

## Running Evals

### Via UI

1. Run `boba serve`
2. Go to "Runs" tab
3. Click "New Run"
4. Select dataset and eval
5. View results with pass/fail and reasoning

### Via CLI (for CI)

```bash
boba run --dataset my-dataset
```

### How Judging Works

1. Your eval function receives the test case inputs
2. Your function calls your agent and returns its response
3. An LLM judge compares the response against the expected outcome
4. Judge returns pass/fail with reasoning

---

## Environment Variables

Boba automatically loads `.env` files from the current directory.

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | For Claude models (generation & judging) |
| `OPENAI_API_KEY` | For OpenAI models |
| `GEMINI_API_KEY` | For Gemini models |

### Environment Variables in Eval Files

**Important:** Validate environment variables inside your eval function, not at module level. This prevents silent import failures and gives clear error messages.

```python
# BAD - fails silently if env var is missing
API_KEY = os.environ["MY_API_KEY"]  # Module level = import error

def my_agent(messages):
    ...

# GOOD - clear error when the eval actually runs
def my_agent(messages):
    api_key = os.environ.get("MY_API_KEY")
    if not api_key:
        raise ValueError("MY_API_KEY not set")
    ...
```

If your eval files aren't showing up, run `boba evals` to see import errors.

---

## Project Structure

After running `boba init`:

```
your-project/
├── evals/
│   ├── .gitignore     # Ignores database
│   ├── README.md      # This file
│   ├── example.py     # Starter template
│   └── simboba.db     # Database (created on first run, not tracked)
└── ...
```

## License

MIT
