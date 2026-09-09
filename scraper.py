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
        # Higher resolution to ensure all sidebars and buttons are reachable
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        try:
            # --- TASK A: FILL LOGIN DETAILS ---
            print("TASK A: Navigating and Filling Credentials...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.wait_for_selector("input[name='email']", timeout=30000)
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            page.screenshot(path="task_a_filled.png")
            print("CHECK A: Credentials Filled.")

            # --- TASK B: CONFIRM ALTCHA ---
            print("TASK B: Solving ALTCHA Verification...")
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=10000)
                page.wait_for_function(
                    "() => document.querySelector('input[name=\"altcha\"]').value.length > 20",
                    timeout=30000
                )
                print("CHECK B: Verification Confirmed.")
                page.screenshot(path="task_b_verified.png")
            except: 
                print("CHECK B: Altcha step skipped.")

            # --- TASK C: CLICK ON LOGIN ---
            print("TASK C: Clicking Login Button...")
            page.click("button[type='submit']", force=True)
            print("CHECK C: Login Clicked.")

            # --- TASK D: THE FINAL DESTINATION (STATIC ADRESS) ---
            print("TASK D: Navigating to SELF DEPLOYED Strategies...")
            time.sleep(10)
            # We go directly to the Self-Deployed filter URL as requested
            page.goto("https://tradetron.tech/deployed-strategies?creator=self", wait_until="load", timeout=60000)
            print("CHECK D: Arrived at Deployed Page.")
            page.screenshot(path="task_d_arrived.png")

            # --- TASK E: CLICK FILTER RESET ---
            print("TASK E: Resetting Filters...")
            try:
                # Targeted click on the red reset icon
                page.locator(".fa-recycle, .fa-sync, .btn-danger").first.click(timeout=10000)
                time.sleep(5)
                print("CHECK E: Filters Reset.")
                page.screenshot(path="task_e_reset.png")
            except: print("CHECK E: Reset button skipped.")

            # --- NEW TASK: SELECT 'SELF' FROM FILTERS ---
            print("TASK: Selecting 'SELF' from Filter Menu...")
            try:
                # Open Filter Menu (Using robust selector for both 'Filter' and 'Filters')
                page.locator("button:has-text('Filter')").first.click(timeout=10000)
                time.sleep(2)
                # Select 'Self'
                page.locator("select[name='creator'], #creator_id").select_option(label="Self")
                time.sleep(1)
                # Click the blue 'Filter' button to apply
                page.locator("button:has-text('Filter')").last.click()
                time.sleep(5)
                print("CHECK: 'Self' filter applied.")
                page.screenshot(path="task_filter_applied.png")
            except: print("Note: Filter step skipped.")

            # --- TASK F: CLICK SWITCH TO LITE ---
            print("TASK F: Enforcing Lite Mode Layout...")
            try:
                lite_btn = page.get_by_text("Switch to Lite")
                if lite_btn.is_visible(timeout=10000):
                    lite_btn.click()
                    time.sleep(5)
                    print("CHECK F: Switched to Lite Mode.")
                    page.screenshot(path="task_f_lite_mode.png")
            except: print("CHECK F: Already in Lite mode or button hidden.")

            # --- FINAL: DATA EXTRACTION (PATTERNS FROM IMAGES) ---
            print("FINAL: Scraping patterned data...")
            strategies = page.evaluate("""() => {
                let data = [];
                // In Lite Mode, strategies live in Table Rows (tr) or Card blocks
                document.querySelectorAll('tr, .strategy-card, .deployment-card').forEach(el => {
                    let text = el.innerText;
                    // Logic check for name and Counter pattern
                    if (text.includes('by ') && (text.includes('₹') || text.includes('Rs.'))) {
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

            # SAVE
            print(f"BATTLE WON: {len(strategies)} strategies captured.")
            output = {"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"FAILED AT TASK: {str(e)}")
            page.screenshot(path="task_failed.png")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
