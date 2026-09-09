import os
import json
import time
from playwright.sync_api import sync_playwright

def run_scraper():
    email = os.environ.get("TT_EMAIL").strip()
    password = os.environ.get("TT_PASSWORD").strip()
    
    # ADD YOUR SHARED CODES HERE (Separated by commas)
    # I have put the one you gave me as the first one.
    shared_codes = [
        "9c83e96d-7321-4db0-ae72-8636826e6687",
        # "e03c0c11-...", (Add more here later)
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 1000})
        page = context.new_page()

        try:
            # --- STEP 1: PROVEN LOGIN ---
            print("Step 1: Establishing Authenticated Session...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20})
                page.wait_for_function("() => document.querySelector('input[name=\"altcha\"]').value.length > 20", timeout=20000)
            except: pass
            page.click("button[type='submit']", force=True)
            page.wait_for_url("**/dashboard*", timeout=30000)
            print("SUCCESS: Session established.")

            # --- STEP 2: FETCH SHARED DATA ---
            print(f"Step 2: Monitoring {len(shared_codes)} shared deployments...")
            final_results = []

            for code in shared_codes:
                print(f"Action: Reading Shared Code {code[:8]}...")
                # The shared execution link provides a clean view of the specific deployment
                shared_url = f"https://tradetron.tech/strategy-execution/shared/{code}"
                page.goto(shared_url, wait_until="networkidle", timeout=60000)
                time.sleep(3) # Let pulsing data load

                # PATTERN EXTRACTION (Trained on Shared Page Layout)
                data = page.evaluate("""() => {
                    let text = document.body.innerText;
                    // Extract Name (Usually the first big header)
                    let name = document.querySelector('h1, h2, .strategy-name')?.innerText || "Unknown";
                    
                    // Extract Counter (Pattern: "Counter: 37")
                    let counterMatch = text.match(/Counter:\\s*(\\d+)/i);
                    let counterNo = counterMatch ? parseInt(counterMatch[1]) : 0;

                    // Extract P&L (Looks for the largest currency value)
                    let pnl = 0.0;
                    let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                    if (pnlMatches) {
                        let lastVal = pnlMatches[pnlMatches.length - 1];
                        pnl = parseFloat(lastVal.replace(/[₹Rs\\.\\s,]/gi, '')) || 0.0;
                        if (lastVal.includes('-')) pnl *= -1;
                    }

                    // Extract Status
                    let status = text.includes('Live-Entered') ? 'Live' : 'Active';
                    
                    return { name, counterNo, pnl, status };
                }""")
                
                # Tag it with the code for tracking
                data['code'] = code
                final_results.append(data)
                print(f"Found: {data['name']} | P&L: {data['pnl']}")

            # --- STEP 3: SAVE ---
            output = {
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(final_results),
                "strategies": final_results
            }
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)
            print("MISSION SUCCESS: Shared data saved.")

        except Exception as e:
            print(f"SHARED PIPE ERROR: {str(e)}")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
