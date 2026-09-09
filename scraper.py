import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    email = os.environ.get("TT_EMAIL").strip()
    password = os.environ.get("TT_PASSWORD").strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Wide viewport to ensure 'Switch to Lite' is visible
        context = browser.new_context(viewport={'width': 1600, 'height': 1200})
        page = context.new_page()
        
        captured_data = []

        # The Network Sniffer (Tuned for v5.0)
        def handle_response(res):
            if "deployed-strategies" in res.url and res.status == 200:
                try:
                    data = res.json()
                    # Only accept real database dictionaries
                    if isinstance(data, dict) and "data" in data:
                        captured_data.append(data)
                except: pass

        page.on("response", handle_response)

        try:
            print("Step 1: Reliable Login...")
            # Use 'load' - proven to work for you
            page.goto("https://tradetron.tech/login", wait_until="load", timeout=60000)
            
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            # Working Altcha handshake
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=5000)
                time.sleep(12) 
            except: pass

            page.click("button[type='submit']", force=True)
            page.wait_for_url("**/dashboard*", timeout=45000)
            print("LOGIN SUCCESSFUL!")

            # Step 2: The Precise Pathway
            print("Step 2: Navigating to Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="load", timeout=60000)
            time.sleep(5)

            # A. Click Reset Filter
            print("Action: Clicking Filter Reset...")
            try:
                page.locator(".fa-recycle, .fa-sync").first.click(timeout=10000)
                time.sleep(5)
            except: print("Note: Reset button not found.")

            # B. Click Switch to Lite
            print("Action: Clicking Switch to Lite...")
            try:
                lite_btn = page.get_by_text("Switch to Lite")
                if lite_btn.is_visible():
                    lite_btn.click()
                    time.sleep(5)
            except: print("Note: Already in Lite mode or button missed.")

            # Step 3: Catch the Pulse
            print("Waiting for data packet (15s)...")
            time.sleep(15)

            final_list = []
            if captured_data:
                # Pick the freshest packet from the list
                raw = captured_data[-1]
                for item in raw.get('data', []):
                    # Filter for 'LIVE AUTO'
                    if item.get('deployment_type') == 'LIVE AUTO':
                        final_list.append({
                            "name": item.get('template', {}).get('name', 'Unnamed'),
                            "todayMove": item.get('all_pnl', 0.0),
                            "counterNo": item.get('run_counter', 0),
                            "counterPnl": item.get('last_pnl', 0.0),
                            "status": item.get('status', 'Active')
                        })
            
            # Fallback: If sniffer missed, read the screen
            if not final_list:
                print("Sniffer missed. Running fallback screen-read...")
                final_list = page.evaluate("""() => {
                    let results = [];
                    document.querySelectorAll('.strategy-card, .deployment-card').forEach(c => {
                        let t = c.innerText;
                        if (t.includes('by ') && (t.includes('₹') || t.includes('Rs.'))) {
                            let lines = t.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                            let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                            results.push({ name, todayMove: 0.0, counterNo: 0, counterPnl: 0.0, status: "Active" });
                        }
                    });
                    return results;
                }""")

            # Final Step: Write the JSON
            print(f"SUCCESS: {len(final_list)} strategies captured.")
            output = {
                "last_updated": time.strftime("%H:%M:%S"),
                "strategies": final_list
            }
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
