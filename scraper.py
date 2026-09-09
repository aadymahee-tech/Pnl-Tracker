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
            # --- TASK A, B, C: LOGIN ---
            print("TASK A-C: Logging in...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=5000)
                time.sleep(12)
            except: pass
            page.click("button[type='submit']", force=True)

            # --- TASK D: LAND ON DEPLOYED PAGE ---
            print("TASK D: Navigating to Deployed Strategies...")
            time.sleep(10)
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="load", timeout=60000)

            # --- TASK E: RESET FILTER ---
            print("TASK E: Resetting Filters...")
            try:
                page.locator(".fa-recycle, .fa-sync, .btn-danger").first.click(timeout=10000)
                time.sleep(5)
            except: pass

            # --- NEW TASK: FILTER BY 'SELF' (AS REQUESTED) ---
            print("TASK: Selecting 'SELF' from Creator list...")
            try:
                # 1. Click the Filters button to open the list
                page.get_by_role("button", name="Filters").click()
                time.sleep(2)
                # 2. Select 'Self' from the Creator dropdown
                page.locator("select[name='creator'], #creator_id").select_option(label="Self")
                # 3. Click the blue 'Filter' button to apply
                page.get_by_role("button", name="Filter").click()
                print("CHECK: 'Self' Filter Applied.")
                time.sleep(5)
            except Exception as filter_err:
                print(f"Note: Filter step encountered an issue: {filter_err}")

            # --- TASK F: SWITCH TO LITE ---
            print("TASK F: Enforcing Lite Mode...")
            try:
                lite_btn = page.get_by_text("Switch to Lite")
                if lite_btn.is_visible(timeout=10000):
                    lite_btn.click()
                    time.sleep(5)
            except: pass

            page.screenshot(path="final_proof.png")

            # --- FINAL: DATA EXTRACTION ---
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
