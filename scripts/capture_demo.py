#!/usr/bin/env python3
"""
Capture demo screenshots and GIF for README.

Usage:
    uv run python scripts/capture_demo.py
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def capture_demo():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2,  # Retina quality
        )
        page = context.new_page()

        # Navigate and wait for load
        page.goto("http://localhost:3000")
        page.wait_for_selector(".status.connected", timeout=10000)
        time.sleep(1)  # Let animations settle

        # Screenshot 1: Default minimalist view (just mindmap)
        page.screenshot(path=str(OUTPUT_DIR / "demo.png"))
        print(f"Saved: {OUTPUT_DIR / 'demo.png'}")

        # Screenshot 2: With sidebar open
        page.click("#btn-toggle-sidebar")
        time.sleep(0.5)
        page.screenshot(path=str(OUTPUT_DIR / "demo_with_sidebar.png"))
        print(f"Saved: {OUTPUT_DIR / 'demo_with_sidebar.png'}")

        # Screenshot 3: With editor open too
        page.click("#btn-toggle-editor")
        time.sleep(0.5)
        # Select a file - use the tree structure
        file_items = page.locator(".tree-item.file")
        if file_items.count() > 0:
            file_items.first.click()
            time.sleep(0.3)
        page.screenshot(path=str(OUTPUT_DIR / "demo_full.png"))
        print(f"Saved: {OUTPUT_DIR / 'demo_full.png'}")

        # Screenshot 4: Light theme
        page.click("#btn-theme-toggle")
        time.sleep(0.3)
        page.screenshot(path=str(OUTPUT_DIR / "demo_light.png"))
        print(f"Saved: {OUTPUT_DIR / 'demo_light.png'}")

        browser.close()

    print("\nDone! Screenshots saved to docs/images/")

if __name__ == "__main__":
    capture_demo()
