# Markdown Mindmap Studio

> Interactive mindmap editor using Markdown files as single source of truth

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
git clone https://github.com/YOUR_USERNAME/markdown-mindmap-studio.git
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
├── mindmap/           # Your content (Markdown files)
│   ├── 01_module/
│   │   ├── content.md
│   │   └── requirements/
│   └── ...
├── editor/            # Web editor
│   ├── server.py
│   └── static/
├── scripts/           # Export tools
│   └── export_mindmap.py
└── exports/           # Generated files
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
