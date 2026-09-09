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
        # Large window to ensure Lite cards load correctly
        context = browser.new_context(viewport={'width': 1600, 'height': 1200})
        page = context.new_page()

        try:
            print("Step 1: Logging in...")
            page.goto("https://tradetron.tech/login", wait_until="domcontentloaded", timeout=60000)
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20})
                time.sleep(12) 
            except: pass

            page.click("button[type='submit']")
            page.wait_for_selector("text='Logout', .dashboard-wrapper", timeout=60000)
            print("LOGIN SUCCESS!")
            page.screenshot(path="step1_dashboard.png")

            # Step 2: Navigate to Data
            print("Step 2: Loading Deployed Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="load", timeout=60000)
            time.sleep(5)
            page.screenshot(path="step2_deployed.png")
            
            # Reset Filters
            try: 
                print("Action: Resetting Filters...")
                page.locator(".fa-recycle, .fa-sync").first.click(timeout=5000)
                time.sleep(3)
            except: pass

            # Switch to Lite
            try:
                if "Switch to Lite" in page.content():
                    print("Action: Clicking Switch to Lite...")
                    page.get_by_text("Switch to Lite").click()
                    time.sleep(5)
                    page.screenshot(path="step3_lite.png")
            except: pass

            # Step 3: Capturing Data (Ultra-Aggressive)
            print("Step 3: Capturing Data...")
            strategies = page.evaluate("""() => {
                let results = [];
                // Look for every block that has 'by' and a currency symbol
                document.querySelectorAll('div, tr, section, .strategy-card').forEach(el => {
                    let t = el.innerText;
                    if (t.includes('by ') && (t.includes('₹') || t.includes('Rs.')) && t.length < 600 && t.length > 50) {
                        let lines = t.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        
                        let pnlMatches = t.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let lastMatch = pnlMatches[pnlMatches.length - 1];
                            let val = lastMatch.replace(/[₹Rs\\.\\s,]/gi, '');
                            let pnl = parseFloat(val) || 0.0;
                            if (lastMatch.includes('-')) pnl *= -1;
                            results.push({ name, pnl });
                        }
                    }
                });
                return [...new Map(results.map(i => [i.name, i])).values()];
            }""")

            if len(strategies) == 0:
                print("ZERO FOUND. Saving page HTML for analysis...")
                with open("page_debug.html", "w", encoding="utf-8") as f:
                    f.write(page.content())

            print(f"Step 4: Process Complete. Found {len(strategies)} strategies.")
            with open("data.json", "w") as f:
                json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)

        except Exception as e:
            print(f"SCRAPE FAILED: {str(e)}")
            page.screenshot(path="fatal_error.png")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
