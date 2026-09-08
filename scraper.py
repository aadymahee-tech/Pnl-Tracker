import os
import json
import time
import random
from playwright.sync_api import sync_playwright

def run_scraper():
    # SECRETS
    email = os.environ.get("TT_EMAIL").strip()
    password = os.environ.get("TT_PASSWORD").strip()

    with sync_playwright() as p:
        # 1. SLOW-MO: Add a 500ms delay between every single command
        browser = p.chromium.launch(headless=True, slow_mo=500)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # MASTER DATA STORAGE
        captured_data = {"strategies": None}

        # THE STICKY SNIFFER (Background Listener)
        def handle_response(response):
            if "deployed-strategies" in response.url and response.status == 200:
                try:
                    captured_data["strategies"] = response.json()
                    print("HUMAN UPDATE: Caught the data packet from the network!")
                except: pass

        page.on("response", handle_response)

        try:
            print("Action: Navigating to Tradetron (Normal Speed)...")
            page.goto("https://tradetron.tech/login", wait_until="domcontentloaded", timeout=90000)
            
            # Step 2: HUMAN TYPING
            print("Action: Typing Email letter by letter...")
            # 'type' with 'delay' simulates a real person hitting keys
            page.type("input[name='email']", email, delay=random.randint(100, 200))
            
            time.sleep(1) # Pause to 'think'
            
            print("Action: Typing Password letter by letter...")
            page.type("input[name='password']", password, delay=random.randint(100, 200))
            
            # Step 3: HUMAN MOUSE MOVEMENT
            print("Action: Solving Altcha verification...")
            try:
                # Hover first, then click (like a real mouse)
                page.hover("altcha-widget")
                page.click("altcha-widget", position={"x": random.randint(15, 25), "y": random.randint(15, 25)})
                print("Action: Waiting for verification circle to turn green...")
                # We wait up to 20 seconds for the math to finish
                page.wait_for_function(
                    "() => { const el = document.querySelector('input[name=\"altcha\"]'); return el && el.value.length > 20; }",
                    timeout=30000
                )
            except: 
                print("Note: Altcha skipped or auto-solved.")

            # Step 4: HUMAN CLICK
            print("Action: Moving mouse to Sign In button...")
            page.hover("button[type='submit']")
            time.sleep(1)
            page.click("button[type='submit']")
            
            print("Action: Waiting for Dashboard to load...")
            page.wait_for_url("**/dashboard*", timeout=60000)
            print("LOGIN SUCCESSFUL!")

            # Step 5: NATURAL BROWSING
            print("Action: Moving to Deployed Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
            
            # SCROLLING: Mimic a human checking their list
            print("Action: Scrolling page to trigger data refresh...")
            page.mouse.wheel(0, 500) # Scroll down
            time.sleep(2)
            page.mouse.wheel(0, -500) # Scroll up
            time.sleep(5) # Let the pulsing numbers settle

            # Step 6: FINAL SAVE
            if captured_data["strategies"]:
                print(f"MISSION SUCCESS: Captured {len(captured_data['strategies'].get('data', []))} strategies.")
                output = {
                    "last_updated": time.strftime("%H:%M:%S"),
                    "strategies": captured_data["strategies"]
                }
            else:
                print("Action: Sniffer missed packet. Falling back to Screen-Read...")
                # Fallback if the network sniffer was blocked
                strategies = page.evaluate("() => { /* standard scrape logic here */ return []; }")
                output = {"error": "Network packet not caught", "url": page.url}

            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"HUMAN ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
