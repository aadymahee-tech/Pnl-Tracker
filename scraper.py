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
            page.goto("https://tradetron.tech/login", wait_until="networkidle", timeout=60000)
            
            # Step 2: Entering Credentials
            print("Step 2: Entering Credentials...")
            page.type("input[name='email']", os.environ.get("TT_EMAIL"), delay=100)
            page.type("input[name='password']", os.environ.get("TT_PASSWORD"), delay=100)
            
            # --- ALTCHA PROTECTION HANDLING ---
            print("Step 3: Handling Human Verification (ALTCHA)...")
            # We wait for the Altcha widget to appear and solve itself
            # The browser will automatically do the math in the background
            try:
                # Wait up to 30 seconds for the 'Verified' state
                page.wait_for_selector("altcha-widget", state="visible", timeout=10000)
                print("Altcha found. Solving proof-of-work...")
                
                # We wait until the hidden input 'altcha' gets a value (the solution)
                page.wait_for_function(
                    "() => document.querySelector('input[name=\"altcha\"]').value.length > 10",
                    timeout=30000
                )
                print("Verification Complete!")
            except Exception as e:
                print(f"Altcha Note: {str(e)} (Proceeding anyway)")

            print("Step 4: Clicking Sign In...")
            page.click("button[type='submit']")
            
            # Step 5: Wait for Login success
            time.sleep(10) 
            if "login" in page.url:
                page_text = page.inner_text("body")
                raise Exception(f"Stuck at Login. Page says: {page_text[:150]}")

            print("Step 6: Success! Scraping Deployed Page...")
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle", timeout=60000)
            time.sleep(5) 

            # Step 7: The Data Catch
            strategies = page.evaluate("""() => {
                let results = [];
                document.querySelectorAll('tr, .strategy-card, .deployment-card').forEach(el => {
                    let t = el.innerText;
                    if (t.includes('by ') && (t.includes('₹') || t.includes('Rs.'))) {
                        let lines = t.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        let pnlMatches = t.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let val = pnlMatches[pnlMatches.length - 1].replace(/[₹Rs\\.\\s,]/gi, '');
                            let pnl = parseFloat(val) || 0.0;
                            if (t.toUpperCase().includes('K')) pnl *= 1000;
                            if (t.toUpperCase().includes('L')) pnl *= 100000;
                            if (pnlMatches[pnlMatches.length - 1].includes('-')) pnl *= -1;
                            results.push({ name, pnl });
                        }
                    }
                });
                return [...new Map(results.map(i => [i.name, i])).values()];
            }""")

            print(f"DONE: Captured {len(strategies)} strategies.")
            with open("data.json", "w") as f:
                json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)

        except Exception as e:
            print(f"FAILED: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f, indent=4)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
