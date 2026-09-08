import os
import json
import time
import random
from playwright.sync_api import sync_playwright

def run_scraper():
    email = os.environ.get("TT_EMAIL").strip()
    password = os.environ.get("TT_PASSWORD").strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        captured_data = {"strategies": None}

        # Background sniffer for the data packet
        page.on("response", lambda res: captured_data.update({"strategies": res.json()}) 
                if "deployed-strategies" in res.url and res.status == 200 else None)

        try:
            print("Step 1: Navigating to Tradetron...")
            page.goto("https://tradetron.tech/login", wait_until="load", timeout=60000)
            
            print("Step 2: Filling Credentials...")
            page.wait_for_selector("input[name='email']", timeout=20000)
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            # SAVE PROOF: Take a screenshot to show the boxes are filled
            page.screenshot(path="before_click.png")
            print("Screenshot saved: before_click.png")

            print("Step 3: Handling Verification...")
            try:
                # We click the widget and wait for the hidden field 'altcha'
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=10000)
                print("Clicked Altcha. Waiting for math to finish...")
                # Safe wait: we check if the element exists BEFORE reading 'value'
                page.wait_for_function(
                    "() => { const el = document.querySelector('input[name=\"altcha\"]'); return el && el.value.length > 10; }",
                    timeout=20000
                )
                print("Verified!")
            except:
                print("Altcha Error or Timeout. Attempting login anyway...")

            print("Step 4: Clicking Sign In...")
            page.click("button[type='submit']", force=True)
            
            # Wait for any sign of success (URL change or 'Logout' text)
            time.sleep(10)
            print(f"Post-Login URL: {page.url}")

            # Step 5: The "Walking" Logic
            print("Step 5: Forcing Deployed Page...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle", timeout=60000)
            
            # Scroll to ensure all 15 strategies are triggered
            print("Scrolling for data...")
            page.evaluate("window.scrollTo(0, 500)")
            time.sleep(5)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(3)

            if captured_data["strategies"]:
                strategies_list = captured_data["strategies"].get('data', [])
                print(f"MISSION SUCCESS! Captured {len(strategies_list)} strategies.")
                output = {"last_updated": time.strftime("%H:%M:%S"), "strategies": captured_data["strategies"]}
            else:
                print("Sniffer missed. Taking debug screenshot...")
                page.screenshot(path="debug.png")
                output = {"error": "Data not captured. Check debug.png", "url": page.url}

            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            page.screenshot(path="debug.png")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
