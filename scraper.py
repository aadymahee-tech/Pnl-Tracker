import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        # Launch a standard browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. GO DIRECTLY TO DEPLOYED (It will force you to login)
            print("Navigating...")
            page.goto("https://tradetron.tech/deployed-strategies", timeout=60000)
            time.sleep(5)

            # 2. LOGIN (Only if we are not already in)
            if "login" in page.url:
                print("Logging in...")
                # Fill the form using the most basic selectors
                page.fill("input[name='email']", os.environ.get("TT_EMAIL").strip())
                page.fill("input[name='password']", os.environ.get("TT_PASSWORD").strip())
                
                # Just click the button. No waiting for Captchas.
                page.click("button[type='submit']")
                print("Form Submitted. Waiting for redirect...")
                time.sleep(10)

            # 3. SCRAPE (The simplest possible way)
            print("Capturing P&L...")
            strategies = page.evaluate("""() => {
                let data = [];
                // Look for every deployment block
                document.querySelectorAll('.deployed-strategy-block, tr, .strategy-card').forEach(el => {
                    let txt = el.innerText;
                    if (txt.includes('by ') && (txt.includes('₹') || txt.includes('Rs.'))) {
                        let name = txt.split('\\n')[0].trim();
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
                return data;
            }""")

            # 4. SAVE
            with open("data.json", "w") as f:
                json.dump({
                    "last_updated": time.strftime("%H:%M:%S"),
                    "count": len(strategies),
                    "strategies": strategies
                }, f, indent=4)
            print(f"Success! Saved {len(strategies)} strategies.")

        except Exception as e:
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
