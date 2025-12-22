# Claude Code Instructions

## OpenRouter Setup (Free Models)

This project uses OpenRouter to access free LLM models for development/testing.

### Privacy Policy Choice

We have enabled **"Enable free endpoints that may publish prompts"** in OpenRouter settings.
This allows using free models, with the tradeoff that prompts/completions may be published to public datasets.

See: https://openrouter.ai/settings/privacy

### Environment Variables

The `.env` file configures OpenRouter integration:

```bash
# OpenRouter API Configuration
ANTHROPIC_BASE_URL=https://openrouter.ai/api
ANTHROPIC_AUTH_TOKEN=<your-openrouter-api-key>
ANTHROPIC_API_KEY=""  # Must be empty string

# Force FREE model
ANTHROPIC_MODEL=openai/gpt-oss-120b:free
ANTHROPIC_SMALL_FAST_MODEL=openai/gpt-oss-120b:free
```

### Free Model Choice

We use `openai/gpt-oss-120b:free` based on:
- SWE-bench Verified score: 62.4%
- High popularity on OpenRouter (212B tokens usage)
- Good balance of capability and availability

Other free model options:
- `qwen/qwen3-coder:free` - 262K context, strong coding
- `mistralai/devstral-2512:free` - 262K context, agentic coding specialist
- `deepseek/deepseek-r1-0528:free` - 163K context, strong reasoning

### Testing

Start the server and test the Agent Chat panel:

```bash
uv run python editor/server.py
# Open http://localhost:3000 and use the Agent Chat panel
```

## Claude Agent SDK Integration

### Message Type Handling

The Agent SDK returns typed message classes, not string types:

```python
from claude_agent_sdk import (
    AssistantMessage,  # Contains content blocks (TextBlock, ToolUseBlock, ThinkingBlock)
    ResultMessage,     # Final result with success/error status
    SystemMessage,     # Init messages (tools, model, session_id)
    TextBlock,         # Text response content
    ThinkingBlock,     # Internal reasoning (skip in UI)
    ToolUseBlock,      # Tool invocation info
)

# Use isinstance() to check message types
async for message in client.receive_response():
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                # Display text to user
            elif isinstance(block, ToolUseBlock):
                # Show tool usage indicator
            elif isinstance(block, ThinkingBlock):
                # Skip (internal reasoning)
    elif isinstance(message, ResultMessage):
        # Check message.is_error for success/failure
    elif isinstance(message, SystemMessage):
        # Skip init messages
```

### Environment Variables for OpenRouter

The server loads `.env` via python-dotenv. For Agent SDK availability:

```python
AGENT_SDK_AVAILABLE = bool(
    os.environ.get("ANTHROPIC_API_KEY") or
    os.environ.get("ANTHROPIC_AUTH_TOKEN")  # OpenRouter uses AUTH_TOKEN
)
```
