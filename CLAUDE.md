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

```bash
uv run python scripts/test_openrouter.py
```

This verifies:
1. Environment variables are set correctly
2. Anthropic SDK connects to OpenRouter
3. Claude Agent SDK works with free models
