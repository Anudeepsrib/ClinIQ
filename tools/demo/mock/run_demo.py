import time
from pathlib import Path

from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = Path(__file__).resolve().parents[3] / "frontend" / "public" / "assets"


def run_demo():
    print("🚀 Starting True Full-Stack Mock Data Demo...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--window-size=1440,900'])
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        
        try:
            print("1️⃣ Navigating to Local RAG Interface...")
            page.goto("http://localhost:3000", wait_until="networkidle")
            page.fill('input[autocomplete="username"]', "demo")
            page.fill('input[autocomplete="current-password"]', "demo")
            page.click("button >> text='Sign in'")
            page.wait_for_selector("textarea")
            page.screenshot(path=str(SCREENSHOT_DIR / "01_Initial_Interface.png"))
            print("   📸 Saved 01_Initial_Interface.png")
            
            print("2️⃣ Submitting vague medical query (API test)...")
            page.fill("textarea", "show me lab results")
            page.keyboard.press("Enter")
            
            time.sleep(2.0)
            page.screenshot(path=str(SCREENSHOT_DIR / "02_Clarification_Requested.png"))
            print("   📸 Saved 02_Clarification_Requested.png")
            
            print("3️⃣ Selecting a clarification option...")
            page.click("button >> text='PATTERSON'")
            
            time.sleep(2.5)
            page.screenshot(path=str(SCREENSHOT_DIR / "03_RBAC_Inline_Masking.png"))
            print("   📸 Saved 03_RBAC_Inline_Masking.png")
            
            print("4️⃣ Querying standard clinical protocol...")
            page.fill("textarea", "what is the heparin dosage?")
            page.keyboard.press("Enter")
            
            time.sleep(2.5)
            page.screenshot(path=str(SCREENSHOT_DIR / "04_Standard_Retrieval.png"))
            print("   📸 Saved 04_Standard_Retrieval.png")

            print("\n✅ True Full-Stack E2E Demo finished successfully!")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_demo()
