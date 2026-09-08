import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        # Start browser with "Anti-Detection" settings
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("Step 1: Logging in...")
            page.goto("https://tradetron.tech/login", wait_until="networkidle", timeout=60000)
            
            # Use specific selectors for accuracy
            page.locator("input[name='email']").fill(os.environ.get("TT_EMAIL"))
            page.locator("input[name='password']").fill(os.environ.get("TT_PASSWORD"))
            page.locator("button[type='submit']").click()
            
            # Wait for login success
            page.wait_for_url("**/dashboard", timeout=45000)
            print("Step 2: Login Successful! Navigating to Deployed...")

            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle", timeout=60000)
            
            # Wait for at least one strategy to appear
            page.wait_for_selector("text='by'", timeout=20000)

            # The Data Extraction Logic
            strategies = page.evaluate("""() => {
                let results = [];
                const cards = document.querySelectorAll('tr, .strategy-card, .deployment-card');
                cards.forEach(card => {
                    let text = card.innerText;
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
                        results.push({ name, pnl, status: 'Active' });
                    }
                });
                return results;
            }""")

            print(f"Step 3: Found {len(strategies)} strategies. Saving...")

            with open("data.json", "w") as f:
                json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)

        except Exception as e:
            print(f"FAILED: {str(e)}")
            # Still save an error file so the app knows
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
