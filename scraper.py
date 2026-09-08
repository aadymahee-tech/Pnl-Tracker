import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("Step 1: Opening Login Page...")
            page.goto("https://tradetron.tech/login", wait_until="networkidle")
            
            # Close any blocking popups
            try: page.click(".tt-app-promo__close", timeout=3000)
            except: pass

            print("Step 2: Typing Credentials (slowly)...")
            # We type with a 100ms delay to look human
            page.type("input[name='email']", os.environ.get("TT_EMAIL"), delay=100)
            page.type("input[name='password']", os.environ.get("TT_PASSWORD"), delay=100)
            
            print("Step 3: Submitting...")
            page.click("button[type='submit']")
            
            # Give it 10 seconds to transition
            time.sleep(10)

            # CHECK: Did we log in?
            if "login" in page.url:
                print("STUCK ON LOGIN PAGE. Searching for errors...")
                error_msg = page.locator(".alert-danger, .text-danger, #error_email").first.inner_text()
                raise Exception(f"Tradetron Error: {error_msg}")

            print("Step 4: Login Success! Fetching Data...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
            page.wait_for_selector("text='Profit'", timeout=30000)

            strategies = page.evaluate("""() => {
                let results = [];
                document.querySelectorAll('tr, .strategy-card, .deployment-card').forEach(c => {
                    let text = c.innerText;
                    if (text.includes('by ') && (text.includes('₹') || text.includes('Rs.'))) {
                        let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let val = pnlMatches[pnlMatches.length - 1].replace(/[₹Rs\\.\\s,]/gi, '');
                            let pnl = parseFloat(val) || 0.0;
                            if (text.toUpperCase().includes('K')) pnl *= 1000;
                            if (text.toUpperCase().includes('L')) pnl *= 100000;
                            if (pnlMatches[pnlMatches.length - 1].includes('-')) pnl *= -1;
                            results.push({ name, pnl });
                        }
                    }
                });
                return results;
            }""")

            print(f"Step 5: Saved {len(strategies)} strategies.")
            with open("data.json", "w") as f:
                json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)

        except Exception as e:
            print(f"INVESTIGATION FAILED: {str(e)}")
            # Log exactly what happened for the user
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "current_url": page.url}, f, indent=4)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
