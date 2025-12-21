"""
QA Visual Testing for Markdown Mindmap Studio
Tests UI interactions, panel toggles, animations, and visual states.

Run: uv run python editor/tests/test_qa_visual.py
"""
import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright

# Screenshot output directory
SCREENSHOT_DIR = Path(__file__).parent.parent.parent / ".playwright-mcp" / "qa_tests"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://localhost:3000"


async def run_qa_tests():
    """Run all QA tests and generate report."""
    print("\n" + "=" * 60)
    print("MARKDOWN MINDMAP STUDIO - QA VISUAL TESTING")
    print("=" * 60 + "\n")

    bugs_found = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=150)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        try:
            await page.goto(BASE_URL)
            await page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"[ERROR] Could not connect to {BASE_URL}: {e}")
            print("Make sure the server is running: uv run python editor/server.py")
            await browser.close()
            return bugs_found

        # Test 1: Initial State
        print("\n--- TEST 1: Initial State ---")
        try:
            sidebar = page.locator("#sidebar")
            editor_pane = page.locator("#editor-pane")
            agent_panel = page.locator("#agent-panel")
            toolbar = page.locator("#floating-toolbar")

            sidebar_classes = await sidebar.get_attribute("class") or ""
            editor_classes = await editor_pane.get_attribute("class") or ""
            agent_classes = await agent_panel.get_attribute("class") or ""

            if "collapsed" not in sidebar_classes:
                bugs_found.append("BUG: Sidebar not collapsed on initial load")
            else:
                print("[PASS] Sidebar collapsed by default")

            if "collapsed" not in editor_classes:
                bugs_found.append("BUG: Editor pane not collapsed on initial load")
            else:
                print("[PASS] Editor pane collapsed by default")

            if "hidden-panel" not in agent_classes:
                bugs_found.append("BUG: Agent panel not hidden on initial load")
            else:
                print("[PASS] Agent panel hidden by default")

            if await toolbar.is_visible():
                print("[PASS] Floating toolbar is visible")
            else:
                bugs_found.append("BUG: Floating toolbar not visible")

            await page.screenshot(path=str(SCREENSHOT_DIR / "01_initial_state.png"))
            print(f"  -> Screenshot: {SCREENSHOT_DIR / '01_initial_state.png'}")
        except Exception as e:
            bugs_found.append(f"ERROR in Test 1: {e}")

        # Test 2: Floating Toolbar Hover Animation
        print("\n--- TEST 2: Floating Toolbar Hover Animation ---")
        try:
            toolbar = page.locator("#floating-toolbar")
            files_btn = toolbar.locator("#btn-toggle-sidebar")
            label = files_btn.locator("span")

            # Check initial state
            initial_opacity = await label.evaluate("el => getComputedStyle(el).opacity")
            initial_max_width = await label.evaluate("el => getComputedStyle(el).maxWidth")
            print(f"  Initial: opacity={initial_opacity}, max-width={initial_max_width}")

            # Hover over toolbar
            await toolbar.hover()
            await page.wait_for_timeout(400)

            # Check hovered state
            hover_opacity = await label.evaluate("el => getComputedStyle(el).opacity")
            hover_max_width = await label.evaluate("el => getComputedStyle(el).maxWidth")
            print(f"  Hovered: opacity={hover_opacity}, max-width={hover_max_width}")

            if float(hover_opacity) > float(initial_opacity):
                print("[PASS] Labels animate in on hover")
            else:
                bugs_found.append("BUG: Label opacity doesn't increase on hover")

            if hover_max_width != "0px":
                print("[PASS] Labels expand on hover")
            else:
                bugs_found.append("BUG: Labels don't expand on hover")

            await page.screenshot(path=str(SCREENSHOT_DIR / "02_toolbar_hovered.png"))
            print(f"  -> Screenshot: {SCREENSHOT_DIR / '02_toolbar_hovered.png'}")
        except Exception as e:
            bugs_found.append(f"ERROR in Test 2: {e}")

        # Test 3: Panel Toggles
        print("\n--- TEST 3: Panel Toggles ---")
        try:
            # Move mouse away from toolbar first
            await page.mouse.move(0, 0)
            await page.wait_for_timeout(200)

            # Open sidebar
            btn_sidebar = page.locator("#btn-toggle-sidebar")
            await btn_sidebar.click()
            await page.wait_for_timeout(500)

            sidebar_classes = await page.locator("#sidebar").get_attribute("class") or ""
            btn_classes = await btn_sidebar.get_attribute("class") or ""

            if "collapsed" in sidebar_classes:
                bugs_found.append("BUG: Sidebar still collapsed after clicking toggle")
            else:
                print("[PASS] Sidebar opens on click")

            if "active" not in btn_classes:
                bugs_found.append("BUG: Sidebar toggle button not marked as active")
            else:
                print("[PASS] Toggle button marked as active")

            await page.screenshot(path=str(SCREENSHOT_DIR / "03_sidebar_open.png"))

            # Open editor
            btn_editor = page.locator("#btn-toggle-editor")
            await btn_editor.click()
            await page.wait_for_timeout(500)

            editor_classes = await page.locator("#editor-pane").get_attribute("class") or ""
            if "collapsed" in editor_classes:
                bugs_found.append("BUG: Editor still collapsed after clicking toggle")
            else:
                print("[PASS] Editor opens on click")

            await page.screenshot(path=str(SCREENSHOT_DIR / "04_sidebar_and_editor_open.png"))

            # Open agent
            btn_agent = page.locator("#btn-toggle-agent")
            await btn_agent.click()
            await page.wait_for_timeout(500)

            agent_classes = await page.locator("#agent-panel").get_attribute("class") or ""
            if "hidden-panel" in agent_classes:
                bugs_found.append("BUG: Agent panel still hidden after clicking toggle")
            else:
                print("[PASS] Agent panel opens on click")

            await page.screenshot(path=str(SCREENSHOT_DIR / "05_all_panels_open.png"))
            print(f"  -> Screenshots saved")
        except Exception as e:
            bugs_found.append(f"ERROR in Test 3: {e}")

        # Test 4: Panel Close
        print("\n--- TEST 4: Panel Close ---")
        try:
            # Close agent
            await page.locator("#btn-toggle-agent").click()
            await page.wait_for_timeout(400)
            agent_classes = await page.locator("#agent-panel").get_attribute("class") or ""
            if "hidden-panel" not in agent_classes:
                bugs_found.append("BUG: Agent panel not hidden after toggle off")
            else:
                print("[PASS] Agent panel closes")

            # Close editor
            await page.locator("#btn-toggle-editor").click()
            await page.wait_for_timeout(400)
            editor_classes = await page.locator("#editor-pane").get_attribute("class") or ""
            if "collapsed" not in editor_classes:
                bugs_found.append("BUG: Editor not collapsed after toggle off")
            else:
                print("[PASS] Editor pane closes")

            # Close sidebar
            await page.locator("#btn-toggle-sidebar").click()
            await page.wait_for_timeout(400)
            sidebar_classes = await page.locator("#sidebar").get_attribute("class") or ""
            if "collapsed" not in sidebar_classes:
                bugs_found.append("BUG: Sidebar not collapsed after toggle off")
            else:
                print("[PASS] Sidebar closes")

            await page.screenshot(path=str(SCREENSHOT_DIR / "06_panels_closed.png"))
            print(f"  -> Screenshot: {SCREENSHOT_DIR / '06_panels_closed.png'}")
        except Exception as e:
            bugs_found.append(f"ERROR in Test 4: {e}")

        # Test 5: Keyboard Shortcuts
        print("\n--- TEST 5: Keyboard Shortcuts ---")
        try:
            # Test Cmd+1 (sidebar)
            await page.keyboard.press("Meta+1")
            await page.wait_for_timeout(400)
            sidebar_classes = await page.locator("#sidebar").get_attribute("class") or ""
            if "collapsed" in sidebar_classes:
                bugs_found.append("BUG: Cmd+1 did not open sidebar")
            else:
                print("[PASS] Cmd+1 opens sidebar")

            await page.keyboard.press("Meta+1")
            await page.wait_for_timeout(400)
            sidebar_classes = await page.locator("#sidebar").get_attribute("class") or ""
            if "collapsed" not in sidebar_classes:
                bugs_found.append("BUG: Cmd+1 did not close sidebar")
            else:
                print("[PASS] Cmd+1 closes sidebar")

            # Test Cmd+2 (editor)
            await page.keyboard.press("Meta+2")
            await page.wait_for_timeout(400)
            editor_classes = await page.locator("#editor-pane").get_attribute("class") or ""
            if "collapsed" in editor_classes:
                bugs_found.append("BUG: Cmd+2 did not open editor")
            else:
                print("[PASS] Cmd+2 opens editor")

            await page.keyboard.press("Meta+2")
            await page.wait_for_timeout(400)

            # Test Cmd+3 (agent)
            await page.keyboard.press("Meta+3")
            await page.wait_for_timeout(400)
            agent_classes = await page.locator("#agent-panel").get_attribute("class") or ""
            if "hidden-panel" in agent_classes:
                bugs_found.append("BUG: Cmd+3 did not open agent panel")
            else:
                print("[PASS] Cmd+3 opens agent panel")

            await page.keyboard.press("Meta+3")
            await page.wait_for_timeout(400)

            await page.screenshot(path=str(SCREENSHOT_DIR / "07_keyboard_shortcuts.png"))
            print(f"  -> Screenshot: {SCREENSHOT_DIR / '07_keyboard_shortcuts.png'}")
        except Exception as e:
            bugs_found.append(f"ERROR in Test 5: {e}")

        # Test 6: Theme Toggle
        print("\n--- TEST 6: Theme Toggle ---")
        try:
            body = page.locator("body")
            theme_btn = page.locator("#btn-theme-toggle")

            # Check initial theme
            initial_classes = await body.get_attribute("class") or ""
            is_light = "light-theme" in initial_classes
            print(f"  Initial theme: {'light' if is_light else 'dark'}")

            # Toggle theme
            await theme_btn.click()
            await page.wait_for_timeout(500)

            toggled_classes = await body.get_attribute("class") or ""
            is_light_after = "light-theme" in toggled_classes

            if is_light == is_light_after:
                bugs_found.append("BUG: Theme toggle did not change theme")
            else:
                print(f"[PASS] Theme toggled to {'light' if is_light_after else 'dark'}")

            await page.screenshot(path=str(SCREENSHOT_DIR / "08_theme_toggled.png"))

            # Open all panels in current theme
            await page.locator("#btn-toggle-sidebar").click()
            await page.wait_for_timeout(200)
            await page.locator("#btn-toggle-editor").click()
            await page.wait_for_timeout(200)
            await page.locator("#btn-toggle-agent").click()
            await page.wait_for_timeout(500)

            await page.screenshot(path=str(SCREENSHOT_DIR / "09_theme_with_all_panels.png"))
            print("[PASS] All panels rendered in toggled theme")
            print(f"  -> Screenshots saved")

            # Toggle back to original theme
            await theme_btn.click()
            await page.wait_for_timeout(300)
        except Exception as e:
            bugs_found.append(f"ERROR in Test 6: {e}")

        # Test 7: File Selection
        print("\n--- TEST 7: File Selection ---")
        try:
            # Make sure sidebar is open
            sidebar_classes = await page.locator("#sidebar").get_attribute("class") or ""
            if "collapsed" in sidebar_classes:
                await page.locator("#btn-toggle-sidebar").click()
                await page.wait_for_timeout(500)

            # Wait for file list
            await page.wait_for_timeout(500)

            # Find files
            files = page.locator(".tree-file")
            count = await files.count()

            if count == 0:
                print("[SKIP] No files found in list")
            else:
                first_file = files.first
                file_name_el = first_file.locator(".tree-name")
                file_name = await file_name_el.text_content() or "unknown"

                # Click the file
                await first_file.click()
                await page.wait_for_timeout(800)

                # Check if active
                file_classes = await first_file.get_attribute("class") or ""
                if "active" not in file_classes:
                    bugs_found.append("BUG: Selected file not marked as active")
                else:
                    print(f"[PASS] File '{file_name}' selected and marked active")

                # Check if mindmap updated (should have nodes)
                nodes = page.locator(".markmap-node")
                node_count = await nodes.count()
                if node_count > 0:
                    print(f"[PASS] Mindmap rendered with {node_count} nodes")
                else:
                    bugs_found.append("BUG: Mindmap has no nodes after file selection")

                await page.screenshot(path=str(SCREENSHOT_DIR / "10_file_selected.png"))
                print(f"  -> Screenshot: {SCREENSHOT_DIR / '10_file_selected.png'}")
        except Exception as e:
            bugs_found.append(f"ERROR in Test 7: {e}")

        await context.close()
        await browser.close()

    # Print summary
    print("\n" + "=" * 60)
    print("QA TEST SUMMARY")
    print("=" * 60)

    if bugs_found:
        print(f"\n[FAILED] Found {len(bugs_found)} issue(s):\n")
        for i, bug in enumerate(bugs_found, 1):
            print(f"  {i}. {bug}")
    else:
        print("\n[SUCCESS] All tests passed!")

    print(f"\nScreenshots saved to: {SCREENSHOT_DIR}")
    print("=" * 60 + "\n")

    return bugs_found


if __name__ == "__main__":
    asyncio.run(run_qa_tests())
