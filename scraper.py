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
        context = browser.new_context(viewport={'width': 1280, 'height': 1000})
        page = context.new_page()
        captured_data = {"strategies": None}

        page.on("response", lambda res: captured_data.update({"strategies": res.json()}) 
                if "deployed-strategies" in res.url and res.status == 200 else None)

        try:
            print("Step 1: Loading Login Page...")
            page.goto("https://tradetron.tech/login", wait_until="load", timeout=60000)
            
            # Remove blocking promos
            page.evaluate("document.querySelectorAll('.tt-app-promo__close, .close').forEach(e => e.click())")

            print("Step 2: Filling Credentials...")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            print("Step 3: Clicking Verification...")
            # Click exactly in the Altcha checkbox area
            page.click("altcha-widget", position={"x": 30, "y": 30})
            print("Waiting 15s for verification...")
            time.sleep(15)

            # --- CAPTURE PRE-LOGIN STATE ---
            page.screenshot(path="login_attempt.png")
            print("Screenshot saved: login_attempt.png")

            print("Step 4: Clicking Sign In...")
            page.click("button[type='submit']", force=True)
            
            # Wait for transition
            print("Waiting for dashboard redirect...")
            time.sleep(15)
            
            # --- CAPTURE POST-LOGIN STATE ---
            page.screenshot(path="after_signin_click.png")
            print("Screenshot saved: after_signin_click.png")

            print(f"Current URL: {page.url}")

            # Step 5: Force Deployed Page
            print("Step 5: Moving to Deployed Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle", timeout=60000)
            time.sleep(10)
            page.screenshot(path="final_deployed_view.png")

            if captured_data["strategies"]:
                print(f"SUCCESS! Captured {len(captured_data['strategies'].get('data', []))} strategies.")
                output = {"last_updated": time.strftime("%H:%M:%S"), "strategies": captured_data["strategies"]}
            else:
                print("No data packet caught. Check final_deployed_view.png")
                output = {"error": "No data found", "url": page.url}

            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            page.screenshot(path="fatal_error.png")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
