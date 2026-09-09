import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    email = os.environ.get("TT_EMAIL").strip()
    password = os.environ.get("TT_PASSWORD").strip()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1400, 'height': 1200})
        page = context.new_page()

        try:
            print("Step 1: Logging in...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20})
                time.sleep(12) 
            except: pass

            page.click("button[type='submit']")
            page.wait_for_url("**/dashboard*", timeout=60000)
            print("LOGIN SUCCESS!")

            # Step 2: Prepare Page (Lite Mode + Reset)
            page.goto("https://tradetron.tech/deployed-strategies", wait_until="networkidle")
            
            # Click Reset Filter
            try: page.locator(".fa-recycle, .fa-sync").first.click(timeout=5000)
            except: pass

            # Click Switch to Lite
            try:
                if "Switch to Lite" in page.content():
                    page.get_by_text("Switch to Lite").click()
                    time.sleep(3)
            except: pass

            # Step 3: Extract & Filter (Only LIVE AUTO)
            strategies = page.evaluate("""() => {
                let results = [];
                document.querySelectorAll('.strategy-card, .deployment-card, .deployed-strategy-block').forEach(card => {
                    let text = card.innerText;
                    let upperText = text.toUpperCase();
                    
                    // FILTER: Only pick 'LIVE AUTO'
                    if (upperText.includes('LIVE AUTO') && (text.includes('₹') || text.includes('Rs.'))) {
                        let lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                        let name = lines[0].replace(/^\\d+\\.\\s*/, '').split(' by ')[0].trim();
                        
                        // Capital
                        let capMatch = text.match(/Capital:\\s*[₹Rs\\.]\\s?([\\d,]+\\.?\\d*)\\s*([Lk]?)/i);
                        let capital = 0;
                        if (capMatch) {
                            capital = parseFloat(capMatch[1].replace(/,/g, ''));
                            if (capMatch[2].toUpperCase() === 'L') capital *= 100000;
                            if (capMatch[2].toUpperCase() === 'K') capital *= 1000;
                        }

                        // Multiplier
                        let multMatch = text.match(/Multiplier:\\s*(\\d+)x/i);
                        let multiplier = multMatch ? parseInt(multMatch[1]) : 1;

                        // P&L (Latest/Current)
                        let pnl = 0.0;
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let lastMatch = pnlMatches[pnlMatches.length - 1];
                            let val = lastMatch.replace(/[₹Rs\\.\\s,]/gi, '');
                            pnl = parseFloat(val) || 0.0;
                            if (lastMatch.includes('-')) pnl *= -1;
                        }

                        results.push({ name, pnl, capital, multiplier, status: text.includes('Live-Entered') ? 'Live-Entered' : 'Active' });
                    }
                });
                return results;
            }""")

            print(f"Step 4: Captured {len(strategies)} LIVE AUTO strategies.")
            with open("data.json", "w") as f:
                json.dump({"last_updated": time.strftime("%H:%M:%S"), "strategies": strategies}, f, indent=4)

        except Exception as e:
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
