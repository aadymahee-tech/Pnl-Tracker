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

        # SAFETY SHIELD: This sniffer will no longer crash the bot if it fails
        def safe_sniffer(res):
            try:
                if "deployed-strategies" in res.url and res.status == 200:
                    captured_data["strategies"] = res.json()
            except:
                pass # Ignore errors in the background

        page.on("response", safe_sniffer)

        try:
            print("Step 1: Loading Tradetron...")
            page.goto("https://tradetron.tech/login", wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)
            
            # Remove any blocking popups
            page.evaluate("document.querySelectorAll('.tt-app-promo__close, .close').forEach(e => e.click())")

            print("Step 2: Entering Credentials...")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            # SAVE PROOF: Take a screenshot immediately after filling
            page.screenshot(path="login_attempt.png")
            print("Action: Captured login_attempt.png")

            print("Step 3: Handling Verification...")
            page.click("altcha-widget", position={"x": 30, "y": 30})
            time.sleep(15) # Wait for math

            print("Step 4: Clicking Sign In...")
            page.click("button[type='submit']", force=True)
            
            print("Waiting for response...")
            time.sleep(15)
            
            # SAVE PROOF: Take a screenshot after the click
            page.screenshot(path="after_signin_click.png")
            print("Action: Captured after_signin_click.png")

            # Step 5: Final Navigation
            print("Step 5: Moving to Deployed Page...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="load", timeout=60000)
            time.sleep(10)
            page.screenshot(path="final_deployed_view.png")

            if captured_data["strategies"]:
                print("MISSION SUCCESS! Data packet caught.")
                output = {"last_updated": time.strftime("%H:%M:%S"), "strategies": captured_data["strategies"]}
            else:
                print("Packet missed. Saving whatever we found on screen.")
                output = {"error": "JSON packet missed", "url": page.url}

            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            # Even if we crash, try to take one final picture
            try: page.screenshot(path="fatal_error.png")
            except: pass
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
