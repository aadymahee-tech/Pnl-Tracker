import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 1000})
        page = context.new_page()

        # MASTER DATA STORAGE
        captured_data = {"strategies": None}

        # THE STICKY SNIFFER: Listens to every single packet Tradetron sends
        def handle_response(response):
            # We look for the 'deployed-strategies' keyword in the network pipe
            if "deployed-strategies" in response.url and response.status == 200:
                try:
                    # We grab the raw JSON data live from the pipe
                    captured_data["strategies"] = response.json()
                    print(f"MASTER CATCH: Found data packet! Size: {len(str(captured_data['strategies']))} chars")
                except: pass

        # Activate the listener
        page.on("response", handle_response)

        try:
            print("Step 1: Logging in...")
            page.goto("https://tradetron.tech/login", timeout=60000)
            page.fill("input[name='email']", os.environ.get("TT_EMAIL").strip())
            page.fill("input[name='password']", os.environ.get("TT_PASSWORD").strip())
            
            # Step 2: Altcha Handshake
            try:
                page.click("altcha-widget", position={"x": 10, "y": 10})
                print("Clicked Altcha. Waiting for verification...")
                page.wait_for_function(
                    "() => { const el = document.querySelector('input[name=\"altcha\"]'); return el && el.value.length > 20; }",
                    timeout=30000
                )
                print("Verification Success!")
            except: pass

            # Step 3: Enter Dashboard
            page.click("button[type='submit']", force=True)
            page.wait_for_url("**/dashboard*", timeout=60000)
            print("LOGIN SUCCESSFUL!")

            # Step 4: Trigger the Data Packet
            print("Step 4: Navigating to Deployed Strategies...")
            # This navigation will trigger the internal API call that our Sniffer is listening for
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
            
            # Give the Sniffer 10 seconds to 'catch' the packet
            print("Waiting for data packet to settle...")
            time.sleep(10)

            # Step 5: Final Check & Save
            if captured_data["strategies"]:
                print(f"Step 5: MISSION SUCCESS! Saving {len(captured_data['strategies'].get('data', []))} strategies.")
                with open("data.json", "w") as f:
                    json.dump({
                        "last_updated": time.strftime("%H:%M:%S"),
                        "count": len(captured_data["strategies"].get('data', [])),
                        "strategies_raw": captured_data["strategies"]
                    }, f, indent=4)
            else:
                print("FAILED: Sniffer didn't catch the packet. Trying fallback scrape...")
                raise Exception("Data packet missing from pipe.")

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
