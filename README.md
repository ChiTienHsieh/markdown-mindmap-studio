# Markdown Mindmap Studio

> Interactive mindmap editor using Markdown files as single source of truth

English | [繁體中文](README-zh.tw.md)

## Features

- **Markdown-based**: All content stored as plain Markdown files
- **Interactive Mindmap**: Visual tree view with Markmap.js
- **Bidirectional Editing**: Edit markdown or click nodes to update
- **Real-time Sync**: WebSocket-based live updates
- **AI Assistant**: Optional Claude Agent integration for editing help
- **Export**: Generate standalone HTML mindmaps and PDF documents

## Quick Start

```bash
# Clone the repo
git clone https://github.com/ChiTienHsieh/markdown-mindmap-studio.git
cd markdown-mindmap-studio

# Install dependencies
uv sync

# Start the editor
uv run python editor/server.py
# Open http://localhost:3000
```

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
│   └── static/
├── scripts/                 # Export tools
│   └── export_mindmap.py
└── exports/                 # Generated HTML/PDF files
```

## Customization

See [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) for:
- Changing project title and module names
- Adding new modules
- Customizing the AI assistant
- Language/locale settings

## Export

```bash
# Generate HTML mindmap and PDF
uv run python scripts/export_mindmap.py
```

## License

MIT
