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
        
        # Buffer to catch live data packets
        captured_data = []

        def sniffer(res):
            # Listen for the official strategies data packet
            if "/api/deployed-strategies" in res.url and res.status == 200:
                try:
                    data = res.json()
                    # CRITICAL FIX: Only catch if it's a real data dictionary
                    if isinstance(data, dict):
                        captured_data.append(data)
                except: pass

        page.on("response", sniffer)

        try:
            print("Step 1: Logging in...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            # Altcha math wait
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=5000)
                time.sleep(12)
            except: pass
            
            page.click("button[type='submit']", force=True)
            page.wait_for_url("**/dashboard*", timeout=30000)
            print("LOGIN SUCCESS!")

            # Step 2: Navigate to Strategies
            print("Step 2: Preparing Deployed Page...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
            
            # --- YOUR CUSTOM PATHWAY ---
            try:
                print("Action: Resetting Filters...")
                page.locator(".fa-recycle, .fa-sync").first.click(timeout=5000)
                time.sleep(3)
            except: pass
            
            try:
                if "Switch to Lite" in page.content():
                    print("Action: Switching to Lite Mode...")
                    page.get_by_text("Switch to Lite").click()
                    time.sleep(5)
            except: pass

            # Step 3: Extract Data (Method A: Network Sniffer)
            final_strategies = []
            if captured_data:
                print("Step 3: Processing captured network packets...")
                for packet in reversed(captured_data):
                    data_block = packet.get("data", [])
                    if isinstance(data_block, list):
                        for item in data_block:
                            if item.get("deployment_type") == "LIVE AUTO":
                                final_strategies.append({
                                    "name": item.get('template', {}).get('name', 'Unnamed'),
                                    "todayMove": item.get('all_pnl', 0.0),
                                    "counterNo": item.get('run_counter', 0),
                                    "counterPnl": item.get('last_pnl', 0.0),
                                    "status": item.get('status', 'Active')
                                })
                        if final_strategies: break

            # Step 4: Method B (Visual Fallback) - Read the screen if sniffer failed
            if not final_strategies:
                print("Step 3 (Fallback): Network missed. Reading screen cards directly...")
                final_strategies = page.evaluate("""() => {
                    let results = [];
                    document.querySelectorAll('.strategy-card, .deployment-card, .deployed-strategy-block').forEach(card => {
                        let text = card.innerText;
                        if (text.includes('by ') && (text.includes('₹') || text.includes('Rs.'))) {
                            let name = text.split('\\n')[0].trim();
                            let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                            let pnl = 0.0;
                            if (pnlMatches) {
                                let val = pnlMatches[pnlMatches.length - 1].replace(/[₹Rs\\.\\s,]/gi, '');
                                pnl = parseFloat(val) || 0.0;
                                if (pnlMatches[pnlMatches.length - 1].includes('-')) pnl *= -1;
                            }
                            results.push({ name, todayMove: pnl, counterNo: 0, counterPnl: pnl, status: "Active" });
                        }
                    });
                    return results;
                }""")

            # Step 5: Final Save
            print(f"MISSION SUCCESS: {len(final_strategies)} strategies found.")
            output = {
                "last_updated": time.strftime("%H:%M:%S"),
                "strategies": final_strategies
            }
            
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"FATAL ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
