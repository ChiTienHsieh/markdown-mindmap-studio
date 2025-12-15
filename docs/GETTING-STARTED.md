# Getting Started

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager

## Installation

1. Clone the repository
2. Run `uv sync` to install dependencies
3. Start the server: `uv run python editor/server.py`
4. Open http://localhost:3000

## Optional: AI Features

To enable the AI assistant:

1. Get an API key from [Anthropic](https://console.anthropic.com/)
2. Set the environment variable:
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   ```
3. Restart the server

## Directory Structure

Your content lives in `mindmap/`. Each module follows this structure:

```
NN_module_name/
├── content.md                 # Module description & user stories
└── requirements/
    ├── content.md             # FR (Functional Requirements) list
    ├── ui_ux/content.md       # UI/UX specifications
    ├── frontend/content.md    # Frontend implementation notes
    ├── backend/content.md     # Backend/API specifications
    └── ai_data/content.md     # AI & Data considerations
```
