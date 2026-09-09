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
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        try:
            # --- TASK A & B & C: LOGIN GATE ---
            print("GATE 1: Login...")
            logged_in = False
            while not logged_in:
                page.goto("https://tradetron.tech/login", wait_until="load")
                page.fill("input[name='email']", email)
                page.fill("input[name='password']", password)
                try:
                    page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=10000)
                    page.wait_for_function("() => document.querySelector('input[name=\"altcha\"]').value.length > 20", timeout=20000)
                except: pass
                page.click("button[type='submit']", force=True)
                time.sleep(5)
                if "login" not in page.url or page.get_by_text("Logout").is_visible():
                    logged_in = True
            print("CHECK: Login Complete.")
            page.screenshot(path="task_c_login.png")

            # --- TASK D: DESTINATION GATE ---
            print("GATE 2: Destination...")
            arrived = False
            while not arrived:
                page.goto("https://tradetron.tech/deployed-strategies", wait_until="load")
                # Confirm arrival by seeing the Filter button from your recording
                if page.get_by_text("Filters").first.is_visible(timeout=10000):
                    arrived = True
            print("CHECK: Arrived at Deployed Page.")
            page.screenshot(path="task_d_arrived.png")

            # --- TASK E: RESET FILTER ---
            print("GATE 3: Reset Filters...")
            reset_done = False
            while not reset_done:
                try:
                    page.locator(".fa-recycle, .fa-sync").first.click(timeout=10000)
                    time.sleep(5)
                    reset_done = True
                except: page.reload()
            print("CHECK: Filters Reset.")
            page.screenshot(path="task_e_reset.png")

            # --- TASK F: APPLY 'SELF' FILTER (FIXED SELECTOR) ---
            print("GATE 4: Applying 'Self' Filter...")
            filter_applied = False
            while not filter_applied:
                try:
                    # We use the text-based selector to avoid the icon token error
                    page.get_by_text("Filters").first.click(timeout=10000)
                    time.sleep(2)
                    # Use the specific ID from your record.json
                    page.select_option("#modalFilterSelect8", label="Self")
                    # Click the 'Filter' button inside the modal
                    page.locator("#deployedFilterModal button:has-text('Filter')").click()
                    time.sleep(5)
                    filter_applied = True
                except: 
                    print("RETRY: Filter Modal missed. Refreshing Gate...")
                    page.reload()
            print("CHECK: 'Self' Filter Applied.")
            page.screenshot(path="task_filter_applied.png")

            # --- TASK G: SWITCH TO LITE ---
            print("GATE 5: Lite Mode...")
            lite_mode = False
            while not lite_mode:
                if "Switch to Pro" in page.content(): # Already in Lite
                    lite_mode = True
                else:
                    try:
                        page.get_by_text("Switch to Lite").click(timeout=10000)
                        time.sleep(5)
                        lite_mode = True
                    except: page.reload()
            print("CHECK: Lite Mode On.")
            page.screenshot(path="task_g_lite.png")

            # --- FINAL: DATA CAPTURE ---
            print("FINAL: Scraping Data...")
            strategies = page.evaluate("""() => {
                let data = [];
                document.querySelectorAll('tr').forEach(row => {
                    let text = row.innerText;
                    if (text.includes('(') && text.includes('₹')) {
                        let name = row.cells[0].innerText.split('(')[0].trim();
                        let cNo = 0; let cPnl = 0.0;
                        let match = text.match(/(\\d+)\\s*\\([₹Rs\\.\\s]*([+-]?[\\d,]+\\.?\\d*)\\)/);
                        if (match) {
                            cNo = parseInt(match[1]);
                            cPnl = parseFloat(match[2].replace(/,/g, ''));
                        }
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        let tMove = 0.0;
                        if (pnlMatches) {
                            let lastVal = pnlMatches[pnlMatches.length - 1];
                            tMove = parseFloat(lastVal.replace(/[₹Rs\\.\\s,]/gi, '')) || 0.0;
                            if (lastVal.includes('-')) tMove *= -1;
                        }
                        data.push({ name, counterNo: cNo, counterPnl: cPnl, pnl: tMove });
                    }
                });
                return data;
            }""")

            print(f"BATTLE WON: Captured {len(strategies)} strategies.")
            with open("data.json", "w") as f:
                json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)

        except Exception as e:
            print(f"FATAL ERROR: {str(e)}")
            page.screenshot(path="fatal_error.png")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
