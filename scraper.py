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

        # Listener for data packet
        page.on("response", lambda res: captured_data.update({"strategies": res.json()}) 
                if "deployed-strategies" in res.url and res.status == 200 else None)

        try:
            print("Step 1: Loading Page...")
            page.goto("https://tradetron.tech/login", wait_until="networkidle")
            
            print("Step 2: Force-Filling Credentials...")
            # We use 'fill' instead of 'type' - it's more reliable for empty fields
            page.wait_for_selector("input[name='email']")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            print("Step 3: Clicking Verification Checkbox...")
            # We click the specific checkbox area of the Altcha widget
            page.click("altcha-widget", position={"x": 25, "y": 25})
            
            print("Waiting for math to finish (15s)...")
            # We wait until the 'altcha' hidden input actually has the token
            page.wait_for_function(
                "() => document.querySelector('input[name=\"altcha\"]').value.length > 20",
                timeout=30000
            )
            print("Verified!")

            # Final check before clicking
            page.screenshot(path="before_click.png") # Check if fields are full now

            print("Step 4: Submitting...")
            # Forced click on the blue button
            page.click("button[type='submit']", force=True)
            
            print("Step 5: Moving to Data Page...")
            # We wait 10 seconds for the login to process, then JUMP to the data page
            time.sleep(10)
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
            
            # Scroll to trigger numbers
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(5)

            if captured_data["strategies"]:
                print(f"SUCCESS! Captured {len(captured_data['strategies'].get('data', []))} items.")
                output = {"last_updated": time.strftime("%H:%M:%S"), "strategies": captured_data["strategies"]}
            else:
                print("FAILED. Capturing debug image...")
                page.screenshot(path="debug.png")
                output = {"error": "No data captured. Check debug.png", "url": page.url}

            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"ERROR: {str(e)}")
            page.screenshot(path="debug.png")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
