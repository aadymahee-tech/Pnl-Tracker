import os
import json
import time
from playwright.sync_api import sync_playwright

# SECRETS (These will come from GitHub Actions)
TT_EMAIL = os.environ.get("TT_EMAIL")
TT_PASSWORD = os.environ.get("TT_PASSWORD")

def run_scraper():
    with sync_playwright() as p:
        # 1. Start invisible browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()

        print("Connecting to Tradetron...")
        page.goto("https://tradetron.tech/login", wait_until="networkidle")

        # 2. Smart Login
        page.fill("input[type='email']", TT_EMAIL)
        page.fill("input[type='password']", TT_PASSWORD)
        page.click("button[type='submit']")
        
        # Wait for dashboard to load
        page.wait_for_url("**/dashboard", timeout=30000)
        print("Login Successful!")

        # 3. Navigate to Deployed Strategies
        page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
        
        # 4. Lite-Vision Algorithm (Auto-switch if needed)
        if "Switch to Lite" in page.content():
            page.get_by_text("Switch to Lite").click()
            time.sleep(2)

        # 5. The Scrape (Neural Tree-Walker Logic)
        strategies = page.evaluate("""() => {
            let results = [];
            const cards = document.querySelectorAll('tr, .strategy-card, .deployment-card');
            cards.forEach(card => {
                let text = card.innerText;
                if (text.includes('by ') && (text.includes('₹') || text.includes('Rs.'))) {
                    let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                    let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                    
                    let pnl = 0.0;
                    let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)\\s*([Lk]?)/gi);
                    if (pnlMatches) {
                        let lastMatch = pnlMatches[pnlMatches.length - 1];
                        let val = lastMatch.replace(/[₹Rs\\.\\s,]/gi, '');
                        pnl = parseFloat(val) || 0.0;
                        if (lastMatch.toUpperCase().includes('K')) pnl *= 1000;
                        if (lastMatch.toUpperCase().includes('L')) pnl *= 100000;
                        if (lastMatch.includes('-')) pnl *= -1;
                    }

                    results.push({ name, pnl, status: text.includes('Live-Entered') ? 'Live' : 'Active' });
                }
            });
            return results;
        }""")

        print(f"Found {len(strategies)} strategies.")

        # 6. Save as clean JSON
        output = {
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "strategies": strategies
        }
        with open("data.json", "w") as f:
            json.dump(output, f, indent=4)

        browser.close()

if __name__ == "__main__":
    run_scraper()