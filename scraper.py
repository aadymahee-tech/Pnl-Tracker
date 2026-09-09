import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    email = os.environ.get("TT_EMAIL").strip()
    password = os.environ.get("TT_PASSWORD").strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 1000})
        page = context.new_page()
        
        # We use a list to store all caught packets for analysis
        captured_packets = []

        # THE PRECISION SNIFFER: Targets the hidden API data
        def sniffer(res):
            # We specifically look for the 'api' endpoint
            if "/api/deployed-strategies" in res.url and res.status == 200:
                try:
                    data = res.json()
                    # Verify it's the correct data packet
                    if isinstance(data, dict) and "data" in data:
                        captured_packets.append(data)
                except: pass

        page.on("response", sniffer)

        try:
            print("Step 1: Secure Login...")
            page.goto("https://tradetron.tech/login", wait_until="domcontentloaded")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            try:
                page.click("altcha-widget", position={"x": 25, "y": 25}, timeout=5000)
                time.sleep(12) # Time for Altcha math
            except: pass
            
            page.click("button[type='submit']", force=True)
            page.wait_for_url("**/dashboard*", timeout=30000)
            print("LOGIN SUCCESS!")

            print("Step 2: Triggering Data Pulse...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="load")
            
            # Reset Filters to force the server to send the fresh packet
            print("Action: Resetting Filters and Switching to Lite...")
            try: page.locator(".fa-recycle, .fa-sync").first.click(timeout=5000)
            except: pass
            
            # Force Switch to Lite Mode (as per your request)
            try:
                if "Switch to Lite" in page.content():
                    page.get_by_text("Switch to Lite").click()
            except: pass

            print("Waiting for network pipe to fill (15s)...")
            time.sleep(15)

            # --- PROCESS DATA ---
            final_list = []
            if captured_packets:
                # Use the latest packet caught from the Deployed page
                raw = captured_packets[-1]
                for item in raw.get('data', []):
                    # Filter for 'LIVE AUTO' specifically
                    if item.get('deployment_type') == 'LIVE AUTO':
                        final_list.append({
                            "name": item.get('template', {}).get('name', 'Unnamed'),
                            "todayMove": item.get('all_pnl', 0.0),
                            "counterNo": item.get('run_counter', 0),
                            "counterPnl": item.get('last_pnl', 0.0),
                            "status": item.get('status', 'Active')
                        })
                
                # TERMINAL REPORT: Print names to console for you to see
                print(f"VERIFICATION: Found {len(final_list)} LIVE AUTO strategies.")
                for s in final_list:
                    print(f" - {s['name']}: Today={s['todayMove']} / Counter={s['counterPnl']}")
            
            else:
                print("FAILED: Sniffer missed the packet. Check debug.png.")
                page.screenshot(path="debug.png")

            # Final Save to GitHub
            output = {
                "last_updated": time.strftime("%H:%M:%S"),
                "count": len(final_list),
                "strategies": final_list
            }
            
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)
            print("Step 3: Professional data saved to data.json")

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
