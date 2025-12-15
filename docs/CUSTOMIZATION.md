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

## Adding a New Module

1. Create directory: `mindmap/NN_name/`
2. Add `content.md` with module description
3. Create `requirements/` subdirectory
4. Add `content.md` with FR list
5. Add dimension folders: `ui_ux/`, `frontend/`, `backend/`, `ai_data/`
6. Update `features.json` modules mapping
7. Refresh the editor

## Custom AI Prompt

Edit `editor/config/agent_prompt.md` to customize the AI assistant's behavior.
