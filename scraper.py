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
            print("TASK: Secure Login...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=5000)
                time.sleep(12)
            except: pass
            page.click("button[type='submit']", force=True)
            page.wait_for_url("**/dashboard*", timeout=30000)

            # --- TASK: NAVIGATE TO DEPLOYED ---
            print("TASK: Teleporting to Deployed Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="load")
            time.sleep(5)

            # --- TASK: SELECT 'SELF' CREATOR (Ensuring only your strategies show) ---
            print("TASK: Filtering for 'Self' strategies...")
            try:
                # We click the Creator filter and select 'Self'
                page.get_by_label("Creator").select_option(label="Self")
                time.sleep(3)
            except: print("Note: Self filter selection skipped.")

            # --- TASK: ENFORCE LITE MODE ---
            print("TASK: Enforcing Lite Mode...")
            try:
                lite_btn = page.get_by_text("Switch to Lite")
                if lite_btn.is_visible(timeout=10000):
                    lite_btn.click()
                    time.sleep(5)
            except: pass

            page.screenshot(path="final_proof.png")

            # --- FINAL: PATTERN EXTRACTION ---
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

            print(f"SUCCESS: {len(strategies)} self-deployed strategies captured.")
            with open("data.json", "w") as f:
                json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)

        except Exception as e:
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
