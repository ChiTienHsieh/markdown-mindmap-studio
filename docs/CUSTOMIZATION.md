# Customization Guide

## Configuration

All settings are in `editor/config/features.json`.

### Project Settings

```json
{
  "project": {
    "name": "your-project",
    "title": "Your Project Title"
  }
}
```

### Module Names

Map directory names to display names:

```json
{
  "modules": {
    "01_users": "User Management",
    "02_billing": "Billing System"
  }
}
```

### Language

Set the default locale:

```json
{
  "ui": {
    "defaultLocale": "en",
    "supportedLocales": ["en", "zh-TW"]
  }
}
```

## Adding Content

The mindmap supports any nested directory structure. Each `content.md` file becomes a node.

### Basic Structure

```
mindmap/
├── 01_topic/
│   ├── content.md          # Parent node content
│   ├── subtopic_a/
│   │   └── content.md      # Child node
│   └── subtopic_b/
│       ├── content.md      # Child node
│       └── nested_item/
│           └── content.md  # Grandchild node
└── 02_another_topic/
    └── content.md
```

### Steps

1. Create directory: `mindmap/NN_name/`
2. Add `content.md` with your content (first line = title, rest = description)
3. Create subdirectories for child nodes, each with its own `content.md`
4. Nest as deep as needed - the tree will reflect your directory structure
5. (Optional) Update `features.json` modules mapping for custom display names
6. Refresh the editor

## Custom AI Prompt

Edit `editor/config/agent_prompt.md` to customize the AI assistant's behavior.
