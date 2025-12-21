#!/usr/bin/env python3
"""
Mindmap Editor Server

A FastAPI server that:
- Serves the editor frontend
- Provides API to read/write markdown files
- WebSocket for live updates
- AI assistant for editing markdown (Phase 3)

Usage:
    cd editor && uv run python server.py
    # Then open http://localhost:3000

Environment:
    ANTHROPIC_API_KEY - Required for AI features
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mindmap-editor")

# Constants
MAX_FILE_SIZE = 1024 * 1024  # 1MB max file size to prevent DoS
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from pydantic import BaseModel

# Claude Agent SDK imports (optional - graceful fallback if not configured)
try:
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    AGENT_SDK_AVAILABLE = bool(os.environ.get("ANTHROPIC_API_KEY"))
except ImportError:
    AGENT_SDK_AVAILABLE = False

# Paths
EDITOR_DIR = Path(__file__).parent
PROJECT_ROOT = EDITOR_DIR.parent
MINDMAP_DIR = PROJECT_ROOT / "mindmap"
STATIC_DIR = EDITOR_DIR / "static"
CONFIG_DIR = EDITOR_DIR / "config"

# Load configuration
def load_config() -> dict:
    """Load configuration from features.json"""
    config_path = CONFIG_DIR / "features.json"
    if config_path.exists():
        config = json.loads(config_path.read_text())
        return config
    return {
        "project": {"title": "Mindmap Editor"},
        "modules": {},
        "dimensions": {"ui_ux": "UI/UX", "frontend": "Frontend", "backend": "Backend", "ai_data": "AI & Data", "specs": "SPEC Links"},
        "agent": {"model": "claude-haiku-4-5-20251201", "maxTokens": 4096, "allowedTools": ["Read", "Edit", "Write", "Glob", "Grep"]}
    }

CONFIG = load_config()


def load_agent_prompt() -> str:
    """Load agent system prompt from file or config"""
    prompt_file = CONFIG.get("agent", {}).get("systemPromptFile")
    if prompt_file:
        prompt_path = PROJECT_ROOT / prompt_file
        if prompt_path.exists():
            return prompt_path.read_text()
    # Fallback to inline config or default
    return CONFIG.get("agent", {}).get("systemPrompt", "You are a mindmap editor assistant.")

app = FastAPI(title="Mindmap Editor")

# --- Security: Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

# --- Security: CORS Configuration ---
# Restrict to localhost origins for local development
# Modify this list if deploying to production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# WebSocket connections for live updates
connected_clients: list[WebSocket] = []


# --- Models ---

class FileContent(BaseModel):
    path: str
    content: str


class NodeUpdate(BaseModel):
    """Update from mindmap UI"""
    file_path: str
    node_path: list[str]  # Path to node in tree (e.g., ["FR-MAP-01", "description"])
    old_value: str
    new_value: str


class AgentChatRequest(BaseModel):
    """Request for agent chat"""
    message: str  # User message
    session_id: Optional[str] = None  # Session ID for multi-turn conversations


# --- API Routes ---

@app.get("/")
async def index():
    """Serve the editor frontend"""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/files")
async def list_files():
    """List all content.md files in mindmap/ directory structure"""
    files = []
    for content_file in sorted(MINDMAP_DIR.rglob("content.md")):
        rel_path = content_file.relative_to(MINDMAP_DIR)
        files.append({
            "path": str(rel_path),
            "name": content_file.name,
            "module": str(rel_path.parts[0]) if len(rel_path.parts) > 0 else None
        })
    return {"files": files}


@app.get("/api/files/{file_path:path}")
async def read_file(file_path: str):
    """Read a markdown file"""
    # SECURITY: Validate path FIRST before any file operations
    full_path = (MINDMAP_DIR / file_path).resolve()
    if not str(full_path).startswith(str(MINDMAP_DIR.resolve())):
        logger.warning(f"Path traversal attempt blocked: {file_path}")
        raise HTTPException(status_code=403, detail="Access denied")
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    if not full_path.is_file():
        raise HTTPException(status_code=400, detail=f"Not a file: {file_path}")

    content = full_path.read_text(encoding="utf-8")
    return {"path": file_path, "content": content}


@app.put("/api/files/{file_path:path}")
async def write_file(file_path: str, data: FileContent):
    """Write/update a markdown file"""
    # SECURITY: Validate path FIRST before any file operations
    full_path = (MINDMAP_DIR / file_path).resolve()
    if not str(full_path).startswith(str(MINDMAP_DIR.resolve())):
        logger.warning(f"Path traversal attempt blocked: {file_path}")
        raise HTTPException(status_code=403, detail="Access denied")

    # Validate file size to prevent DoS
    if len(data.content.encode("utf-8")) > MAX_FILE_SIZE:
        logger.warning(f"File size limit exceeded: {file_path} ({len(data.content)} bytes)")
        raise HTTPException(status_code=413, detail=f"File too large. Max size: {MAX_FILE_SIZE} bytes")

    # Create parent directories if needed
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    full_path.write_text(data.content, encoding="utf-8")
    logger.info(f"File written: {file_path}")

    # Notify all connected clients
    await broadcast_update({
        "type": "file_updated",
        "path": file_path,
        "content": data.content
    })

    return {"status": "ok", "path": file_path}


@app.get("/api/config")
async def get_config():
    """Get application configuration"""
    config_path = Path(__file__).parent / "config" / "features.json"
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {"mindmap": {"maxFrItems": 100, "maxDimensionItems": 100, "maxDescriptionLength": 200}}


@app.get("/api/locales/{locale}")
async def get_locale(locale: str):
    """Get locale strings"""
    # SECURITY: Validate locale format (e.g., "en", "zh-TW", "en-US")
    if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', locale):
        raise HTTPException(status_code=400, detail="Invalid locale format")

    locale_path = EDITOR_DIR / "locales" / f"{locale}.json"
    if not locale_path.exists():
        # Fallback to English
        locale_path = EDITOR_DIR / "locales" / "en.json"
    if locale_path.exists():
        return json.loads(locale_path.read_text())
    return {}


@app.get("/api/tree")
async def get_tree():
    """Get the full document tree for mindmap rendering - supports any directory structure"""

    def read_content_file(path: Path) -> str:
        """Helper to read content.md file, return empty string if not exists"""
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def build_tree_recursive(directory: Path) -> dict:
        """Recursively build tree from directory structure"""
        result = {
            "id": directory.name,
            "name": CONFIG.get("modules", {}).get(directory.name, directory.name),
            "content": read_content_file(directory / "content.md"),
            "children": []
        }

        # Get all subdirectories (sorted alphabetically)
        for subdir in sorted(directory.iterdir()):
            if subdir.is_dir() and not subdir.name.startswith("."):
                child = build_tree_recursive(subdir)
                result["children"].append(child)

        return result

    modules = []

    # Walk through module directories
    for module_dir in sorted(MINDMAP_DIR.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("."):
            continue

        module = build_tree_recursive(module_dir)
        modules.append(module)

    return {
        "title": CONFIG.get("project", {}).get("title", "Mindmap"),
        "modules": modules
    }


# --- Claude Agent SDK ---

AGENT_SYSTEM_PROMPT = load_agent_prompt()

# Store active agent sessions (in production, use Redis or database)
agent_sessions: dict[str, ClaudeSDKClient] = {}


@app.get("/api/agent/status")
async def agent_status():
    """Check if Claude Agent SDK is available"""
    return {
        "available": AGENT_SDK_AVAILABLE,
        "message": "Agent ready" if AGENT_SDK_AVAILABLE else "Claude Agent SDK not available"
    }


@app.post("/api/agent/chat")
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute per IP
async def agent_chat(request: Request, chat_request: AgentChatRequest):
    """Chat with Claude Agent (streaming SSE response)"""
    if not AGENT_SDK_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Agent not available. Install claude-agent-sdk and set ANTHROPIC_API_KEY."
        )

    async def generate():
        try:
            agent_config = CONFIG.get("agent", {})
            options = ClaudeAgentOptions(
                system_prompt=AGENT_SYSTEM_PROMPT,
                allowed_tools=agent_config.get("allowedTools", ["Read", "Edit", "Write", "Glob", "Grep"]),
                permission_mode="acceptEdits",
                cwd=str(PROJECT_ROOT),
                model=agent_config.get("model", "claude-haiku-4-5-20251201"),
            )

            async with ClaudeSDKClient(options=options) as client:
                await client.query(chat_request.message)

                async for message in client.receive_response():
                    # Handle different message types from the SDK
                    if hasattr(message, 'type'):
                        if message.type == 'assistant':
                            # Extract text content
                            for block in getattr(message, 'content', []):
                                if hasattr(block, 'text'):
                                    yield f"data: {json.dumps({'type': 'text', 'content': block.text})}\n\n"
                                elif hasattr(block, 'type') and block.type == 'tool_use':
                                    yield f"data: {json.dumps({'type': 'tool_use', 'tool': block.name})}\n\n"
                        elif message.type == 'result':
                            yield f"data: {json.dumps({'type': 'result', 'content': str(getattr(message, 'result', ''))})}\n\n"
                    else:
                        # Fallback for unknown message format
                        yield f"data: {json.dumps({'type': 'message', 'content': str(message)})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# --- WebSocket ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "node_update":
                await handle_node_update(message, websocket)
            elif message.get("type") == "request_sync":
                # Send current tree state
                tree = await get_tree()
                await websocket.send_json({"type": "sync", "tree": tree})

    except WebSocketDisconnect:
        connected_clients.remove(websocket)


async def handle_node_update(message: dict, sender: WebSocket):
    """Handle a node update from the mindmap UI"""
    file_path = message.get("file_path")
    line_number = message.get("line_number")
    old_text = message.get("old_text")
    new_text = message.get("new_text")

    if not all([file_path, old_text is not None, new_text is not None]):
        await sender.send_json({"type": "error", "message": "Invalid update message"})
        return

    # SECURITY: Validate path FIRST before any file operations
    full_path = (MINDMAP_DIR / file_path).resolve()
    if not str(full_path).startswith(str(MINDMAP_DIR.resolve())):
        logger.warning(f"WebSocket path traversal attempt blocked: {file_path}")
        await sender.send_json({"type": "error", "message": "Access denied"})
        return
    if not full_path.exists():
        await sender.send_json({"type": "error", "message": f"File not found: {file_path}"})
        return

    # Read and update file
    content = full_path.read_text(encoding="utf-8")

    # Use line-based replacement if line_number is provided
    if line_number is not None:
        lines = content.split('\n')

        # Convert to 0-based index (frontend sends 1-based line numbers)
        line_idx = line_number - 1

        if 0 <= line_idx < len(lines):
            if old_text in lines[line_idx]:
                # Replace only on the target line
                lines[line_idx] = lines[line_idx].replace(old_text, new_text, 1)
                new_content = '\n'.join(lines)
                full_path.write_text(new_content, encoding="utf-8")

                # Broadcast to all clients
                await broadcast_update({
                    "type": "file_updated",
                    "path": file_path,
                    "content": new_content
                })

                await sender.send_json({"type": "update_success", "path": file_path})
            else:
                await sender.send_json({
                    "type": "error",
                    "message": f"Text not found at line {line_number}. The file may have been modified."
                })
        else:
            await sender.send_json({
                "type": "error",
                "message": f"Invalid line number: {line_number}. File has {len(lines)} lines."
            })
    else:
        # Fallback to first-match replacement if no line_number provided
        if old_text in content:
            new_content = content.replace(old_text, new_text, 1)
            full_path.write_text(new_content, encoding="utf-8")

            # Broadcast to all clients
            await broadcast_update({
                "type": "file_updated",
                "path": file_path,
                "content": new_content
            })

            await sender.send_json({"type": "update_success", "path": file_path})
        else:
            await sender.send_json({
                "type": "error",
                "message": f"Text not found in file. The file may have been modified."
            })


async def broadcast_update(message: dict):
    """Broadcast update to all connected WebSocket clients"""
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception as e:
            logger.debug(f"Failed to send to client (likely disconnected): {e}")


# --- Static files (must be last) ---

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- Run server ---

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("Mindmap Editor Server")
    print("=" * 50)
    print()
    print(f"Mindmap directory: {MINDMAP_DIR}")
    print(f"Open http://localhost:3000 in your browser")
    print()
    uvicorn.run(app, host="127.0.0.1", port=3000)
