import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 1000})
        page = context.new_page()

        try:
            print("Step 1: Logging in...")
            page.goto("https://tradetron.tech/login", timeout=60000)
            page.fill("input[name='email']", os.environ.get("TT_EMAIL").strip())
            page.fill("input[name='password']", os.environ.get("TT_PASSWORD").strip())
            
            # Wait for Altcha click
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=5000)
                time.sleep(10) # Wait for math to finish
            except: pass

            page.click("button[type='submit']")
            page.wait_for_url("**/dashboard**", timeout=45000)
            print("LOGIN SUCCESSFUL!")

            # Step 2: GO TO THE DATA PAGE
            print("Step 2: Navigating to Deployed Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle", timeout=60000)
            
            # Wait for any strategy card to appear
            print("Waiting for strategies to load...")
            page.wait_for_selector("text='by '", timeout=30000)
            time.sleep(5) # Final buffer for P&L updates

            # Step 3: Extract Data
            strategies = page.evaluate("""() => {
                let data = [];
                // Scans the page for any block that looks like a strategy
                document.querySelectorAll('div, tr, section').forEach(el => {
                    let txt = el.innerText;
                    if (txt.includes('by ') && (txt.includes('₹') || txt.includes('Rs.')) && txt.length < 500 && txt.length > 50) {
                        let lines = txt.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        let pnl = 0.0;
                        let matches = txt.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (matches) {
                            let val = matches[matches.length - 1].replace(/[₹Rs\\.\\s,]/gi, '');
                            pnl = parseFloat(val) || 0.0;
                            if (txt.toUpperCase().includes('K')) pnl *= 1000;
                            if (txt.toUpperCase().includes('L')) pnl *= 100000;
                            if (matches[matches.length - 1].includes('-')) pnl *= -1;
                        }
                        data.push({ name, pnl });
                    }
                });
                // Remove duplicates by name
                return [...new Map(data.map(i => [i.name, i])).values()];
            }""")

            print(f"Step 3: Captured {len(strategies)} strategies.")
            
            with open("data.json", "w") as f:
                json.dump({
                    "last_updated": time.strftime("%H:%M:%S"),
                    "count": len(strategies),
                    "strategies": strategies
                }, f, indent=4)
            print("DATA SAVED TO data.json")

        except Exception as e:
            print(f"ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
