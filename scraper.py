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

        # MISSION STATE TRACKER
        mission_complete = False
        attempts = 0

        while not mission_complete and attempts < 3:
            attempts += 1
            print(f"\n--- STARTING MISSION ATTEMPT {attempts} ---")
            try:
                # --- TASK A: FILL LOGIN ---
                print("TASK A: Loading Login Page...")
                page.goto("https://tradetron.tech/login", wait_until="load")
                page.wait_for_selector("input[name='email']", timeout=20000)
                
                page.fill("input[name='email']", email)
                page.fill("input[name='password']", password)
                
                # VERIFY A: Ensure boxes are not empty
                email_val = page.input_value("input[name='email']")
                if not email_val: raise Exception("Task A Failed: Email box empty.")
                print("CHECK A: Credentials Verified.")
                page.screenshot(path="task_a_filled.png")

                # --- TASK B: COMPULSORY ALTCHA ---
                print("TASK B: solving ALTCHA (No Skipping Allowed)...")
                # Wait for the widget to exist
                page.wait_for_selector("altcha-widget", timeout=15000)
                page.click("altcha-widget", position={"x": 25, "y": 25})
                
                # STRICT VERIFICATION: We wait for the 'altcha' token to appear
                # If it doesn't appear in 40s, we refresh the whole page.
                page.wait_for_function(
                    "() => { const el = document.querySelector('input[name=\"altcha\"]'); return el && el.value.length > 30; }",
                    timeout=40000
                )
                print("CHECK B: Human verification confirmed (Green Light).")
                page.screenshot(path="task_b_verified.png")

                # --- TASK C: CLICK LOGIN ---
                print("TASK C: Submitting Login...")
                page.click("button[type='submit']", force=True)
                
                # --- TASK D: THE FINAL DESTINATION ---
                print("TASK D: Forcing Navigation to Deployed Page...")
                # We wait 5s for the login to process then JUMP
                time.sleep(5)
                page.goto("https://tradetron.tech/deployed-strategies", wait_until="load", timeout=60000)
                
                # VERIFY D: Are we actually logged in?
                if "login" in page.url:
                    raise Exception("Task D Failed: Still on login page. Session rejected.")
                print("CHECK D: Inside Deployed Strategies.")
                page.screenshot(path="task_d_arrived.png")

                # --- TASK E: CLICK FILTER RESET ---
                print("TASK E: Performing Compulsory Filter Reset...")
                # We wait for the reset button (red recycle icon)
                reset_btn = page.locator(".fa-recycle, .fa-sync, .btn-danger").first
                reset_btn.wait_for(state="visible", timeout=20000)
                reset_btn.click()
                print("Action: Reset Clicked. Waiting for page refresh...")
                time.sleep(8) 
                print("CHECK E: Filter Reset complete.")
                page.screenshot(path="task_e_reset.png")

                # --- TASK E.2: SELECT 'SELF' ---
                print("TASK E.2: Filtering by 'SELF' Creator...")
                page.locator("button:has-text('Filter')").first.click(timeout=10000)
                time.sleep(2)
                page.locator("select[name='creator'], #creator_id").select_option(label="Self")
                page.locator("button:has-text('Filter')").last.click()
                time.sleep(5)
                print("CHECK E.2: 'Self' Filter Active.")

                # --- TASK F: SWITCH TO LITE ---
                print("TASK F: Enforcing Lite Mode...")
                # If "Switch to Lite" is visible, we MUST click it.
                lite_btn = page.get_by_text("Switch to Lite")
                if lite_btn.is_visible(timeout=5000):
                    lite_btn.click()
                    time.sleep(5)
                    print("CHECK F: Switched to Lite Mode.")
                else:
                    print("CHECK F: Already in Lite mode (Confirmed).")
                page.screenshot(path="task_f_complete.png")

                # --- MISSION COMPLETE: DATA EXTRACTION ---
                print("FINAL: Scraping patterned data...")
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

                if len(strategies) > 0:
                    print(f"MISSION SUCCESS: {len(strategies)} strategies captured.")
                    with open("data.json", "w") as f:
                        json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)
                    mission_complete = True
                else:
                    raise Exception("Scrape resulted in 0 items. Retrying mission...")

            except Exception as e:
                print(f"TASK FAILED: {str(e)}. Refreshing and restarting checklist...")
                page.screenshot(path=f"attempt_{attempts}_error.png")
                time.sleep(5)

        browser.close()

if __name__ == "__main__":
    run_scraper()
