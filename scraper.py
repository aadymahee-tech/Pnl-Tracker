import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("Step 1: Logging in...")
            page.goto("https://tradetron.tech/login", timeout=60000)
            page.fill("input[name='email']", os.environ.get("TT_EMAIL").strip())
            page.fill("input[name='password']", os.environ.get("TT_PASSWORD").strip())
            
            # Handle Altcha Handshake
            try:
                page.click("altcha-widget", position={"x": 10, "y": 10})
                time.sleep(10) 
            except: pass

            page.click("button[type='submit']")
            page.wait_for_url("**/dashboard", timeout=45000)
            print("LOGIN SUCCESSFUL!")

            # --- PLAYWRIGHT MASTER ACTION: THE CATCH ---
            print("Step 2: Intercepting the raw data pipe...")
            
            # We tell Playwright to wait for the specific 'data' response from Tradetron's server
            with page.expect_response("**/api/deployed-strategies**", timeout=60000) as response_info:
                page.goto("https://tradetron.tech/deployed-strategies")
                
                # Playwright catches the raw JSON packet here!
                raw_data = response_info.value.json()
                
                print("Step 3: Raw data captured successfully!")
                
                # We simply save the data exactly as Tradetron sent it. 
                # No scraping, no errors, no 'Unnamed' strategies.
                with open("data.json", "w") as f:
                    json.dump({
                        "last_updated": time.strftime("%H:%M:%S"),
                        "raw_tradetron_data": raw_data
                    }, f, indent=4)
                
            print("MISSION COMPLETE: Clean data saved to data.json")

        except Exception as e:
            print(f"MASTER ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
