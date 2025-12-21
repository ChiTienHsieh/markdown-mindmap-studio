"""
Playwright UI tests for Mindmap Editor

Run with:
    cd editor && uv run pytest tests/test_ui.py -v --headed

Or headless (faster, for CI):
    cd editor && uv run pytest tests/test_ui.py -v

Screenshots are saved to: editor/tests/screenshots/

UI Architecture (Minimalist Mode - Dec 2024):
- Sidebar, Editor, Agent panels are HIDDEN by default
- Floating toolbar at bottom center toggles panels
- Keyboard shortcuts: Cmd+1 (Files), Cmd+2 (Editor), Cmd+3 (Agent)
- Panels have smooth CSS animations when toggling
"""

import re
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

# Test configuration
BASE_URL = "http://localhost:3000"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"


@pytest.fixture(scope="module", autouse=True)
def setup_screenshots():
    """Create screenshots directory if it doesn't exist"""
    SCREENSHOT_DIR.mkdir(exist_ok=True)


@pytest.fixture
def page(page: Page):
    """Navigate to the app before each test"""
    # Clear localStorage to ensure clean state
    page.goto(BASE_URL)
    page.evaluate("localStorage.clear()")
    page.goto(f"{BASE_URL}?nocache={id(page)}")
    # Wait for WebSocket connection
    page.wait_for_selector(".status.connected", timeout=5000)
    return page


# ============== HELPER FUNCTIONS ==============

def open_sidebar(page: Page):
    """Open sidebar panel if it's collapsed"""
    sidebar = page.locator("#sidebar")
    if "collapsed" in (sidebar.get_attribute("class") or ""):
        page.click("#btn-toggle-sidebar")
        page.wait_for_timeout(400)  # Wait for animation


def open_editor(page: Page):
    """Open editor panel if it's collapsed"""
    editor_pane = page.locator("#editor-pane")
    if "collapsed" in (editor_pane.get_attribute("class") or ""):
        page.click("#btn-toggle-editor")
        page.wait_for_timeout(400)  # Wait for animation


def open_agent(page: Page):
    """Open agent panel if it's hidden"""
    agent_panel = page.locator("#agent-panel")
    if "hidden-panel" in (agent_panel.get_attribute("class") or ""):
        page.click("#btn-toggle-agent")
        page.wait_for_timeout(400)  # Wait for animation


class TestThemeToggle:
    """Tests for theme toggle functionality"""

    def test_default_is_dark_theme(self, page: Page):
        """App should start in dark theme by default"""
        # Check body does NOT have light-theme class
        body = page.locator("body")
        expect(body).not_to_have_class(re.compile(r"\blight-theme\b"))

        # Verify dark background color (updated for new design)
        bg_color = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
        assert bg_color == "rgb(9, 9, 11)", f"Expected dark bg, got {bg_color}"

        page.screenshot(path=SCREENSHOT_DIR / "01_dark_theme_default.png")

    def test_toggle_to_light_theme(self, page: Page):
        """Clicking theme toggle should switch to light theme"""
        # Click theme toggle button (in header)
        page.click("#btn-theme-toggle")

        # Check body has light-theme class
        body = page.locator("body")
        expect(body).to_have_class(re.compile(r"\blight-theme\b"))

        # Wait for CSS transition to complete (0.3s transition in CSS)
        page.wait_for_timeout(400)

        # Verify light background color
        bg_color = page.evaluate("window.getComputedStyle(document.body).backgroundColor")
        assert bg_color == "rgb(255, 255, 255)", f"Expected white bg, got {bg_color}"

        page.screenshot(path=SCREENSHOT_DIR / "02_light_theme.png")

    def test_toggle_back_to_dark_theme(self, page: Page):
        """Clicking again should switch back to dark theme"""
        body = page.locator("body")

        # Toggle to light first
        page.click("#btn-theme-toggle")
        expect(body).to_have_class(re.compile(r"\blight-theme\b"))

        # Toggle back to dark
        page.click("#btn-theme-toggle")
        expect(body).not_to_have_class(re.compile(r"\blight-theme\b"))

        page.screenshot(path=SCREENSHOT_DIR / "03_dark_theme_toggled_back.png")

    def test_theme_persists_after_reload(self, page: Page):
        """Theme preference should persist in localStorage"""
        body = page.locator("body")

        # Switch to light theme
        page.click("#btn-theme-toggle")
        expect(body).to_have_class(re.compile(r"\blight-theme\b"))

        # Reload page (without clearing localStorage)
        page.goto(f"{BASE_URL}?persist_test=1")
        page.wait_for_selector(".status.connected", timeout=5000)

        # Should still be light theme
        expect(page.locator("body")).to_have_class(re.compile(r"\blight-theme\b"))

        page.screenshot(path=SCREENSHOT_DIR / "04_theme_persisted.png")


# NOTE: Fullscreen button was removed in minimalist UI redesign (Dec 2024)
# The floating toolbar now has a Fit button instead
# Keeping this class as a placeholder for potential future fullscreen via keyboard


class TestFloatingToolbar:
    """Tests for floating toolbar and panel toggles"""

    def test_floating_toolbar_visible(self, page: Page):
        """Floating toolbar should be visible at bottom center"""
        toolbar = page.locator("#floating-toolbar")
        expect(toolbar).to_be_visible()

        # Check it's positioned at bottom
        position = page.evaluate(
            "window.getComputedStyle(document.getElementById('floating-toolbar')).position"
        )
        assert position == "fixed", f"Expected fixed position, got {position}"

        page.screenshot(path=SCREENSHOT_DIR / "05_floating_toolbar.png")

    def test_toolbar_has_all_buttons(self, page: Page):
        """Toolbar should have Files, Editor, Agent, Fit, Edit buttons"""
        expect(page.locator("#btn-toggle-sidebar")).to_be_visible()
        expect(page.locator("#btn-toggle-editor")).to_be_visible()
        expect(page.locator("#btn-toggle-agent")).to_be_visible()
        expect(page.locator("#btn-fit")).to_be_visible()
        # Edit mode is a label containing a hidden checkbox
        expect(page.locator(".edit-toggle")).to_be_visible()

    def test_toolbar_labels_appear_on_hover(self, page: Page):
        """Hovering toolbar should reveal button labels"""
        toolbar = page.locator("#floating-toolbar")
        files_label = page.locator("#btn-toggle-sidebar span")

        # Initially labels should have max-width 0 (hidden)
        initial_opacity = page.evaluate(
            "getComputedStyle(document.querySelector('#btn-toggle-sidebar span')).opacity"
        )
        assert float(initial_opacity) < 0.5, "Label should be hidden initially"

        # Hover over toolbar
        toolbar.hover()
        page.wait_for_timeout(400)

        # Labels should now be visible
        hover_opacity = page.evaluate(
            "getComputedStyle(document.querySelector('#btn-toggle-sidebar span')).opacity"
        )
        assert float(hover_opacity) > 0.5, "Label should be visible on hover"

        page.screenshot(path=SCREENSHOT_DIR / "06_toolbar_hovered.png")


class TestInitialState:
    """Tests for initial minimalist state (panels hidden by default)"""

    def test_sidebar_collapsed_by_default(self, page: Page):
        """Sidebar should be collapsed on initial load"""
        sidebar = page.locator("#sidebar")
        expect(sidebar).to_have_class(re.compile(r"\bcollapsed\b"))

    def test_editor_collapsed_by_default(self, page: Page):
        """Editor pane should be collapsed on initial load"""
        editor_pane = page.locator("#editor-pane")
        expect(editor_pane).to_have_class(re.compile(r"\bcollapsed\b"))

    def test_agent_hidden_by_default(self, page: Page):
        """Agent panel should be hidden on initial load"""
        agent_panel = page.locator("#agent-panel")
        expect(agent_panel).to_have_class(re.compile(r"\bhidden-panel\b"))

    def test_mindmap_visible_by_default(self, page: Page):
        """Mindmap pane should be visible (hero element)"""
        mindmap_pane = page.locator("#mindmap-pane")
        expect(mindmap_pane).to_be_visible()

        page.screenshot(path=SCREENSHOT_DIR / "07_initial_minimalist_state.png")


class TestPanelToggles:
    """Tests for panel toggle functionality"""

    def test_toggle_sidebar(self, page: Page):
        """Clicking sidebar toggle should show/hide sidebar"""
        sidebar = page.locator("#sidebar")
        btn = page.locator("#btn-toggle-sidebar")

        # Initially collapsed
        expect(sidebar).to_have_class(re.compile(r"\bcollapsed\b"))
        expect(btn).not_to_have_class(re.compile(r"\bactive\b"))

        # Click to open
        btn.click()
        page.wait_for_timeout(400)
        expect(sidebar).not_to_have_class(re.compile(r"\bcollapsed\b"))
        expect(btn).to_have_class(re.compile(r"\bactive\b"))

        # Click to close
        btn.click()
        page.wait_for_timeout(400)
        expect(sidebar).to_have_class(re.compile(r"\bcollapsed\b"))
        expect(btn).not_to_have_class(re.compile(r"\bactive\b"))

        page.screenshot(path=SCREENSHOT_DIR / "08_sidebar_toggle.png")

    def test_toggle_editor(self, page: Page):
        """Clicking editor toggle should show/hide editor"""
        editor_pane = page.locator("#editor-pane")
        btn = page.locator("#btn-toggle-editor")

        # Initially collapsed
        expect(editor_pane).to_have_class(re.compile(r"\bcollapsed\b"))

        # Click to open
        btn.click()
        page.wait_for_timeout(400)
        expect(editor_pane).not_to_have_class(re.compile(r"\bcollapsed\b"))
        expect(btn).to_have_class(re.compile(r"\bactive\b"))

        page.screenshot(path=SCREENSHOT_DIR / "09_editor_open.png")

    def test_toggle_agent(self, page: Page):
        """Clicking agent toggle should show/hide agent panel"""
        agent_panel = page.locator("#agent-panel")
        btn = page.locator("#btn-toggle-agent")

        # Initially hidden
        expect(agent_panel).to_have_class(re.compile(r"\bhidden-panel\b"))

        # Click to open
        btn.click()
        page.wait_for_timeout(400)
        expect(agent_panel).not_to_have_class(re.compile(r"\bhidden-panel\b"))
        expect(btn).to_have_class(re.compile(r"\bactive\b"))

        page.screenshot(path=SCREENSHOT_DIR / "10_agent_open.png")

    def test_resize_handle_hidden_when_editor_closed(self, page: Page):
        """Resize handle should be hidden when editor is collapsed"""
        resize_handle = page.locator("#resize-handle")
        editor_pane = page.locator("#editor-pane")

        # Initially editor is collapsed, resize handle should be hidden
        expect(editor_pane).to_have_class(re.compile(r"\bcollapsed\b"))
        expect(resize_handle).to_have_class(re.compile(r"\bhidden\b"))

        # Open editor
        page.click("#btn-toggle-editor")
        page.wait_for_timeout(400)

        # Resize handle should be visible
        expect(resize_handle).not_to_have_class(re.compile(r"\bhidden\b"))


class TestKeyboardShortcutsPanels:
    """Tests for keyboard shortcuts to toggle panels"""

    def test_cmd_1_toggles_sidebar(self, page: Page):
        """Cmd+1 should toggle sidebar"""
        sidebar = page.locator("#sidebar")

        # Initially collapsed
        expect(sidebar).to_have_class(re.compile(r"\bcollapsed\b"))

        # Press Cmd+1 to open
        page.keyboard.press("Meta+1")
        page.wait_for_timeout(400)
        expect(sidebar).not_to_have_class(re.compile(r"\bcollapsed\b"))

        # Press Cmd+1 to close
        page.keyboard.press("Meta+1")
        page.wait_for_timeout(400)
        expect(sidebar).to_have_class(re.compile(r"\bcollapsed\b"))

        page.screenshot(path=SCREENSHOT_DIR / "11_keyboard_cmd1.png")

    def test_cmd_2_toggles_editor(self, page: Page):
        """Cmd+2 should toggle editor"""
        editor_pane = page.locator("#editor-pane")

        # Initially collapsed
        expect(editor_pane).to_have_class(re.compile(r"\bcollapsed\b"))

        # Press Cmd+2 to open
        page.keyboard.press("Meta+2")
        page.wait_for_timeout(400)
        expect(editor_pane).not_to_have_class(re.compile(r"\bcollapsed\b"))

        # Press Cmd+2 to close
        page.keyboard.press("Meta+2")
        page.wait_for_timeout(400)
        expect(editor_pane).to_have_class(re.compile(r"\bcollapsed\b"))

    def test_cmd_3_toggles_agent(self, page: Page):
        """Cmd+3 should toggle agent panel"""
        agent_panel = page.locator("#agent-panel")

        # Initially hidden
        expect(agent_panel).to_have_class(re.compile(r"\bhidden-panel\b"))

        # Press Cmd+3 to open
        page.keyboard.press("Meta+3")
        page.wait_for_timeout(400)
        expect(agent_panel).not_to_have_class(re.compile(r"\bhidden-panel\b"))

        # Press Cmd+3 to close
        page.keyboard.press("Meta+3")
        page.wait_for_timeout(400)
        expect(agent_panel).to_have_class(re.compile(r"\bhidden-panel\b"))

        page.screenshot(path=SCREENSHOT_DIR / "12_keyboard_cmd3.png")


class TestFileOperations:
    """Tests for file sidebar and editor"""

    def test_file_list_loads(self, page: Page):
        """File list should populate from /api/files"""
        # Open sidebar first (collapsed by default in minimalist mode)
        open_sidebar(page)

        file_list = page.locator("#file-list")

        # Should have file items
        file_items = file_list.locator(".tree-file")
        expect(file_items.first).to_be_visible()

        # Should have folder nodes (tree structure)
        folder_nodes = file_list.locator(".tree-folder")
        expect(folder_nodes.first).to_be_visible()

        page.screenshot(path=SCREENSHOT_DIR / "13_file_list.png")

    def test_select_file(self, page: Page):
        """Clicking a file should load it in editor"""
        # Open sidebar and editor first
        open_sidebar(page)
        open_editor(page)

        # Click first file item (now shows parent dir name, not content.md)
        page.click(".tree-file")
        page.wait_for_timeout(500)

        # Editor should have content
        editor = page.locator("#markdown-editor")
        expect(editor).not_to_be_empty()

        # Current file label should update (still shows actual filename content.md)
        current_file = page.locator("#current-file")
        expect(current_file).to_contain_text("content.md")

        # File should be marked active
        active_item = page.locator(".tree-file.active")
        expect(active_item).to_be_visible()

        page.screenshot(path=SCREENSHOT_DIR / "14_file_selected.png")


class TestMindmap:
    """Tests for mindmap functionality"""

    def test_mindmap_renders(self, page: Page):
        """Mindmap should render with content"""
        # Wait for mindmap to have nodes
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Should have at least some nodes (root + modules)
        nodes = page.locator("#mindmap .markmap-node")
        count = nodes.count()
        assert count >= 3, f"Expected at least 3 nodes (root + modules), got {count}"

        page.screenshot(path=SCREENSHOT_DIR / "10_mindmap_rendered.png")

    def test_fit_to_view(self, page: Page):
        """Fit button should trigger markmap.fit()"""
        # Wait for mindmap to render
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Click fit button
        page.click("#btn-fit")

        # Give time for animation
        page.wait_for_timeout(500)

        page.screenshot(path=SCREENSHOT_DIR / "11_mindmap_fitted.png")


class TestIconsAndButtons:
    """Tests for icon visibility and button states"""

    def test_header_buttons_visible(self, page: Page):
        """Header should have theme toggle and refresh buttons"""
        expect(page.locator("#btn-theme-toggle")).to_be_visible()
        expect(page.locator("#btn-refresh")).to_be_visible()

        # Theme toggle should have SVG icon
        theme_svg = page.locator("#btn-theme-toggle svg")
        expect(theme_svg.first).to_be_visible()

    def test_floating_toolbar_buttons_visible(self, page: Page):
        """Floating toolbar should have toggle and fit buttons"""
        expect(page.locator("#btn-toggle-sidebar")).to_be_visible()
        expect(page.locator("#btn-toggle-editor")).to_be_visible()
        expect(page.locator("#btn-toggle-agent")).to_be_visible()
        expect(page.locator("#btn-fit")).to_be_visible()

        # Fit button should have SVG icon
        fit_svg = page.locator("#btn-fit svg")
        expect(fit_svg.first).to_be_visible()

    def test_icon_size(self, page: Page):
        """Icons should be properly sized"""
        btn = page.locator("#btn-theme-toggle")

        # Get computed dimensions
        width = page.evaluate(
            "window.getComputedStyle(document.getElementById('btn-theme-toggle')).width"
        )
        height = page.evaluate(
            "window.getComputedStyle(document.getElementById('btn-theme-toggle')).height"
        )

        # Button size should be reasonable (36px for new design)
        assert float(width.replace("px", "")) >= 32, f"Button too small: {width}"
        assert float(height.replace("px", "")) >= 32, f"Button too small: {height}"

    def test_theme_icon_changes_with_theme(self, page: Page):
        """Sun icon in dark mode, moon icon in light mode"""
        # In dark mode, sun should be visible
        sun = page.locator("#btn-theme-toggle .icon-sun")
        moon = page.locator("#btn-theme-toggle .icon-moon")

        expect(sun).to_be_visible()
        expect(moon).to_be_hidden()

        # Toggle to light mode
        page.click("#btn-theme-toggle")

        expect(sun).to_be_hidden()
        expect(moon).to_be_visible()


class TestResponsive:
    """Tests for responsive behavior"""

    def test_resize_handle_visible_when_editor_open(self, page: Page):
        """Resize handle should be visible when editor is open"""
        # Open editor first
        open_editor(page)

        handle = page.locator("#resize-handle")
        expect(handle).not_to_have_class(re.compile(r"\bhidden\b"))

        # Get initial editor width
        initial_width = page.evaluate(
            "document.querySelector('.editor-pane').offsetWidth"
        )
        assert initial_width > 0, "Editor should have width when open"

        page.screenshot(path=SCREENSHOT_DIR / "15_resize_handle.png")


class TestAgentChat:
    """Tests for Agent Chat panel functionality"""

    def test_agent_panel_hidden_by_default(self, page: Page):
        """Agent panel should be hidden by default in minimalist mode"""
        agent_panel = page.locator("#agent-panel")
        expect(agent_panel).to_have_class(re.compile(r"\bhidden-panel\b"))

        page.screenshot(path=SCREENSHOT_DIR / "16_agent_panel_hidden_default.png")

    def test_agent_panel_opens_via_toolbar(self, page: Page):
        """Agent panel should open when clicking toolbar button"""
        agent_panel = page.locator("#agent-panel")

        # Open via floating toolbar
        open_agent(page)

        # Panel should be visible
        expect(agent_panel).not_to_have_class(re.compile(r"\bhidden-panel\b"))

        # Header elements should be visible
        expect(page.locator("#agent-panel .agent-panel-header")).to_be_visible()
        expect(page.locator("#agent-status")).to_be_visible()

        page.screenshot(path=SCREENSHOT_DIR / "17_agent_panel_visible.png")

    def test_agent_status_indicator(self, page: Page):
        """Agent status should show Ready or Unavailable"""
        open_agent(page)

        agent_status = page.locator("#agent-status")

        # Wait for status to update from "Checking..."
        page.wait_for_timeout(1000)

        # Status should be either Ready or Unavailable (case-insensitive)
        status_text = agent_status.inner_text().upper()
        assert status_text in ["READY", "UNAVAILABLE"], (
            f"Expected 'Ready' or 'Unavailable', got '{status_text}'"
        )

        # Send button should always be visible (shows error when clicked if unavailable)
        send_btn = page.locator("#agent-send")
        expect(send_btn).to_be_visible()

        page.screenshot(path=SCREENSHOT_DIR / "18_agent_status.png")

    def test_agent_panel_collapse_expand(self, page: Page):
        """Agent panel internal toggle should collapse/expand body"""
        open_agent(page)

        agent_panel = page.locator("#agent-panel")
        toggle_btn = page.locator("#agent-toggle")

        # Initially the panel is visible (not hidden-panel), but may be collapsed internally
        # Click header toggle to expand/collapse
        toggle_btn.click()
        page.wait_for_timeout(300)

        # Toggle again
        toggle_btn.click()
        page.wait_for_timeout(300)

        page.screenshot(path=SCREENSHOT_DIR / "19_agent_panel_toggle.png")

    def test_agent_welcome_message(self, page: Page):
        """Agent panel should show welcome message by default"""
        open_agent(page)

        welcome_msg = page.locator(".agent-welcome")
        expect(welcome_msg).to_be_visible()

        # Check for welcome message content (locale-dependent, check for structure)
        expect(welcome_msg.locator("ul")).to_be_visible()

        page.screenshot(path=SCREENSHOT_DIR / "20_agent_welcome.png")

    def test_agent_input_elements(self, page: Page):
        """Input area should have textarea and send button"""
        open_agent(page)

        input_area = page.locator(".agent-input-area")
        expect(input_area).to_be_visible()

        # Textarea should be present
        agent_input = page.locator("#agent-input")
        expect(agent_input).to_be_visible()

        # Send button should be present
        send_btn = page.locator("#agent-send")
        expect(send_btn).to_be_visible()

        page.screenshot(path=SCREENSHOT_DIR / "21_agent_input_area.png")

    def test_agent_input_interaction(self, page: Page):
        """Typing in input should work normally"""
        open_agent(page)

        agent_input = page.locator("#agent-input")

        # Type some text
        test_message = "列出所有 FR"
        agent_input.fill(test_message)

        # Verify text is in input
        expect(agent_input).to_have_value(test_message)

        page.screenshot(path=SCREENSHOT_DIR / "22_agent_input_typed.png")

    def test_agent_panel_position(self, page: Page):
        """Agent panel should be positioned in bottom-right corner"""
        open_agent(page)

        agent_panel = page.locator("#agent-panel")

        # Check CSS position
        position = page.evaluate(
            "window.getComputedStyle(document.getElementById('agent-panel')).position"
        )
        assert position == "fixed", f"Expected fixed position, got {position}"

        # Bottom value should be above floating toolbar (around 80px)
        bottom = page.evaluate(
            "window.getComputedStyle(document.getElementById('agent-panel')).bottom"
        )
        bottom_val = float(bottom.replace("px", ""))
        assert bottom_val >= 50, f"Panel should be positioned above toolbar: {bottom}"

    def test_agent_panel_width(self, page: Page):
        """Agent panel should have reasonable width"""
        open_agent(page)

        width = page.evaluate(
            "document.getElementById('agent-panel').offsetWidth"
        )

        # Should be around 380px (check style.css for exact value)
        assert width >= 300, f"Panel too narrow: {width}px"
        assert width <= 500, f"Panel too wide: {width}px"


class TestEditorOperations:
    """Tests for editor editing and save functionality"""

    def test_save_button_disabled_initially(self, page: Page):
        """Save button should be disabled when no changes made"""
        # Open sidebar and editor first
        open_sidebar(page)
        open_editor(page)

        # Select a file first
        page.click(".tree-file")
        page.wait_for_timeout(500)

        # Save button should be disabled
        save_btn = page.locator("#btn-save")
        expect(save_btn).to_be_disabled()

    def test_save_button_enabled_after_edit(self, page: Page):
        """Save button should be enabled after editing content"""
        # Open sidebar and editor first
        open_sidebar(page)
        open_editor(page)

        # Select a file first
        page.click(".tree-file")
        page.wait_for_timeout(500)

        # Type in editor to trigger change
        editor = page.locator("#markdown-editor")
        editor.press("End")
        editor.type(" test change")

        # Save button should now be enabled
        save_btn = page.locator("#btn-save")
        expect(save_btn).not_to_be_disabled()

        page.screenshot(path=SCREENSHOT_DIR / "23_save_button_enabled.png")

    def test_editor_shows_file_content(self, page: Page):
        """Editor should display the selected file's content"""
        # Open sidebar and editor first
        open_sidebar(page)
        open_editor(page)

        # Click on a content.md file
        page.click(".tree-file")
        page.wait_for_timeout(500)

        # Editor should contain markdown content
        editor = page.locator("#markdown-editor")
        content = editor.input_value()

        # Should contain some content
        assert len(content) > 0, "Content should not be empty"

    def test_file_indicator_updates(self, page: Page):
        """Current file indicator should show selected filename"""
        # Open sidebar and editor first
        open_sidebar(page)
        open_editor(page)

        # Click on a file
        page.click(".tree-file")
        page.wait_for_timeout(500)

        # File indicator should show the filename
        indicator = page.locator("#current-file")
        expect(indicator).to_contain_text("content.md")


class TestApiTree:
    """Tests for /api/tree endpoint with new mindmap/ directory structure"""

    def test_api_tree_returns_valid_json(self, page: Page):
        """Test /api/tree returns valid JSON"""
        response = page.evaluate("""
            fetch('/api/tree')
                .then(r => r.json())
                .catch(e => ({ error: e.message }))
        """)
        assert "error" not in response, f"API returned error: {response.get('error')}"
        assert "title" in response, "Response missing 'title' field"
        assert "modules" in response, "Response missing 'modules' field"

    def test_api_tree_has_all_modules(self, page: Page, mindmap_structure):
        """Test response contains all modules from file system"""
        response = page.evaluate("fetch('/api/tree').then(r => r.json())")
        modules = response["modules"]

        # Verify module count matches file system
        fs_module_count = mindmap_structure["module_count"]
        assert len(modules) == fs_module_count, \
            f"Expected {fs_module_count} modules from FS, got {len(modules)} from API"

        # Verify module IDs match file system
        api_module_ids = {m["id"] for m in modules}
        fs_module_ids = mindmap_structure["module_ids"]
        assert api_module_ids == fs_module_ids, \
            f"Module ID mismatch: API={api_module_ids}, FS={fs_module_ids}"

    def test_api_tree_module_structure(self, page: Page):
        """Test each module has correct base structure"""
        response = page.evaluate("fetch('/api/tree').then(r => r.json())")
        modules = response["modules"]

        for module in modules:
            # Each module should have these basic fields
            assert "id" in module, f"Module missing 'id': {module}"
            assert "name" in module, f"Module missing 'name': {module}"
            assert "content" in module, f"Module missing 'content': {module}"


class TestMindmapStructure:
    """Tests for mindmap rendering with mindmap/ directory structure"""

    def test_mindmap_shows_all_modules(self, page: Page, mindmap_structure):
        """Mindmap should show all modules from file system"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Get modules from API to verify consistency (API uses display names)
        api_response = page.evaluate("fetch('/api/tree').then(r => r.json())")
        api_module_count = len(api_response["modules"])

        # Verify API module count matches file system
        fs_module_count = mindmap_structure["module_count"]
        assert api_module_count == fs_module_count, \
            f"API module count ({api_module_count}) != FS module count ({fs_module_count})"

        # Verify mindmap renders some text content
        mindmap_text = page.evaluate(
            "document.getElementById('mindmap').textContent"
        )
        assert len(mindmap_text) > 50, "Mindmap should contain substantial text content"

        page.screenshot(path=SCREENSHOT_DIR / "24_all_modules.png")

    def test_mindmap_shows_content(self, page: Page):
        """Mindmap should show content from markdown files"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Get text from mindmap SVG using JavaScript
        mindmap_text = page.evaluate(
            "document.getElementById('mindmap').textContent"
        )

        # Should have substantial content rendered
        assert len(mindmap_text) > 100, "Mindmap should have substantial text content"

    def test_mindmap_node_count(self, page: Page):
        """Mindmap should have significant number of nodes"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        nodes = page.locator("#mindmap .markmap-node")
        count = nodes.count()

        # Should have at least root + modules (minimum 4 nodes)
        assert count >= 4, f"Expected at least 4 nodes, got only {count}"

    def test_mindmap_renders_multiline_content(self, page: Page):
        """Mindmap should render multiline content correctly"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Check that content from content.md files appears
        mindmap_text = page.evaluate(
            "document.getElementById('mindmap').textContent"
        )

        # Should have substantial content (multiline text from various content.md)
        assert len(mindmap_text) > 200, "Mindmap should render content from markdown files"


class TestEditMode:
    """Tests for edit mode toggle functionality"""

    def test_edit_mode_checkbox_exists(self, page: Page):
        """Edit mode toggle label should exist (checkbox is hidden, styled)"""
        # The checkbox is hidden, we check for the parent label
        edit_toggle = page.locator(".edit-toggle")
        expect(edit_toggle).to_be_visible()

    def test_edit_mode_toggle(self, page: Page):
        """Clicking edit mode label should toggle edit mode"""
        # Click the parent label, not the hidden checkbox
        edit_toggle = page.locator(".edit-toggle")
        mindmap_pane = page.locator("#mindmap-pane")

        # Initially not in edit mode
        expect(mindmap_pane).not_to_have_class(re.compile(r"\bedit-mode\b"))

        # Enable edit mode by clicking the label
        edit_toggle.click()
        expect(mindmap_pane).to_have_class(re.compile(r"\bedit-mode\b"))

        # Disable edit mode
        edit_toggle.click()
        expect(mindmap_pane).not_to_have_class(re.compile(r"\bedit-mode\b"))

        page.screenshot(path=SCREENSHOT_DIR / "23_edit_mode_toggle.png")


class TestKeyboardShortcutsSave:
    """Tests for Ctrl+S save keyboard shortcut"""

    def test_ctrl_s_triggers_save(self, page: Page):
        """Ctrl+S should trigger save when file is dirty"""
        # Open sidebar and editor first
        open_sidebar(page)
        open_editor(page)

        # Select a file
        page.click(".tree-file")
        page.wait_for_timeout(500)

        # Make a change
        editor = page.locator("#markdown-editor")
        original_content = editor.input_value()
        editor.press("End")
        editor.type(" ")  # Small change

        # Save button should be enabled
        save_btn = page.locator("#btn-save")
        expect(save_btn).not_to_be_disabled()

        # Press Ctrl+S (this triggers save, button should become disabled)
        page.keyboard.press("Control+s")
        page.wait_for_timeout(1000)

        # After save, button should be disabled again
        expect(save_btn).to_be_disabled()


class TestMindmapToolbar:
    """Tests for mindmap toolbar controls"""

    def test_zoom_controls_visible(self, page: Page):
        """Zoom in/out controls should be visible"""
        page.wait_for_selector(".mm-toolbar", timeout=10000)

        toolbar = page.locator(".mm-toolbar")
        expect(toolbar).to_be_visible()

    def test_fit_button_works(self, page: Page):
        """Fit button should work without errors"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Click fit button
        page.click("#btn-fit")
        page.wait_for_timeout(500)

        # Should not cause any errors (check console)
        # The mindmap should still have nodes
        nodes = page.locator("#mindmap .markmap-node")
        count = nodes.count()
        assert count > 0, "Mindmap nodes disappeared after fit"


class TestEditModal:
    """Tests for edit modal functionality (click-to-edit mindmap nodes)"""

    def test_modal_initially_hidden(self, page: Page):
        """Edit modal should be hidden by default"""
        modal = page.locator("#edit-modal")
        expect(modal).to_have_class(re.compile(r"\bhidden\b"))

    def test_modal_opens_on_node_click_in_edit_mode(self, page: Page):
        """Clicking a mindmap node in edit mode should open modal"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Enable edit mode
        page.click(".edit-toggle")
        page.wait_for_timeout(300)

        # Click on a mindmap node (first FR item)
        node = page.locator("#mindmap .markmap-node").first
        node.click()
        page.wait_for_timeout(300)

        # Modal should be visible (hidden class removed)
        modal = page.locator("#edit-modal")
        expect(modal).not_to_have_class(re.compile(r"\bhidden\b"))

        page.screenshot(path=SCREENSHOT_DIR / "24_edit_modal_open.png")

    def test_modal_contains_node_text(self, page: Page):
        """Modal input should contain the clicked node's text"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Enable edit mode and click a node
        page.click(".edit-toggle")
        page.wait_for_timeout(300)

        # Get text from a specific node before clicking
        node = page.locator("#mindmap .markmap-node").first
        node.click()
        page.wait_for_timeout(300)

        # Modal input should have some text (node content)
        edit_input = page.locator("#edit-input")
        input_value = edit_input.input_value()
        assert len(input_value) > 0, "Edit input should contain node text"

    def test_cancel_button_closes_modal(self, page: Page):
        """Cancel button should close modal without saving"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Enable edit mode and open modal
        page.click(".edit-toggle")
        page.wait_for_timeout(300)
        page.locator("#mindmap .markmap-node").first.click()
        page.wait_for_timeout(300)

        # Modal should be open
        modal = page.locator("#edit-modal")
        expect(modal).not_to_have_class(re.compile(r"\bhidden\b"))

        # Click cancel
        page.click("#edit-cancel")
        page.wait_for_timeout(300)

        # Modal should be hidden again
        expect(modal).to_have_class(re.compile(r"\bhidden\b"))

        page.screenshot(path=SCREENSHOT_DIR / "25_edit_modal_cancelled.png")

    def test_click_outside_modal_closes_it(self, page: Page):
        """Clicking outside modal content should close modal"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Enable edit mode and open modal
        page.click(".edit-toggle")
        page.wait_for_timeout(300)
        page.locator("#mindmap .markmap-node").first.click()
        page.wait_for_timeout(300)

        # Modal should be open
        modal = page.locator("#edit-modal")
        expect(modal).not_to_have_class(re.compile(r"\bhidden\b"))

        # Click on the modal backdrop (outside .modal-content)
        # Use JavaScript to click on the modal element itself (not the content)
        page.evaluate("document.getElementById('edit-modal').click()")
        page.wait_for_timeout(300)

        # Modal should be hidden
        expect(modal).to_have_class(re.compile(r"\bhidden\b"))

    def test_modal_has_correct_elements(self, page: Page):
        """Modal should have title, input, cancel and save buttons"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Enable edit mode and open modal
        page.click(".edit-toggle")
        page.wait_for_timeout(300)
        page.locator("#mindmap .markmap-node").first.click()
        page.wait_for_timeout(300)

        # Check modal elements
        expect(page.locator("#edit-modal h3")).to_contain_text("Edit Node")
        expect(page.locator("#edit-input")).to_be_visible()
        expect(page.locator("#edit-cancel")).to_be_visible()
        expect(page.locator("#edit-save")).to_be_visible()

    def test_node_click_without_edit_mode_does_not_open_modal(self, page: Page):
        """Clicking node without edit mode should NOT open modal"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Make sure edit mode is OFF (don't click the toggle)
        mindmap_pane = page.locator("#mindmap-pane")
        expect(mindmap_pane).not_to_have_class(re.compile(r"\bedit-mode\b"))

        # Click on a mindmap node
        node = page.locator("#mindmap .markmap-node").first
        node.click()
        page.wait_for_timeout(300)

        # Modal should still be hidden
        modal = page.locator("#edit-modal")
        expect(modal).to_have_class(re.compile(r"\bhidden\b"))

    def test_save_button_closes_modal(self, page: Page):
        """Save button should close modal"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Enable edit mode and open modal
        page.click(".edit-toggle")
        page.wait_for_timeout(300)
        page.locator("#mindmap .markmap-node").first.click()
        page.wait_for_timeout(300)

        # Modal should be open
        modal = page.locator("#edit-modal")
        expect(modal).not_to_have_class(re.compile(r"\bhidden\b"))

        # Click save (don't modify content, just test that it closes)
        page.click("#edit-save")
        page.wait_for_timeout(500)

        # Modal should be hidden
        expect(modal).to_have_class(re.compile(r"\bhidden\b"))

        page.screenshot(path=SCREENSHOT_DIR / "26_edit_modal_saved.png")


class TestFileListDisplay:
    """Tests for file list display names (Bug fix: show parent dir instead of content.md)"""

    def test_file_list_shows_parent_dir_names(self, page: Page):
        """File list should show parent directory names, not 'content.md'"""
        # Open sidebar first
        open_sidebar(page)

        file_list = page.locator("#file-list")

        # Get all file item texts
        file_items = file_list.locator(".tree-file")
        count = file_items.count()
        assert count > 0, "No file items found"

        # Check that no file item shows "content.md"
        for i in range(count):
            item_text = file_items.nth(i).inner_text()
            assert "content.md" not in item_text, \
                f"File item should show parent dir, not 'content.md': {item_text}"

        page.screenshot(path=SCREENSHOT_DIR / "25_file_list_parent_dirs.png")

    def test_file_list_shows_meaningful_names(self, page: Page):
        """File list should show meaningful directory names in folder nodes"""
        # Open sidebar first
        open_sidebar(page)

        file_list = page.locator("#file-list")

        # Get text from all folder nodes
        folder_nodes = file_list.locator(".tree-folder")
        folder_count = folder_nodes.count()

        # Should have multiple folder nodes (modules and subdirectories)
        assert folder_count >= 3, f"Expected multiple folders, got {folder_count}"

        # Folder texts should be meaningful (not empty)
        folder_texts = [folder_nodes.nth(i).inner_text() for i in range(folder_count)]
        meaningful_folders = [t for t in folder_texts if len(t.strip()) > 0]

        assert len(meaningful_folders) >= 3, \
            f"Expected meaningful folder names, found: {folder_texts}"

    def test_file_list_shows_module_names(self, page: Page, mindmap_structure):
        """File list should show module directory names in folder nodes"""
        # Open sidebar first
        open_sidebar(page)

        file_list = page.locator("#file-list")

        # Wait for folder nodes to load
        page.wait_for_selector(".tree-folder", timeout=5000)

        folder_nodes = file_list.locator(".tree-folder")
        count = folder_nodes.count()
        folder_texts = [folder_nodes.nth(i).inner_text() for i in range(count)]

        # Should contain module names from file system (dynamically discovered)
        module_ids = mindmap_structure["module_ids"]
        found_modules = []
        for module_id in module_ids:
            if any(module_id in text for text in folder_texts):
                found_modules.append(module_id)

        assert len(found_modules) >= 2, \
            f"Expected to find module IDs from FS in {folder_texts}, found: {found_modules}"


class TestZoomPreservation:
    """Tests for zoom level preservation when folding nodes"""

    def test_zoom_preserved_after_fold(self, page: Page):
        """Zoom level should be preserved after clicking fold/toggle button"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Agent panel is hidden by default in minimalist mode, no need to collapse

        # Get initial zoom transform
        initial_transform = page.evaluate("""
            () => {
                const svg = document.getElementById('mindmap');
                const transform = d3.zoomTransform(svg);
                return { k: transform.k, x: transform.x, y: transform.y };
            }
        """)

        # Zoom in 3 times
        for _ in range(3):
            page.click(".mm-toolbar [title='Zoom in']")
            page.wait_for_timeout(200)

        # Get zoom after zooming in
        zoomed_transform = page.evaluate("""
            () => {
                const svg = document.getElementById('mindmap');
                const transform = d3.zoomTransform(svg);
                return { k: transform.k, x: transform.x, y: transform.y };
            }
        """)

        # Verify zoom changed
        assert zoomed_transform["k"] > initial_transform["k"], \
            "Zoom level should increase after zoom in"

        # Click toggle recursively (fold) button
        page.click(".mm-toolbar [title='Toggle recursively']")
        page.wait_for_timeout(1000)  # Wait for animation to complete

        # Get zoom after fold
        after_fold_transform = page.evaluate("""
            () => {
                const svg = document.getElementById('mindmap');
                const transform = d3.zoomTransform(svg);
                return { k: transform.k, x: transform.x, y: transform.y };
            }
        """)

        # Zoom level should be preserved (allow 5% tolerance for minor adjustments)
        zoom_diff = abs(after_fold_transform["k"] - zoomed_transform["k"])
        tolerance = zoomed_transform["k"] * 0.05  # 5% tolerance
        assert zoom_diff < tolerance, \
            f"Zoom level changed too much after fold: {zoomed_transform['k']} -> {after_fold_transform['k']} (diff: {zoom_diff}, tolerance: {tolerance})"

        page.screenshot(path=SCREENSHOT_DIR / "28_zoom_preserved_after_fold.png")

    def test_zoom_preserved_after_theme_toggle(self, page: Page):
        """Zoom level should be preserved after toggling theme"""
        page.wait_for_selector("#mindmap .markmap-node", timeout=10000)

        # Agent panel is hidden by default in minimalist mode, no need to collapse

        # Zoom in
        for _ in range(2):
            page.click(".mm-toolbar [title='Zoom in']")
            page.wait_for_timeout(200)

        # Get zoom before theme toggle
        before_transform = page.evaluate("""
            () => {
                const svg = document.getElementById('mindmap');
                const transform = d3.zoomTransform(svg);
                return { k: transform.k, x: transform.x, y: transform.y };
            }
        """)

        # Toggle theme
        page.click("#btn-theme-toggle")
        page.wait_for_timeout(1000)  # Wait for transition to complete

        # Get zoom after theme toggle
        after_transform = page.evaluate("""
            () => {
                const svg = document.getElementById('mindmap');
                const transform = d3.zoomTransform(svg);
                return { k: transform.k, x: transform.x, y: transform.y };
            }
        """)

        # Zoom level should be preserved (allow 5% tolerance)
        zoom_diff = abs(after_transform["k"] - before_transform["k"])
        tolerance = before_transform["k"] * 0.05  # 5% tolerance
        assert zoom_diff < tolerance, \
            f"Zoom changed too much after theme toggle: {before_transform['k']} -> {after_transform['k']} (diff: {zoom_diff}, tolerance: {tolerance})"

        page.screenshot(path=SCREENSHOT_DIR / "29_zoom_preserved_after_theme.png")


# Run a quick smoke test if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--headed", "-x"])
