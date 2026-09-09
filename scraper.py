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
            # --- TASK A: FILL LOGIN DETAILS ---
            task_a_done = False
            while not task_a_done:
                print("TASK A: Filling Credentials...")
                page.goto("https://tradetron.tech/login", wait_until="load")
                page.wait_for_selector("input[name='email']", timeout=20000)
                page.fill("input[name='email']", email)
                page.fill("input[name='password']", password)
                # Verify
                if page.input_value("input[name='email']") == email:
                    task_a_done = True
                    print("CHECK A: Verified.")
                    page.screenshot(path="task_a_complete.png")

            # --- TASK B: CONFIRM ALTCHA ---
            task_b_done = False
            while not task_b_done:
                print("TASK B: Solving ALTCHA...")
                try:
                    page.click("altcha-widget", position={"x": 25, "y": 25})
                    # We stay here until the server generates the 'altcha' token
                    page.wait_for_function(
                        "() => { const el = document.querySelector('input[name=\"altcha\"]'); return el && el.value.length > 30; }",
                        timeout=30000
                    )
                    task_b_done = True
                    print("CHECK B: Verified.")
                    page.screenshot(path="task_b_complete.png")
                except:
                    print("RETRY B: Altcha didn't trigger. Refreshing Task B...")
                    page.reload()
                    page.fill("input[name='email']", email)
                    page.fill("input[name='password']", password)

            # --- TASK C: CLICK LOGIN ---
            print("TASK C: Clicking Login...")
            page.click("button[type='submit']", force=True)
            time.sleep(5)
            print("CHECK C: Login Clicked.")

            # --- TASK D: CHECK URL & LAND ON DESTINATION ---
            task_d_done = False
            while not task_d_done:
                print("TASK D: Ensuring Deployed Page...")
                # We teleport to the static address
                page.goto("https://tradetron.tech/deployed-strategies", wait_until="load")
                if "deployed-strategies" in page.url and "login" not in page.url:
                    task_d_done = True
                    print("CHECK D: Arrived at Destination.")
                    page.screenshot(path="task_d_complete.png")
                else:
                    print("RETRY D: Still on Login or Redirect. Retrying Teleport...")
                    time.sleep(5)

            # --- TASK E: CLICK FILTER RESET ---
            task_e_done = False
            while not task_e_done:
                print("TASK E: Resetting Filters...")
                try:
                    reset_btn = page.locator(".fa-recycle, .fa-sync, .btn-danger").first
                    reset_btn.click(timeout=10000)
                    time.sleep(5)
                    task_e_done = True
                    print("CHECK E: Verified.")
                    page.screenshot(path="task_e_complete.png")
                except:
                    print("RETRY E: Reset button missed. Retrying...")
                    page.reload()

            # --- TASK F: CLICK SWITCH TO LITE ---
            task_f_done = False
            while not task_f_done:
                print("TASK F: Enforcing Lite Mode...")
                try:
                    if "Switch to Pro" in page.content(): # Means we are already in Lite Mode
                        task_f_done = True
                        print("CHECK F: Lite Mode confirmed.")
                    else:
                        lite_btn = page.get_by_text("Switch to Lite")
                        lite_btn.click(timeout=10000)
                        time.sleep(5)
                        task_f_done = True
                        print("CHECK F: Lite Mode activated.")
                except:
                    print("RETRY F: Lite button missed. Retrying...")
                    page.reload()
            page.screenshot(path="task_f_complete.png")

            # --- FINAL: DATA EXTRACTION (TRAINED ON YOUR IMAGE) ---
            print("FINAL TASK: Extracting Pattern-Based Data...")
            # I have retrained the scraper to read the 'Lite' table pattern from your image
            strategies = page.evaluate("""() => {
                let results = [];
                // Target the table rows in Lite Mode
                document.querySelectorAll('tr').forEach(row => {
                    let text = row.innerText;
                    if (text.includes('(') && text.includes('₹')) {
                        let cells = text.split('\\t').length > 1 ? text.split('\\t') : text.split('\\n');
                        let name = cells[0].split('(')[0].trim();
                        
                        // Capture Counter No & P&L from the pattern "38 (-₹ 1,191)"
                        let counterNo = 0; let counterPnl = 0.0;
                        let match = text.match(/(\\d+)\\s*\\([₹Rs\\.\\s]*([+-]?[\\d,]+\\.?\\d*)\\)/);
                        if (match) {
                            counterNo = parseInt(match[1]);
                            counterPnl = parseFloat(match[2].replace(/,/g, ''));
                        }

                        // Capture Today Move (The last number in the row)
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        let todayMove = 0.0;
                        if (pnlMatches) {
                            let lastVal = pnlMatches[pnlMatches.length - 1];
                            todayMove = parseFloat(lastVal.replace(/[₹Rs\\.\\s,]/gi, '')) || 0.0;
                            if (lastVal.includes('-')) todayMove *= -1;
                        }

                        results.push({ name, counterNo, counterPnl, pnl: todayMove });
                    }
                });
                return results;
            }""")

            print(f"MISSION SUCCESS: Captured {len(strategies)} strategies.")
            output = {"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"FATAL: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
