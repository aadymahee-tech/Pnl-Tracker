import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        # Start browser with human-like settings
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("Step 1: Connecting to Tradetron...")
            page.goto("https://tradetron.tech/login", wait_until="domcontentloaded", timeout=60000)
            
            # Type credentials like a human
            print("Step 2: Entering credentials...")
            page.fill("input[name='email']", os.environ.get("TT_EMAIL"))
            time.sleep(1)
            page.fill("input[name='password']", os.environ.get("TT_PASSWORD"))
            time.sleep(1)
            
            # Click and wait for ANY dashboard indicator
            page.click("button[type='submit']")
            print("Step 3: Waiting for Dashboard (be patient)...")
            
            # We wait for either the dashboard link OR the "Deployed" menu item
            page.wait_for_selector("a[href*='deployed-strategies'], .dashboard-wrapper", timeout=60000)
            print("Step 4: Login Successful! Loading strategies...")

            # Go directly to the data page
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle", timeout=60000)
            time.sleep(5) # Allow dynamic numbers to load

            # The Intelligent Extraction
            strategies = page.evaluate("""() => {
                let results = [];
                const items = document.querySelectorAll('tr, .strategy-card, .deployment-card');
                items.forEach(item => {
                    let text = item.innerText;
                    if (text.includes('by ') && (text.includes('₹') || text.includes('Rs.'))) {
                        let name = text.split('\\n')[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        let pnl = 0.0;
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)\\s*([Lk]?)/gi);
                        if (pnlMatches) {
                            let val = pnlMatches[pnlMatches.length - 1].replace(/[₹Rs\\.\\s,]/gi, '');
                            pnl = parseFloat(val) || 0.0;
                            if (text.toUpperCase().includes('K')) pnl *= 1000;
                            if (text.toUpperCase().includes('L')) pnl *= 100000;
                            if (text.includes('-')) pnl *= -1;
                        }
                        results.push({ name, pnl });
                    }
                });
                return results;
            }""")

            print(f"Step 5: Captured {len(strategies)} strategies.")
            
            # Save the pure data
            output = {
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "strategies": strategies
            }
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)
            print("Step 6: Data saved to data.json")

        except Exception as e:
            print(f"FATAL ERROR: {str(e)}")
            # Log what the page looked like to help us debug
            print(f"Current URL: {page.url}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
