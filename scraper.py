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
            print("Step 1: Navigating to Tradetron...")
            page.goto("https://tradetron.tech/login", timeout=60000)
            time.sleep(3)

            print("Step 2: Entering Credentials...")
            page.fill("input[name='email']", os.environ.get("TT_EMAIL").strip())
            page.fill("input[name='password']", os.environ.get("TT_PASSWORD").strip())
            
            # --- WORKING LOGIN HANDSHAKE ---
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=5000)
                print("Clicked Altcha. Waiting for math...")
                time.sleep(10) # Time for math to finish
            except: pass

            print("Clicking Sign In...")
            page.click("button[type='submit']", force=True)
            
            # Wait for dashboard using a simpler pattern
            page.wait_for_url("**/dashboard", timeout=45000)
            print(f"LOGIN SUCCESS! Landed on: {page.url}")

            # --- NAVIGATION TO DATA ---
            print("Step 3: Moving to Deployed Strategies...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle", timeout=60000)
            
            print("Waiting for strategy cards to appear...")
            # We wait for the 'by' keyword which always exists near the strategy name
            page.wait_for_selector("text='by'", timeout=30000)
            time.sleep(8) # Final buffer for P&L numbers to load/pulse

            # --- DATA CAPTURE ---
            print("Step 4: Scoping P&L values...")
            strategies = page.evaluate("""() => {
                let data = [];
                // Omni-Scraper logic: find any block with a name and a currency symbol
                document.querySelectorAll('div, tr, section').forEach(el => {
                    let txt = el.innerText;
                    if (txt.includes('by ') && (txt.includes('₹') || txt.includes('Rs.')) && txt.length < 500 && txt.length > 40) {
                        let lines = txt.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        
                        let pnlMatches = txt.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let val = pnlMatches[pnlMatches.length - 1].replace(/[₹Rs\\.\\s,]/gi, '');
                            let pnl = parseFloat(val) || 0.0;
                            if (txt.toUpperCase().includes('K')) pnl *= 1000;
                            if (txt.toUpperCase().includes('L')) pnl *= 100000;
                            // Check if the number was red/negative
                            if (pnlMatches[pnlMatches.length - 1].includes('-') || txt.includes('-₹') || txt.includes('-Rs')) {
                                if (pnl > 0) pnl *= -1;
                            }
                            data.push({ name, pnl });
                        }
                    }
                });
                // Unique by name to prevent double counting
                return [...new Map(data.map(i => [i.name, i])).values()];
            }""")

            print(f"Step 5: Captured {len(strategies)} strategies. Saving file...")
            
            with open("data.json", "w") as f:
                json.dump({
                    "last_updated": time.strftime("%H:%M:%S"),
                    "count": len(strategies),
                    "strategies": strategies
                }, f, indent=4)
            print("SUCCESS: data.json updated.")

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
