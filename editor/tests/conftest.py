"""
Shared pytest fixtures for mindmap editor tests.

These fixtures dynamically discover mindmap structure from the file system,
allowing tests to work with any project content.
"""

import json
import pytest
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
MINDMAP_DIR = PROJECT_ROOT / "mindmap"
CONFIG_PATH = PROJECT_ROOT / "editor" / "config" / "features.json"


@pytest.fixture(scope="session")
def mindmap_structure():
    """
    Dynamically discover mindmap structure from file system.

    Returns a dict with:
    - modules: list of module info (id, has_requirements, dimensions)
    - module_ids: set of module IDs for quick lookup
    """
    modules = []

    if not MINDMAP_DIR.exists():
        return {"modules": [], "module_ids": set()}

    for module_dir in sorted(MINDMAP_DIR.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("."):
            continue

        req_dir = module_dir / "requirements"
        dimensions = []
        if req_dir.exists():
            dimensions = [d.name for d in sorted(req_dir.iterdir()) if d.is_dir()]

        modules.append({
            "id": module_dir.name,
            "path": module_dir,
            "has_requirements": req_dir.exists(),
            "dimensions": dimensions,
            "has_content": (module_dir / "content.md").exists(),
        })

    return {
        "modules": modules,
        "module_ids": {m["id"] for m in modules},
        "module_count": len(modules),
    }


@pytest.fixture(scope="session")
def app_config():
    """
    Load features.json configuration.

    Returns the config dict or empty dict if not found.
    """
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {}


@pytest.fixture(scope="session")
def expected_dimensions():
    """
    Standard dimension directory names (structural constant).

    These are the standard dimension folders that should exist
    under each module's requirements/ directory.
    """
    return ["ui_ux", "frontend", "backend", "ai_data"]
