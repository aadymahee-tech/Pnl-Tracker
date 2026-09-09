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
            print("TASK A: Filling Credentials...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.wait_for_selector("input[name='email']", timeout=30000)
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)

            # --- TASK B: CONFIRM ALTCHA ---
            print("TASK B: Solving ALTCHA...")
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=10000)
                page.wait_for_function("() => { const el = document.querySelector('input[name=\"altcha\"]'); return el && el.value.length > 20; }", timeout=30000)
            except: pass

            # --- TASK C: CLICK LOGIN ---
            print("TASK C: Clicking Login...")
            page.click("button[type='submit']", force=True)

            # --- TASK D: THE FINAL DESTINATION (STATIC ADDRESS UPDATE) ---
            print("TASK D: Navigating to SELF DEPLOYED Strategies...")
            time.sleep(10)
            # CHANGED: Added '?creator=self' to ensure it only grabs your strategies
            page.goto("https://tradetron.tech/deployed-strategies?creator=self", wait_until="load", timeout=60000)
            print("CHECK D: Arrived at Self-Deployed page.")

            # --- TASK E: CLICK FILTER RESET ---
            print("TASK E: Resetting Filters...")
            try:
                page.locator(".fa-recycle, .fa-sync, .btn-danger").first.click(timeout=10000)
                time.sleep(5)
            except: pass

            # --- TASK F: CLICK SWITCH TO LITE ---
            print("TASK F: Enforcing Lite Mode...")
            try:
                lite_btn = page.get_by_text("Switch to Lite")
                if lite_btn.is_visible(timeout=10000):
                    lite_btn.click()
                    time.sleep(5)
            except: pass

            # --- FINAL: PATTERN EXTRACTION ---
            print("FINAL: Extracting Counter and P&L...")
            strategies = page.evaluate("""() => {
                let data = [];
                document.querySelectorAll('div, tr, section').forEach(el => {
                    let text = el.innerText;
                    if (text.includes('by ') && text.includes('Counter:')) {
                        let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        
                        let cNo = 0; let cPnl = 0.0;
                        let cMatch = text.match(/Counter:\\s*(\\d+)\\s*\\([₹Rs\\.\\s]*([+-]?[\\d,]+\\.?\\d*)\\)/i);
                        if (cMatch) {
                            cNo = parseInt(cMatch[1]);
                            cPnl = parseFloat(cMatch[2].replace(/,/g, ''));
                        }

                        let tMove = 0.0;
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let lastVal = pnlMatches[pnlMatches.length - 1];
                            tMove = parseFloat(lastVal.replace(/[₹Rs\\.\\s,]/gi, '')) || 0.0;
                            if (lastVal.includes('-')) tMove *= -1;
                        }
                        data.push({ name, counterNo: cNo, counterPnl: cPnl, pnl: tMove, status: "Active" });
                    }
                });
                return [...new Map(data.map(i => [i.name, i])).values()];
            }""")

            print(f"SUCCESS: {len(strategies)} strategies captured.")
            with open("data.json", "w") as f:
                json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)

        except Exception as e:
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
