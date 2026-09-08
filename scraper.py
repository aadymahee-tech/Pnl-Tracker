import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("Step 1: Connecting...")
            page.goto("https://tradetron.tech/login", wait_until="networkidle", timeout=60000)
            
            # Close any blocking overlays
            try:
                if page.locator(".tt-app-promo__close").is_visible():
                    page.locator(".tt-app-promo__close").click(timeout=5000)
            except: pass

            print("Step 2: Entering Credentials...")
            page.fill("input[name='email']", os.environ.get("TT_EMAIL"))
            page.fill("input[name='password']", os.environ.get("TT_PASSWORD"))
            
            print("Step 3: Clicking Login...")
            page.click("button[type='submit']")
            
            # Wait for URL to change to dashboard (Simple & Reliable)
            print("Step 4: Waiting for Login success...")
            page.wait_for_url("**/dashboard", timeout=60000)
            print("Step 5: Login Success! Going to Deployed page...")

            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle", timeout=60000)
            time.sleep(10) # Heavy buffer for pulsing data

            strategies = page.evaluate("""() => {
                let results = [];
                const cards = document.querySelectorAll('tr, .strategy-card, .deployment-card');
                cards.forEach(c => {
                    let text = c.innerText;
                    if (text.includes('by ') && (text.includes('₹') || text.includes('Rs.'))) {
                        let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        let pnl = 0.0;
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let lastMatch = pnlMatches[pnlMatches.length - 1];
                            let val = lastMatch.replace(/[₹Rs\\.\\s,]/gi, '');
                            pnl = parseFloat(val) || 0.0;
                            if (text.toUpperCase().includes('K')) pnl *= 1000;
                            if (text.toUpperCase().includes('L')) pnl *= 100000;
                            if (lastMatch.includes('-')) pnl *= -1;
                        }
                        results.push({ name, pnl });
                    }
                });
                return results;
            }""")

            print(f"Step 6: Captured {len(strategies)} strategies.")
            output = {"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)
            print("DONE.")

        except Exception as e:
            print(f"FATAL ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
