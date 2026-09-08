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
            
            # Close any blocking overlays (Mobile promo, etc.)
            try:
                page.locator(".tt-app-promo__close, .close, .modal-close").first.click(timeout=5000)
                print("Step 1b: Closed blocking overlay.")
            except: pass

            print("Step 2: Entering Credentials...")
            # Use multi-selector logic for robustness
            email_field = page.locator("input[name='email'], #modalEmailSignIn, input[type='email']").first
            pass_field = page.locator("input[name='password'], #modalPasswordSignIn, input[type='password']").first
            
            email_field.fill(os.environ.get("TT_EMAIL"))
            pass_field.fill(os.environ.get("TT_PASSWORD"))
            
            print("Step 3: Attempting Sign In...")
            login_btn = page.locator("button[type='submit'], #signInButtonPopup, .btn-login").first
            login_btn.click()
            
            # WAIT FOR DASHBOARD OR SUCCESS INDICATOR
            print("Step 4: Waiting for Dashboard...")
            page.wait_for_selector("a[href*='deployed-strategies'], .dashboard-wrapper, text='Deployed'", timeout=60000)
            print("Step 5: Login Success! Fetching P&L...")

            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle", timeout=60000)
            time.sleep(10) # Heavy buffer for pulsing data

            strategies = page.evaluate("""() => {
                let results = [];
                const cards = document.querySelectorAll('tr, .strategy-card, .deployment-card, .deployed-strategy-block');
                cards.forEach(c => {
                    let text = c.innerText;
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

            print(f"Step 6: Captured {len(strategies)} strategies.")
            output = {"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)

        except Exception as e:
            print(f"FATAL ERROR: {str(e)}")
            # Debug: Capture what the bot actually saw
            page_text = page.content()[:500].replace('\n', ' ')
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url, "snapshot": page_text}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
