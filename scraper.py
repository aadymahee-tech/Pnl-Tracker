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
        context = browser.new_context(viewport={'width': 1400, 'height': 1200})
        page = context.new_page()

        try:
            print("Step 1: Secure Login...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20})
                time.sleep(12) 
            except: pass
            page.click("button[type='submit']")
            page.wait_for_url("**/dashboard*", timeout=60000)

            # Step 2: Set the Stage (Reset + Lite)
            print("Step 2: Preparing Deployed Layout...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
            
            # Reset Filters
            try: page.locator(".fa-recycle, .fa-sync").first.click(timeout=5000)
            except: pass

            # Force Switch to Lite
            try:
                if "Switch to Lite" in page.content():
                    page.get_by_text("Switch to Lite").click()
                    time.sleep(4)
            except: pass

            # Step 3: Precise Data Extraction
            print("Step 3: Extracting Lite-Card Patterns...")
            strategies = page.evaluate("""() => {
                let data = [];
                document.querySelectorAll('.strategy-card, .deployment-card, .deployed-strategy-block').forEach(card => {
                    let text = card.innerText;
                    let upper = text.toUpperCase();
                    
                    // FILTER: Only Live Auto
                    if (upper.includes('LIVE AUTO') && (text.includes('₹') || text.includes('Rs.'))) {
                        let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        
                        // Counter & Counter P&L: Pattern "Counter: 37 (₹ 545)"
                        let counterNo = 0;
                        let counterPnl = 0.0;
                        let counterMatch = text.match(/Counter:\\s*(\\d+)\\s*\\([₹Rs\\.\\s]*([+-]?[\\d,]+\\.?\\d*)\\)/i);
                        if (counterMatch) {
                            counterNo = parseInt(counterMatch[1]);
                            counterPnl = parseFloat(counterMatch[2].replace(/,/g, ''));
                        }

                        // Today's Move (Bottom Right Value)
                        let todayMove = 0.0;
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let lastMatch = pnlMatches[pnlMatches.length - 1];
                            todayMove = parseFloat(lastMatch.replace(/[₹Rs\\.\\s,]/gi, '')) || 0.0;
                            if (lastMatch.includes('-')) todayMove *= -1;
                        }

                        let status = text.includes('Live-Entered') ? 'Live-Entered' : 'Active';
                        
                        data.push({ name, todayMove, counterNo, counterPnl, status });
                    }
                });
                return data;
            }""")

            print(f"Step 4: Success! Found {len(strategies)} strategies.")
            with open("data.json", "w") as f:
                json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)

        except Exception as e:
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
