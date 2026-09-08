import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        # Standard Desktop browser for best compatibility
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 1000})
        page = context.new_page()

        try:
            print("Step 1: Navigating to Tradetron...")
            page.goto("https://tradetron.tech/login", timeout=60000)
            time.sleep(5)

            print("Step 2: Entering Credentials...")
            page.fill("input[name='email']", os.environ.get("TT_EMAIL").strip())
            page.fill("input[name='password']", os.environ.get("TT_PASSWORD").strip())
            
            # --- ALTCHA HANDSHAKE ---
            print("Step 3: Handling ALTCHA (The Robot Check)...")
            try:
                # 1. Find the checkbox inside the altcha-widget and click it
                # We wait for the 'I'm not a robot' text area to be clickable
                page.click("altcha-widget", position={"x": 20, "y": 20}) 
                print("SUCCESS: Clicked the verification box.")
                
                # 2. WAIT for the verification to complete
                # ALTCHA math takes time. We wait for the hidden field to get its 'Proof' token.
                print("Waiting for computer to finish math (Proof-of-Work)...")
                page.wait_for_function(
                    "() => document.querySelector('input[name=\"altcha\"]').value.length > 20",
                    timeout=30000
                )
                print("SUCCESS: Human verification verified!")
                
            except Exception as e:
                print(f"ALTCHA NOTE: {str(e)} (Proceeding anyway...)")

            print("Step 4: Clicking Sign In...")
            # We use a slight delay before clicking to ensure Tradetron's server is ready
            time.sleep(2)
            page.click("button[type='submit']", force=True)
            
            print("Step 5: Waiting for Dashboard (Redirect)...")
            # Wait until the URL changes to something that isn't 'login'
            page.wait_for_url("**/dashboard**", timeout=45000)
            print(f"LOGIN SUCCESS! Landed on: {page.url}")

            # Now go to the data page
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
            time.sleep(5)

            # --- EXTRACTION ---
            print("Step 6: Capturing P&L Data...")
            strategies = page.evaluate("""() => {
                let data = [];
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

            print(f"Step 7: Captured {len(strategies)} strategies. Saving...")
            
            with open("data.json", "w") as f:
                json.dump({
                    "last_updated": time.strftime("%H:%M:%S"),
                    "final_url": page.url,
                    "strategies": strategies
                }, f, indent=4)

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
