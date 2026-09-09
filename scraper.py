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
            print("Step 1: Logging in...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            # Handle Altcha box
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20})
                time.sleep(12) 
            except: pass

            page.click("button[type='submit']")
            page.wait_for_url("**/dashboard*", timeout=60000)
            print("LOGIN SUCCESS!")

            # Step 2: Navigate and Setup Layout
            print("Step 2: Preparing Deployed Page...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
            
            # A. Click Reset Filter (The red button next to Filters)
            try:
                page.locator(".fa-recycle, .fa-sync").first.click(timeout=5000)
                print("Action: Filters Reset.")
            except: pass

            # B. Click Switch to Lite (In the blue summary box)
            try:
                if "Switch to Lite" in page.content():
                    page.get_by_text("Switch to Lite").click()
                    print("Action: Switched to Lite Mode.")
                    time.sleep(3)
            except: pass

            # Step 3: Extract Rich Data from Lite Cards
            print("Step 3: Extracting Lite-Card Data...")
            strategies = page.evaluate("""() => {
                let results = [];
                document.querySelectorAll('.strategy-card, .deployment-card, .deployed-strategy-block').forEach(card => {
                    let text = card.innerText;
                    if (text.includes('by ') && (text.includes('₹') || text.includes('Rs.'))) {
                        let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        
                        // Name & Identity
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        
                        // Extract Capital
                        let capMatch = text.match(/Capital:\\s*[₹Rs\\.]\\s?([\\d,]+\\.?\\d*)\\s*([Lk]?)/i);
                        let capital = 0;
                        if (capMatch) {
                            capital = parseFloat(capMatch[1].replace(/,/g, ''));
                            if (capMatch[2].toUpperCase() === 'L') capital *= 100000;
                            if (capMatch[2].toUpperCase() === 'K') capital *= 1000;
                        }

                        // Extract Multiplier
                        let multMatch = text.match(/Multiplier:\\s*(\\d+)x/i);
                        let multiplier = multMatch ? parseInt(multMatch[1]) : 1;

                        // Extract Status
                        let status = "Active";
                        if (text.includes('Live-Entered')) status = "Live-Entered";
                        else if (text.includes('Exited')) status = "Exited";
                        else if (text.includes('Error')) status = "Error";

                        // Extract Current P&L (Bottom Right green/red value)
                        let pnl = 0.0;
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let lastMatch = pnlMatches[pnlMatches.length - 1];
                            let val = lastMatch.replace(/[₹Rs\\.\\s,]/gi, '');
                            pnl = parseFloat(val) || 0.0;
                            if (lastMatch.includes('-')) pnl *= -1;
                        }

                        results.push({ name, pnl, capital, multiplier, status });
                    }
                });
                return results;
            }""")

            print(f"Step 4: Captured {len(strategies)} strategies.")
            with open("data.json", "w") as f:
                json.dump({
                    "last_updated": time.strftime("%H:%M:%S"),
                    "strategies": strategies
                }, f, indent=4)

        except Exception as e:
            print(f"ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
