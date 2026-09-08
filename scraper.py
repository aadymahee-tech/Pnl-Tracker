import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 1000},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("Step 1: Connecting to Tradetron...")
            page.goto("https://tradetron.tech/login", wait_until="load", timeout=60000)
            
            # KILL PROMOS: Remove any overlays that might block the bot's vision
            page.evaluate("""() => {
                document.querySelectorAll('.tt-app-promo__close, .close, .modal').forEach(el => el.remove());
                document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                document.body.classList.remove('modal-open');
            }""")

            print("Step 2: Entering Credentials...")
            # We use strip() to remove any accidental spaces from GitHub Secrets
            email = os.environ.get("TT_EMAIL").strip()
            password = os.environ.get("TT_PASSWORD").strip()
            
            page.type("input[name='email']", email, delay=100)
            page.type("input[name='password']", password, delay=100)
            
            print("Step 3: Solving Altcha (Waiting for green signal)...")
            # We wait for the hidden 'altcha' input to be filled with the server-side solution
            page.wait_for_function(
                "() => { const el = document.querySelector('input[name=\"altcha\"]'); return el && el.value.length > 30; }",
                timeout=60000
            )
            print("Altcha Verified!")

            print("Step 4: Submitting Login Form...")
            # Use direct JS submission to bypass any UI blocking
            page.evaluate("() => document.querySelector('button[type=\"submit\"]').click()")
            
            # WAIT FOR THE DASHBOARD
            print("Step 5: Waiting for Dashboard...")
            page.wait_for_selector("a[href*='deployed'], .dashboard-wrapper, text='Logout'", timeout=60000)
            print("LOGIN SUCCESS!")

            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
            time.sleep(10) # Heavy buffer for live numbers

            strategies = page.evaluate("""() => {
                let results = [];
                document.querySelectorAll('div, tr, section, .strategy-card').forEach(el => {
                    let t = el.innerText;
                    if (t.includes('by ') && (t.includes('₹') || t.includes('Rs.')) && t.length < 500 && t.length > 50) {
                        let name = t.split('\\n')[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        let pnlMatches = t.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let lastMatch = pnlMatches[pnlMatches.length - 1];
                            let val = lastMatch.replace(/[₹Rs\\.\\s,]/gi, '');
                            let pnl = parseFloat(val) || 0.0;
                            if (lastMatch.toUpperCase().includes('K')) pnl *= 1000;
                            if (lastMatch.toUpperCase().includes('L')) pnl *= 100000;
                            if (lastMatch.includes('-')) pnl *= -1;
                            results.push({ name, pnl });
                        }
                    }
                });
                return [...new Map(results.map(i => [i.name, i])).values()];
            }""")

            print(f"DONE: Captured {len(strategies)} items.")
            with open("data.json", "w") as f:
                json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)

        except Exception as e:
            print(f"FAILED: {str(e)}")
            # Capture the exact error from the page (e.g. "Invalid Password")
            try:
                page_error = page.inner_text(".alert-danger, .text-danger")
            except:
                page_error = "No specific error on screen"
            
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "page_msg": page_error, "url": page.url}, f, indent=4)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
