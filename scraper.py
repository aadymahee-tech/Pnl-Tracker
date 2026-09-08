import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("Step 1: Navigating to Deployed Page...")
            page.goto("https://tradetron.tech/deployed-strategies", timeout=60000)
            time.sleep(5)

            if "login" in page.url:
                print(f"Current URL is {page.url}. Login required.")
                
                # Check if fields exist
                email_input = page.locator("input[name='email']").first
                pass_input = page.locator("input[name='password']").first
                
                if email_input.is_visible():
                    print("SUCCESS: Email field found. Filling...")
                    email_input.fill(os.environ.get("TT_EMAIL").strip())
                    
                    print("SUCCESS: Password field found. Filling...")
                    pass_input.fill(os.environ.get("TT_PASSWORD").strip())
                    
                    print("Step 2: Clicking Sign In Button...")
                    # We use a forced click to ensure it goes through
                    page.click("button[type='submit']", force=True)
                    
                    print("Step 3: Waiting for Redirect (15 seconds)...")
                    time.sleep(15)
                else:
                    print("FAILURE: Could not find login fields. Tradetron might be showing a different page.")
            
            # Final Check
            print(f"Final Page URL: {page.url}")
            print("Step 4: Attempting to find P&L numbers...")
            
            strategies = page.evaluate("""() => {
                let data = [];
                // Target the clean 'Lite' card or standard rows
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

            print(f"Step 5: Process Complete. Found {len(strategies)} strategies.")
            
            with open("data.json", "w") as f:
                json.dump({
                    "last_updated": time.strftime("%H:%M:%S"),
                    "final_url": page.url,
                    "count": len(strategies),
                    "strategies": strategies
                }, f, indent=4)

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e), "url": page.url}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
