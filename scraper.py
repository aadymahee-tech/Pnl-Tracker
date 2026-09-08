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
            # --- EXACT working v2.2 LOGIN LOGIC ---
            print("Step 1: Navigating to Tradetron...")
            page.goto("https://tradetron.tech/login", timeout=60000)
            time.sleep(5)

            print("Step 2: Entering Credentials...")
            page.fill("input[name='email']", os.environ.get("TT_EMAIL").strip())
            page.fill("input[name='password']", os.environ.get("TT_PASSWORD").strip())
            
            print("Step 3: Handling ALTCHA (The Robot Check)...")
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}) 
                print("SUCCESS: Clicked the verification box.")
                print("Waiting for computer to finish math (Proof-of-Work)...")
                page.wait_for_function(
                    "() => document.querySelector('input[name=\"altcha\"]').value.length > 20",
                    timeout=30000
                )
                print("SUCCESS: Human verification verified!")
            except Exception as e:
                print(f"ALTCHA NOTE: {str(e)} (Proceeding anyway...)")

            print("Step 4: Clicking Sign In...")
            time.sleep(2)
            page.click("button[type='submit']", force=True)
            
            print("Step 5: Waiting for Dashboard...")
            # We wait for the dashboard URL or the 'Logout' button to confirm entry
            page.wait_for_selector("text='Logout'", timeout=45000)
            print(f"LOGIN SUCCESS! Landed on: {page.url}")

            # --- PLAYWRIGHT MASTER TAKES OVER HERE ---
            print("Step 6: Master Scraper Active - Intercepting Data Pipe...")
            
            # We tell Playwright to 'Sniff' the network for the strategies list
            # We wait for the internal API call 'deployed-strategies'
            with page.expect_response("**/api/deployed-strategies**", timeout=60000) as response_info:
                # This navigation triggers the background data packet
                page.goto("https://tradetron.tech/deployed-strategies")
                
                # Playwright catches the 100% accurate database file here!
                raw_data = response_info.value.json()
                print("Step 7: Master Catch Successful! Raw data captured.")

                # We save the data exactly as Tradetron sent it to your browser
                with open("data.json", "w") as f:
                    json.dump({
                        "last_updated": time.strftime("%H:%M:%S"),
                        "count": len(raw_data.get('data', [])),
                        "raw_tradetron_data": raw_data
                    }, f, indent=4)
                
            print("MISSION COMPLETE: Professional data saved to data.json")

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
