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
        # Professional resolution to ensure all buttons are visible
        context = browser.new_context(viewport={'width': 1600, 'height': 1200})
        page = context.new_page()

        try:
            # --- TASK A: FILL LOGIN DETAILS ---
            print("TASK A: Navigating and Filling Credentials...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.wait_for_selector("input[name='email']", timeout=30000)
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            print("CHECK A: Credentials Filled.")

            # --- TASK B: CONFIRM ALTCHA ---
            print("TASK B: Solving ALTCHA Verification...")
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=10000)
                # We WAIT until the hidden 'altcha' solution appears
                page.wait_for_function(
                    "() => { const el = document.querySelector('input[name=\"altcha\"]'); return el && el.value.length > 20; }",
                    timeout=30000
                )
                print("CHECK B: Verification Confirmed.")
            except: 
                print("CHECK B: Altcha not found or auto-passed.")

            # --- TASK C: CLICK ON LOGIN ---
            print("TASK C: Clicking Login Button...")
            page.click("button[type='submit']", force=True)
            print("CHECK C: Login Clicked.")

            # --- TASK D: CHECK URL & FORCE NAVIGATE ---
            print("TASK D: Verifying Account Entry...")
            # We wait 10 seconds for the server to process
            time.sleep(10)
            # Force teleport to the static address as you requested
            print("Action: Teleporting to Deployed Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="load", timeout=60000)
            print("CHECK D: Arrived at Deployed Page.")

            # --- TASK E: CLICK FILTER RESET ---
            print("TASK E: Resetting Filters...")
            try:
                # Target the red recycle/reset icon specifically
                reset_btn = page.locator(".fa-recycle, .fa-sync, .btn-danger").first
                reset_btn.click(timeout=10000)
                time.sleep(5)
                print("CHECK E: Filters Reset.")
            except: 
                print("CHECK E: Reset button skipped (may already be clean).")

            # --- TASK F: CLICK SWITCH TO LITE ---
            print("TASK F: Enforcing Lite Mode Layout...")
            try:
                # We wait for the Lite button to appear in the summary block
                lite_btn = page.get_by_text("Switch to Lite")
                if lite_btn.is_visible(timeout=10000):
                    lite_btn.click()
                    time.sleep(5)
                    print("CHECK F: Switched to Lite Mode.")
                else:
                    print("CHECK F: Already in Lite mode.")
            except: 
                print("CHECK F: Lite Switch skipped.")

            # --- FINAL TASK: EXTRACT DATA FROM LITE MODE ---
            print("FINAL: Capturing Pattern-Based Data...")
            strategies = page.evaluate("""() => {
                let results = [];
                // Every strategy in Lite Mode lives in a specific block
                document.querySelectorAll('.strategy-card, .deployment-card, .deployed-strategy-block').forEach(card => {
                    let text = card.innerText;
                    // Only process real strategy cards
                    if (text.includes('by ') && (text.includes('₹') || text.includes('Rs.'))) {
                        let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        
                        // Precise extraction for Counter
                        let counterNo = 0;
                        let counterPnl = 0.0;
                        let counterMatch = text.match(/Counter:\\s*(\\d+)\\s*\\([₹Rs\\.\\s]*([+-]?[\\d,]+\\.?\\d*)\\)/i);
                        if (counterMatch) {
                            counterNo = parseInt(counterMatch[1]);
                            counterPnl = parseFloat(counterMatch[2].replace(/,/g, ''));
                        }

                        // Extract 'Today Move' from the 'Total' block at the bottom
                        let todayPnl = 0.0;
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let lastMatch = pnlMatches[pnlMatches.length - 1];
                            todayPnl = parseFloat(lastMatch.replace(/[₹Rs\\.\\s,]/gi, '')) || 0.0;
                            if (lastMatch.includes('-')) todayPnl *= -1;
                        }

                        let status = text.includes('Live-Entered') ? 'Live-Entered' : 'Active';
                        
                        results.append({ name, counterNo, counterPnl, todayPnl, status });
                    }
                });
                return results;
            }""")

            # SAVE
            print(f"BATTLE WON: {len(strategies)} strategies captured.")
            output = {
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "strategies": strategies
            }
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"BATTLE FAILED at Task: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
