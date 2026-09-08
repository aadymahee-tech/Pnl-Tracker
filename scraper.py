import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 1000})
        page = context.new_page()

        try:
            # --- YOUR PROVEN LOGIN LOGIC ---
            print("Step 1: Navigating to Tradetron...")
            page.goto("https://tradetron.tech/login", timeout=60000)
            time.sleep(5)

            print("Step 2: Entering Credentials...")
            page.fill("input[name='email']", os.environ.get("TT_EMAIL").strip())
            page.fill("input[name='password']", os.environ.get("TT_PASSWORD").strip())
            
            print("Step 3: Handling ALTCHA...")
            try:
                # Use a safe click on the widget
                page.click("altcha-widget", position={"x": 20, "y": 20}) 
                print("SUCCESS: Clicked the verification box.")
                # Wait for the math to finish with a safer check
                page.wait_for_function(
                    "() => { const el = document.querySelector('input[name=\"altcha\"]'); return el && el.value.length > 20; }",
                    timeout=30000
                )
                print("SUCCESS: Human verification verified!")
            except Exception as e:
                print(f"ALTCHA NOTE: {str(e)} (Proceeding anyway...)")

            print("Step 4: Clicking Sign In...")
            time.sleep(2)
            page.click("button[type='submit']", force=True)
            
            # --- THE NAVIGATION FIX (Using URL detection instead of text) ---
            print("Step 5: Waiting for Dashboard...")
            # We wait for the URL to change to 'dashboard'. This is what worked in your 'Talking' logs.
            page.wait_for_url("**/dashboard*", timeout=60000)
            print(f"LOGIN SUCCESS! Landed on: {page.url}")

            # --- PLAYWRIGHT MASTER DATA CAPTURE ---
            print("Step 6: Sniffing the Data Pipe...")
            
            # We tell Playwright to 'Catch' the official data packet from Tradetron's server
            with page.expect_response("**/api/deployed-strategies**", timeout=60000) as response_info:
                # Go to the deployed page to trigger the data packet
                page.goto("https://tradetron.tech/deployed-strategies")
                
                # CATCH the JSON here
                raw_data = response_info.value.json()
                print("Step 7: Master Catch Successful! Data Captured.")

                # Save the official, accurate data
                with open("data.json", "w") as f:
                    json.dump({
                        "last_updated": time.strftime("%H:%M:%S"),
                        "count": len(raw_data.get('data', [])),
                        "strategies_raw": raw_data
                    }, f, indent=4)
                
            print("MISSION COMPLETE: Professional data saved to data.json")

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
