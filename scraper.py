import os
import json
import time
import random
from playwright.sync_api import sync_playwright

def run_scraper():
    email = os.environ.get("TT_EMAIL").strip()
    password = os.environ.get("TT_PASSWORD").strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=500)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        captured_data = {"strategies": None}

        def handle_response(response):
            if "deployed-strategies" in response.url and response.status == 200:
                try: captured_data["strategies"] = response.json()
                except: pass

        page.on("response", handle_response)

        try:
            print("Step 1: Loading Login Page...")
            page.goto("https://tradetron.tech/login", wait_until="load", timeout=90000)
            
            print("Step 2: Typing Credentials...")
            page.type("input[name='email']", email, delay=random.randint(50, 150))
            page.type("input[name='password']", password, delay=random.randint(50, 150))
            
            print("Step 3: Solving Verification Box...")
            # We wait specifically for the Altcha text to ensure it's loaded
            page.wait_for_selector("altcha-widget", timeout=10000)
            page.click("altcha-widget") 
            
            print("Waiting 15 seconds for Math to complete...")
            time.sleep(15) 

            print("Step 4: Clicking Sign In...")
            page.click("button[type='submit']")
            
            # --- THE MAGIC TRICK ---
            # Instead of waiting for a redirect, we FORCE the browser to go to the data page
            print("Step 5: Forcing Navigation to Deployed Strategies...")
            time.sleep(5)
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle", timeout=60000)
            
            # SCROLL to wake up the data
            page.mouse.wheel(0, 1000)
            time.sleep(5)

            if captured_data["strategies"]:
                print(f"SUCCESS: Captured {len(captured_data['strategies'].get('data', []))} strategies.")
                output = {"last_updated": time.strftime("%H:%M:%S"), "strategies": captured_data["strategies"]}
            else:
                print("CAPTURE FAILED. Taking a debug screenshot...")
                page.screenshot(path="debug.png") # This will show us the problem!
                output = {"error": "No data captured. Check debug.png in repo.", "url": page.url}

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
