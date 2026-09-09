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
            time.sleep(10)
            print("Action: Teleporting to Deployed Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="load", timeout=60000)
            print("CHECK D: Arrived at Deployed Page.")

            # --- TASK E: CLICK FILTER RESET ---
            print("TASK E: Resetting Filters...")
            try:
                reset_btn = page.locator(".fa-recycle, .fa-sync, .btn-danger").first
                reset_btn.click(timeout=10000)
                time.sleep(5)
                print("CHECK E: Filters Reset.")
            except: 
                print("CHECK E: Reset button skipped.")

            # --- TASK F: CLICK SWITCH TO LITE ---
            print("TASK F: Enforcing Lite Mode Layout...")
            try:
                lite_btn = page.get_by_text("Switch to Lite")
                if lite_btn.is_visible(timeout=10000):
                    lite_btn.click()
                    time.sleep(5)
                    print("CHECK F: Switched to Lite Mode.")
                else:
                    print("CHECK F: Already in Lite mode.")
            except: 
                print("CHECK F: Lite Switch skipped.")

            # --- TAKE THE PROOF IMAGE ---
            print("Action: Capturing final proof image...")
            page.screenshot(path="final_proof.png")

            # --- FINAL TASK: EXTRACT DATA ---
            print("FINAL: Capturing Pattern-Based Data...")
            strategies = page.evaluate("""() => {
                let data = [];
                // Find all card-like structures on the page
                document.querySelectorAll('div, tr, section').forEach(el => {
                    let text = el.innerText;
                    // Pattern: Look for 'by' and 'Counter' which are unique to strategy cards
                    if (text.includes('by ') && text.includes('Counter:')) {
                        let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        
                        // Counter No & P&L Extraction
                        let cNo = 0;
                        let cPnl = 0.0;
                        let cMatch = text.match(/Counter:\\s*(\\d+)\\s*\\([₹Rs\\.\\s]*([+-]?[\\d,]+\\.?\\d*)\\)/i);
                        if (cMatch) {
                            cNo = parseInt(cMatch[1]);
                            cPnl = parseFloat(cMatch[2].replace(/,/g, ''));
                        }

                        // Today Move (Total P&L) Extraction
                        let tMove = 0.0;
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let lastVal = pnlMatches[pnlMatches.length - 1];
                            tMove = parseFloat(lastVal.replace(/[₹Rs\\.\\s,]/gi, '')) || 0.0;
                            if (lastVal.includes('-')) tMove *= -1;
                        }

                        // Use push (JavaScript) instead of append (Python)
                        data.push({ name, counterNo: cNo, counterPnl: cPnl, pnl: tMove, status: "Active" });
                    }
                });
                // Return unique strategies by name
                return [...new Map(data.map(i => [i.name, i])).values()];
            }""")

            # SAVE
            print(f"BATTLE WON: {len(strategies)} strategies captured.")
            output = {
                "last_updated": time.strftime("%H:%M:%S"),
                "strategies": strategies
            }
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"BATTLE FAILED: {str(e)}")
            page.screenshot(path="final_proof.png")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
