import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    email = os.environ.get("TT_EMAIL").strip()
    password = os.environ.get("TT_PASSWORD").strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1600, 'height': 1200})
        page = context.new_page()
        
        # Buffer to catch live data packets
        captured_data = []

        # THE INTELLIGENT SNIFFER: Only catches real database dictionaries
        def handle_response(res):
            if "deployed-strategies" in res.url and res.status == 200:
                try:
                    data = res.json()
                    if isinstance(data, dict) and "data" in data:
                        captured_data.append(data)
                        print(f"PIPELINE: Caught data packet containing {len(data['data'])} items.")
                except: pass

        page.on("response", handle_response)

        try:
            print("Action: Navigating to Login...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            # Dynamic Altcha Handshake
            print("Action: Waiting for Verification math...")
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=5000)
                # We wait specifically for the 'altcha' hidden token to be generated
                page.wait_for_function("() => document.querySelector('input[name=\"altcha\"]').value.length > 20", timeout=30000)
                print("SUCCESS: Human verification complete.")
            except: print("Note: Verification step bypassed.")

            print("Action: Signing In...")
            page.click("button[type='submit']", force=True)
            
            # Wait for successful entry into the account
            page.wait_for_url("**/dashboard*", timeout=60000)
            print("LOGIN SUCCESSFUL!")

            # --- DYNAMIC NAVIGATION TO DATA ---
            print("Action: Moving to Deployed Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="load")

            # 1. Wait for Filter Reset (Red Button) to be visible
            print("Waiting for Filter Reset button...")
            reset_btn = page.locator(".fa-recycle, .fa-sync").first
            reset_btn.wait_for(state="visible", timeout=30000)
            reset_btn.click()
            print("SUCCESS: Filters Reset.")

            # 2. Wait for Switch to Lite to be visible
            print("Waiting for Lite Mode button...")
            lite_btn = page.get_by_text("Switch to Lite")
            if lite_btn.is_visible(timeout=10000):
                lite_btn.click()
                print("SUCCESS: Switched to Lite Mode.")

            # 3. Wait for the actual STRATEGIES to appear on screen
            print("Waiting for strategy cards to appear on screen...")
            page.wait_for_selector("text='by '", timeout=45000)
            
            # Final scroll to ensure the server sends the most recent pulse
            page.evaluate("window.scrollTo(0, 500)")
            
            # --- FINAL DATA ARRANGE ---
            final_list = []
            if captured_data:
                # Process only the freshest packet caught
                raw = captured_data[-1]
                for item in raw.get('data', []):
                    if item.get('deployment_type') == 'LIVE AUTO':
                        final_list.append({
                            "name": item.get('template', {}).get('name', 'Unnamed'),
                            "todayMove": item.get('all_pnl', 0.0),
                            "counterNo": item.get('run_counter', 0),
                            "counterPnl": item.get('last_pnl', 0.0),
                            "status": item.get('status', 'Active')
                        })
            
            # Save the result
            print(f"MISSION COMPLETE: Captured {len(final_list)} LIVE AUTO strategies.")
            output = {"last_updated": time.strftime("%H:%M:%S"), "strategies": final_list}
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"BATTLE ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
