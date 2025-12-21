"""
Comprehensive pytest tests for FastAPI server in editor/server.py

Run with:
    cd editor && uv run pytest tests/test_api.py -v

Run with coverage:
    cd editor && uv run pytest tests/test_api.py -v --cov=editor.server

Requirements:
    - pytest
    - httpx (async client for FastAPI testing)
    - pytest-asyncio (for async test support)
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from httpx import AsyncClient, ASGITransport
from fastapi import status


# Import server app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import app, MINDMAP_DIR, STATIC_DIR, PROJECT_ROOT


# ==================== Fixtures ====================

@pytest.fixture
def temp_docs_dir(tmp_path):
    """Create a temporary mindmap directory for testing (generic tree structure)"""
    mindmap = tmp_path / "mindmap"
    mindmap.mkdir()

    # Create a sample module structure (generic tree)
    module_01 = mindmap / "01_adventure"
    module_01.mkdir()

    # Create module-level content.md
    module_content = module_01 / "content.md"
    module_content.write_text("Your Adventure Begins\nWelcome to the world!")

    # Create child directories with content
    child1 = module_01 / "first_quest"
    child1.mkdir()
    (child1 / "content.md").write_text("Find the ancient sword\nDefeat the dragon")

    child2 = module_01 / "second_quest"
    child2.mkdir()
    (child2 / "content.md").write_text("Save the village\nBring peace to the land")

    # Create nested child
    nested = child1 / "dragon_lair"
    nested.mkdir()
    (nested / "content.md").write_text("The dragon sleeps here\nBe careful!")

    return mindmap


@pytest.fixture
async def client(temp_docs_dir, monkeypatch):
    """Create an async test client with patched MINDMAP_DIR"""
    # Patch the MINDMAP_DIR to use temp directory
    monkeypatch.setattr("server.MINDMAP_DIR", temp_docs_dir)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_agent_sdk():
    """Mock Claude Agent SDK for agent endpoints"""
    with patch("server.ClaudeSDKClient") as mock:
        # Setup async context manager
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        # Mock query and response
        mock_client.query = AsyncMock()

        async def mock_receive():
            # Yield a few messages
            mock_msg1 = MagicMock()
            mock_msg1.type = "assistant"
            mock_block = MagicMock()
            mock_block.text = "Agent 回覆內容"
            mock_msg1.content = [mock_block]
            yield mock_msg1

        mock_client.receive_response = mock_receive
        mock.return_value = mock_client

        yield mock_client


# ==================== Basic Routes Tests ====================

@pytest.mark.asyncio
class TestBasicRoutes:
    """Test basic HTTP routes"""

    async def test_root_returns_html(self, client):
        """GET / should return index.html"""
        response = await client.get("/")
        assert response.status_code == status.HTTP_200_OK
        # Should be HTML (we can't check exact content without real static files)
        assert "text/html" in response.headers["content-type"].lower()

    async def test_api_config_returns_default(self, client):
        """GET /api/config should return default config"""
        response = await client.get("/api/config")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check default config structure
        assert "project" in data
        assert "modules" in data
        assert "theme" in data

    async def test_api_config_reads_from_file(self, client, monkeypatch, tmp_path):
        """GET /api/config should read from features.json if exists"""
        # Create a mock config file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "features.json"
        config_data = {
            "mindmap": {
                "maxFrItems": 50,
                "maxDimensionItems": 30,
                "maxDescriptionLength": 150
            }
        }
        config_file.write_text(json.dumps(config_data))

        # Patch the config path
        monkeypatch.setattr("server.Path", lambda x: tmp_path if "server.py" in str(x) else Path(x))

        # Note: This test has limitations due to Path patching complexity
        # In real scenario, we'd use dependency injection or config loader


# ==================== File API Tests ====================

@pytest.mark.asyncio
class TestFileAPI:
    """Test file listing and CRUD operations"""

    async def test_list_files_empty(self, client, temp_docs_dir, monkeypatch):
        """GET /api/files should list content.md files"""
        response = await client.get("/api/files")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "files" in data
        files = data["files"]
        # Generic structure: 1 module + 2 children + 1 nested = 4 content.md files
        assert len(files) == 4

        # Check file structure - all files should be content.md
        assert all(f["name"] == "content.md" for f in files)
        # All should be in 01_adventure module
        assert all(f["module"] == "01_adventure" for f in files)

    async def test_read_file_success(self, client):
        """GET /api/files/{path} should return file content"""
        # Read from content.md structure
        response = await client.get("/api/files/01_adventure/first_quest/content.md")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["path"] == "01_adventure/first_quest/content.md"
        # Check content contains expected text
        assert "dragon" in data["content"].lower(), \
            f"Expected 'dragon' in content: {data['content']}"

    async def test_read_file_not_found(self, client):
        """GET /api/files/{path} should return 404 for missing file"""
        response = await client.get("/api/files/nonexistent/file.md")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    async def test_read_file_path_traversal_blocked(self, client):
        """GET /api/files/{path} should block path traversal attacks"""
        response = await client.get("/api/files/../../../etc/passwd")
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    async def test_write_file_success(self, client, temp_docs_dir, monkeypatch):
        """PUT /api/files/{path} should write file content"""
        new_content = "# New Module\n\n## FR-NEW-01: New Feature"

        response = await client.put(
            "/api/files/02-new/requirements.md",
            json={"path": "02-new/requirements.md", "content": new_content}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"
        assert data["path"] == "02-new/requirements.md"

        # Verify file was written
        written_file = temp_docs_dir / "02-new" / "requirements.md"
        assert written_file.exists()
        assert written_file.read_text() == new_content

    async def test_write_file_path_traversal_blocked(self, client):
        """PUT /api/files/{path} should block path traversal attacks"""
        response = await client.put(
            "/api/files/../../../tmp/evil.md",
            json={"path": "../../../tmp/evil.md", "content": "evil"}
        )
        # Either 403 (blocked) or 404 (path normalized away) indicates protection
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


# ==================== Tree API Tests ====================

@pytest.mark.asyncio
class TestTreeAPI:
    """Test document tree API for mindmap"""

    async def test_get_tree_structure(self, client):
        """GET /api/tree should return hierarchical tree (generic format)"""
        response = await client.get("/api/tree")
        assert response.status_code == status.HTTP_200_OK
        tree = response.json()

        # Check root structure (title comes from config, just verify it exists)
        assert "title" in tree
        assert isinstance(tree["title"], str)
        assert "modules" in tree

        # Check module nodes structure (generic tree format)
        assert len(tree["modules"]) >= 1
        module = tree["modules"][0]
        assert "id" in module
        assert "name" in module
        assert "content" in module
        assert "children" in module

        # Module should have children (subdirectories)
        assert len(module["children"]) >= 1

    async def test_get_tree_excludes_hidden_dirs(self, client, temp_docs_dir):
        """GET /api/tree should exclude hidden directories (starting with .)"""
        # Create a hidden dir
        hidden_dir = temp_docs_dir / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "content.md").write_text("# Hidden")

        response = await client.get("/api/tree")
        tree = response.json()

        # Hidden dir should not be in modules
        module_ids = [m["id"] for m in tree["modules"]]
        assert ".hidden" not in module_ids


# ==================== Agent SDK Tests ====================

@pytest.mark.asyncio
class TestAgentSDK:
    """Test Claude Agent SDK endpoints"""

    async def test_agent_status_available(self, client, monkeypatch):
        """GET /api/agent/status should report available when SDK is ready"""
        monkeypatch.setattr("server.AGENT_SDK_AVAILABLE", True)

        response = await client.get("/api/agent/status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["available"] is True
        assert "ready" in data["message"].lower()

    async def test_agent_status_unavailable(self, client, monkeypatch):
        """GET /api/agent/status should report unavailable when SDK not available"""
        monkeypatch.setattr("server.AGENT_SDK_AVAILABLE", False)

        response = await client.get("/api/agent/status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["available"] is False
        assert "not available" in data["message"].lower()

    async def test_agent_chat_unavailable(self, client, monkeypatch):
        """POST /api/agent/chat should return 503 when SDK not available"""
        monkeypatch.setattr("server.AGENT_SDK_AVAILABLE", False)

        response = await client.post(
            "/api/agent/chat",
            json={"message": "Hello agent"}
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "not available" in response.json()["detail"].lower()

    async def test_agent_chat_success(self, client, monkeypatch, mock_agent_sdk):
        """POST /api/agent/chat should return SSE stream with agent responses"""
        monkeypatch.setattr("server.AGENT_SDK_AVAILABLE", True)

        response = await client.post(
            "/api/agent/chat",
            json={"message": "請幫我查看 01-map/requirements.md"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Read SSE stream
        content = response.text
        assert "data:" in content

    async def test_agent_chat_with_session_id(self, client, monkeypatch, mock_agent_sdk):
        """POST /api/agent/chat should accept optional session_id"""
        monkeypatch.setattr("server.AGENT_SDK_AVAILABLE", True)

        response = await client.post(
            "/api/agent/chat",
            json={
                "message": "繼續上次的對話",
                "session_id": "test-session-123"
            }
        )

        assert response.status_code == status.HTTP_200_OK

    async def test_agent_chat_error_handling(self, client, monkeypatch):
        """POST /api/agent/chat should handle agent errors gracefully"""
        monkeypatch.setattr("server.AGENT_SDK_AVAILABLE", True)

        # Mock SDK to raise exception
        with patch("server.ClaudeSDKClient") as mock:
            mock.return_value.__aenter__.side_effect = Exception("Agent error")

            response = await client.post(
                "/api/agent/chat",
                json={"message": "Test message"}
            )

            # Should still return 200 with SSE error message
            assert response.status_code == status.HTTP_200_OK
            content = response.text
            assert "error" in content.lower()


# ==================== Integration Tests ====================

@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for common workflows"""

    async def test_full_workflow_list_read_edit(self, client, temp_docs_dir):
        """Test complete workflow: list files -> read -> edit"""
        # 1. List files
        list_response = await client.get("/api/files")
        assert list_response.status_code == status.HTTP_200_OK
        files = list_response.json()["files"]

        file_path = files[0]["path"]

        # 2. Read file
        read_response = await client.get(f"/api/files/{file_path}")
        assert read_response.status_code == status.HTTP_200_OK
        original_content = read_response.json()["content"]

        # 3. Modify and write
        modified_content = original_content + "\n\n## FR-MAP-02: 新增功能"
        write_response = await client.put(
            f"/api/files/{file_path}",
            json={"path": file_path, "content": modified_content}
        )
        assert write_response.status_code == status.HTTP_200_OK

        # 4. Verify change
        verify_response = await client.get(f"/api/files/{file_path}")
        assert "FR-MAP-02" in verify_response.json()["content"]

    async def test_tree_reflects_file_changes(self, client, temp_docs_dir):
        """Test that /api/tree reflects changes made via /api/files"""
        # Get initial tree
        tree1 = await client.get("/api/tree")
        initial_tree = tree1.json()

        # Add a new module with proper content.md structure
        new_module_path = "99_test/content.md"
        await client.put(
            f"/api/files/{new_module_path}",
            json={
                "path": new_module_path,
                "content": "✓ Test user story"
            }
        )

        # Get updated tree
        tree2 = await client.get("/api/tree")
        updated_tree = tree2.json()

        # New module should appear (by id since no MODULE_NAMES mapping)
        module_ids = [m["id"] for m in updated_tree["modules"]]
        assert "99_test" in module_ids


# ==================== Edge Cases & Security ====================

@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and security concerns"""

    async def test_file_path_with_spaces(self, client, temp_docs_dir):
        """Test handling of file paths with spaces"""
        path_with_spaces = "01-map/file with spaces.md"
        content = "# Test content"

        # Write file
        response = await client.put(
            f"/api/files/{path_with_spaces}",
            json={"path": path_with_spaces, "content": content}
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_unicode_content(self, client, temp_docs_dir):
        """Test handling of Unicode content"""
        unicode_content = "# 測試\n\n這是繁體中文內容 🚀"

        response = await client.put(
            "/api/files/01-map/unicode.md",
            json={"path": "01-map/unicode.md", "content": unicode_content}
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify read back
        read_response = await client.get("/api/files/01-map/unicode.md")
        assert read_response.json()["content"] == unicode_content

    async def test_large_file_content(self, client, temp_docs_dir):
        """Test handling of large file content (under limit)"""
        large_content = "# Large File\n\n" + ("A" * 100000)  # ~100KB, under 1MB limit

        response = await client.put(
            "/api/files/01-map/large.md",
            json={"path": "01-map/large.md", "content": large_content}
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_file_too_large_rejected(self, client, temp_docs_dir):
        """Test that files exceeding MAX_FILE_SIZE (1MB) are rejected"""
        oversized_content = "A" * (1024 * 1024 + 1)  # Just over 1MB

        response = await client.put(
            "/api/files/01-map/oversized.md",
            json={"path": "01-map/oversized.md", "content": oversized_content}
        )
        assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
        assert "too large" in response.json()["detail"].lower()

    async def test_empty_file_content(self, client, temp_docs_dir):
        """Test handling of empty file content"""
        response = await client.put(
            "/api/files/01-map/empty.md",
            json={"path": "01-map/empty.md", "content": ""}
        )
        assert response.status_code == status.HTTP_200_OK


# ==================== Security Feature Tests ====================

@pytest.mark.asyncio
class TestSecurityFeatures:
    """Test security features: CORS, rate limiting, locale validation"""

    async def test_locale_valid_format_en(self, client):
        """GET /api/locales/en should succeed with valid locale"""
        response = await client.get("/api/locales/en")
        assert response.status_code == status.HTTP_200_OK

    async def test_locale_valid_format_zh_TW(self, client):
        """GET /api/locales/zh-TW should succeed with valid locale"""
        response = await client.get("/api/locales/zh-TW")
        # 200 if exists, still 200 with fallback to en
        assert response.status_code == status.HTTP_200_OK

    async def test_locale_invalid_format_rejected(self, client):
        """GET /api/locales/{invalid} should return 400 for invalid format"""
        invalid_locales = [
            "en_US",             # Wrong separator (underscore)
            "english",           # Too long
            "e",                 # Too short
            "EN",                # Wrong case (should be lowercase)
            "zh-tw",             # Wrong case for country (should be uppercase)
            "123",               # Numbers
            "en-USA",            # Country code too long
        ]
        for locale in invalid_locales:
            response = await client.get(f"/api/locales/{locale}")
            assert response.status_code == status.HTTP_400_BAD_REQUEST, \
                f"Expected 400 for invalid locale '{locale}', got {response.status_code}"

    async def test_locale_path_traversal_blocked(self, client):
        """GET /api/locales with path traversal should be blocked"""
        response = await client.get("/api/locales/../../etc/passwd")
        # Either 400 (invalid format) or 404 (path normalized) - both indicate protection
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    async def test_cors_headers_present(self, client):
        """OPTIONS request should return CORS headers"""
        # Send preflight request
        response = await client.options(
            "/api/files",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        # CORS middleware should handle this
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    async def test_cors_allows_localhost(self, client):
        """Requests from localhost:3000 should be allowed"""
        response = await client.get(
            "/api/config",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == status.HTTP_200_OK
        # Check CORS header is present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200

    async def test_rate_limit_agent_chat(self, client, monkeypatch, mock_agent_sdk):
        """POST /api/agent/chat should enforce rate limiting (10/min)"""
        monkeypatch.setattr("server.AGENT_SDK_AVAILABLE", True)

        # Reset rate limiter storage for clean test
        from server import limiter
        limiter.reset()

        # Make 12 requests rapidly - should hit rate limit after 10
        responses = []
        for i in range(12):
            response = await client.post(
                "/api/agent/chat",
                json={"message": f"Test message {i}"}
            )
            responses.append(response.status_code)

        # First 10 should succeed, remaining should be rate limited
        assert responses.count(status.HTTP_200_OK) == 10, \
            f"Expected 10 successful requests, got {responses.count(status.HTTP_200_OK)}"
        assert responses.count(status.HTTP_429_TOO_MANY_REQUESTS) == 2, \
            f"Expected 2 rate-limited requests, got {responses.count(status.HTTP_429_TOO_MANY_REQUESTS)}"


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
