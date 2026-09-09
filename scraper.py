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
        # Using a resolution close to your recording
        context = browser.new_context(viewport={'width': 1280, 'height': 1000})
        page = context.new_page()

        try:
            # --- TASK A-C: LOGIN ---
            print("TASK A-C: Logging in...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=10000)
                page.wait_for_function("() => { const el = document.querySelector('input[name=\"altcha\"]'); return el && el.value.length > 20; }", timeout=30000)
            except: pass
            page.click("button[type='submit']", force=True)
            page.wait_for_url("**/dashboard*", timeout=30000)
            print("CHECK: Login success.")

            # --- TASK D: LAND ON DEPLOYED ---
            print("TASK D: Navigating to Deployed Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="load", timeout=60000)
            page.wait_for_selector("text='Filters'", timeout=30000)
            print("CHECK D: Arrived.")

            # --- TASK: APPLY 'SELF' FILTER (FROM YOUR RECORDING) ---
            print("TASK: Opening Filter Modal...")
            # Using the exact selector from your recording
            page.click("aria/ Filters") 
            time.sleep(2)
            
            print("TASK: Selecting 'Self' from dropdown...")
            # Using the exact ID found in your record.json
            page.select_option("#modalFilterSelect8", label="Self")
            time.sleep(1)
            
            print("TASK: Clicking the Filter submit button...")
            # Click the 'Filter' button inside the modal body
            page.locator("#deployedFilterModal button:has-text('Filter')").click()
            print("CHECK: 'Self' Filter Applied.")
            time.sleep(5)
            page.screenshot(path="after_filter.png")

            # --- TASK F: SWITCH TO LITE ---
            print("TASK F: Enforcing Lite Mode...")
            try:
                # We only click if we are NOT already in Lite Mode
                if not page.get_by_text("Switch to Pro").is_visible():
                    page.get_by_text("Switch to Lite").click(timeout=10000)
                    time.sleep(5)
                    print("CHECK F: Lite Mode activated.")
                else:
                    print("CHECK F: Already in Lite mode.")
            except: pass

            page.screenshot(path="final_proof.png")

            # --- FINAL: DATA EXTRACTION ---
            print("FINAL: Extracting patterned data...")
            strategies = page.evaluate("""() => {
                let results = [];
                document.querySelectorAll('tr').forEach(row => {
                    let text = row.innerText;
                    if (text.includes('(') && text.includes('₹')) {
                        let name = row.cells[0].innerText.split('(')[0].trim();
                        
                        // Extract Counter info
                        let cNo = 0; let cPnl = 0.0;
                        let match = text.match(/(\\d+)\\s*\\([₹Rs\\.\\s]*([+-]?[\\d,]+\\.?\\d*)\\)/);
                        if (match) {
                            cNo = parseInt(match[1]);
                            cPnl = parseFloat(match[2].replace(/,/g, ''));
                        }

                        // Extract Today Move (the very last column)
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        let tMove = 0.0;
                        if (pnlMatches) {
                            let lastVal = pnlMatches[pnlMatches.length - 1];
                            tMove = parseFloat(lastVal.replace(/[₹Rs\\.\\s,]/gi, '')) || 0.0;
                            if (lastVal.includes('-')) tMove *= -1;
                        }
                        results.push({ name, counterNo: cNo, counterPnl: cPnl, pnl: tMove });
                    }
                });
                return results;
            }""")

            print(f"SUCCESS: Captured {len(strategies)} strategies.")
            output = {
                "last_updated": time.strftime("%H:%M:%S"),
                "strategies": strategies
            }
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"FATAL ERROR: {str(e)}")
            page.screenshot(path="fatal_error.png")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
