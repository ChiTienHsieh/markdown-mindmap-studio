# Markdown Mindmap Studio

[![CI](https://github.com/ChiTienHsieh/markdown-mindmap-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/ChiTienHsieh/markdown-mindmap-studio/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/ChiTienHsieh/markdown-mindmap-studio/pulls)

> Interactive mindmap editor using Markdown files as single source of truth ヽ(・∀・)ノ

English | [繁體中文](README-zh.tw.md)

![Demo](docs/images/demo.gif)

## Features

- **Markdown-based**: All content stored as plain Markdown files - version control friendly
- **Interactive Mindmap**: Beautiful visual tree view powered by Markmap.js
- **Bidirectional Editing**: Edit markdown directly or click nodes to update
- **Real-time Sync**: WebSocket-based live updates across all views (๑•̀ㅂ•́)و✧
- **Dark/Light Theme**: Toggle between themes with persistence
- **Export Options**: PNG image, standalone HTML, and PDF document
- **AI Assistant**: Optional Claude Agent integration for smart editing (requires API key)

## Quick Start

```bash
# Clone the repo
git clone https://github.com/ChiTienHsieh/markdown-mindmap-studio.git
cd markdown-mindmap-studio

# Install dependencies (requires uv - https://docs.astral.sh/uv/)
uv sync

# Start the editor
uv run python editor/server.py

# Open http://localhost:3000 in your browser
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + 1` | Toggle file sidebar |
| `Cmd/Ctrl + 2` | Toggle markdown editor |
| `Cmd/Ctrl + 3` | Toggle AI agent panel |
| `Cmd/Ctrl + S` | Save current file |

## Project Structure

```
markdown-mindmap-studio/
├── mindmap/                 # Your content (nested directories with content.md)
│   ├── 01_topic/
│   │   ├── content.md       # Topic content
│   │   ├── subtopic_a/
│   │   │   └── content.md
│   │   └── subtopic_b/
│   │       └── content.md
│   └── 02_another_topic/
│       └── ...
├── editor/                  # Web editor (FastAPI + vanilla JS)
│   ├── server.py
│   ├── static/
│   └── tests/
├── scripts/                 # Export tools
│   └── export_mindmap.py
└── exports/                 # Generated HTML/PDF files
```

## Export

Export your mindmap directly from the UI using the **Export** button, or via command line:

```bash
# Generate HTML mindmap and PDF document
uv run python scripts/export_mindmap.py

# Files are saved to exports/
```

## Customization

See [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) for:
- Changing project title and module names
- Adding new modules
- Customizing the AI assistant
- Language/locale settings

## AI Assistant (Optional)

### Option 1: Anthropic API (Paid)

```bash
export ANTHROPIC_API_KEY=your-key-here
uv run python editor/server.py
```

### Option 2: OpenRouter Free Models

Use free models via OpenRouter (prompts may be published to public datasets):

1. Get an API key from [openrouter.ai](https://openrouter.ai)
2. Enable "free endpoints that may publish prompts" in [Privacy Settings](https://openrouter.ai/settings/privacy)
3. Create `.env` file:

```bash
ANTHROPIC_BASE_URL=https://openrouter.ai/api
ANTHROPIC_AUTH_TOKEN=your-openrouter-key
ANTHROPIC_API_KEY=""
ANTHROPIC_MODEL=openai/gpt-oss-120b:free
ANTHROPIC_SMALL_FAST_MODEL=openai/gpt-oss-120b:free
```

4. Run with dotenv:

```bash
uv run python editor/server.py
```

See [CLAUDE.md](CLAUDE.md) for more details on free model options.

## Tech Stack

- **Backend**: FastAPI, WebSocket, Python 3.12+
- **Frontend**: Vanilla JS, Markmap.js, D3.js
- **Export**: WeasyPrint (PDF), Pure Python HTML generation

## Contributing

PRs are welcome! Please open an issue first to discuss what you'd like to change (ﾉ´ヮ`)ﾉ*: ・ﾟ✧

## License

[MIT](LICENSE)
