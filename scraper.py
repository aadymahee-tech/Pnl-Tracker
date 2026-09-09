import os
import json
import time
import random
from playwright.sync_api import sync_playwright

def run_scraper():
    email = os.environ.get("TT_EMAIL").strip()
    password = os.environ.get("TT_PASSWORD").strip()
    
    # YOUR SHARED CODES (Add more as needed)
    shared_codes = [
        "9c83e96d-7321-4db0-ae72-8636826e6687",
        "e03c0c11-22d2-405f-a605-415822d197e4",
        "37dc822f-f7f1-47cc-99f2-d8a2db54dcc4",
        "12b18f93-542d-48de-996c-328b474ef7e0",
        "1ff9c236-f0c8-41cb-a168-e3a2ca46550f"
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 1000})
        page = context.new_page()

        try:
            # --- TASK A-C: LOGIN GATE ---
            print("GATE 1: Establishing Session...")
            page.goto("https://tradetron.tech/login", wait_until="load")
            page.fill("input[name='email']", email)
            page.fill("input[name='password']", password)
            
            try:
                page.click("altcha-widget", position={"x": 20, "y": 20}, timeout=10000)
                page.wait_for_function("() => document.querySelector('input[name=\"altcha\"]').value.length > 20", timeout=20000)
                print("CHECK: Altcha Verified.")
            except: pass

            page.click("button[type='submit']", force=True)
            # Patiently wait for any sign of success
            page.wait_for_selector("text='Logout', text='Dashboard', .dashboard-wrapper", timeout=60000)
            print("CHECK: Login Successful.")

            # --- TASK D: FETCH SHARED DATA ---
            final_results = []
            print(f"GATE 2: Scanning {len(shared_codes)} shared reports...")

            for code in shared_codes:
                try:
                    print(f"Action: Opening Shared Code {code[:8]}...")
                    url = f"https://tradetron.tech/strategy-execution/shared/{code}"
                    page.goto(url, wait_until="load", timeout=60000)
                    time.sleep(5) # Let pulsing numbers load
                    
                    # Pattern Extraction
                    data = page.evaluate("""() => {
                        let text = document.body.innerText;
                        let name = document.querySelector('h1, h2, .strategy-name, .text-primary')?.innerText || "Unknown";
                        
                        // Extract Counter (Pattern: "Counter: 37")
                        let cMatch = text.match(/Counter:\\s*(\\d+)/i);
                        let counterNo = cMatch ? parseInt(cMatch[1]) : 0;

                        // Extract P&L (Largest currency match)
                        let pnl = 0.0;
                        let pnlMatches = text.match(/[₹Rs\\.]\\s?([+-]?[\\d,]+\\.?\\d*)/gi);
                        if (pnlMatches) {
                            let lastVal = pnlMatches[pnlMatches.length - 1];
                            pnl = parseFloat(lastVal.replace(/[₹Rs\\.\\s,]/gi, '')) || 0.0;
                            if (lastVal.includes('-')) pnl *= -1;
                        }
                        
                        return { name, counterNo, pnl, status: text.includes('Live-Entered') ? 'Live' : 'Active' };
                    }""")
                    
                    data['code'] = code
                    final_results.append(data)
                    print(f"SUCCESS: Captured {data['name']} (P&L: {data['pnl']})")
                except Exception as inner_e:
                    print(f"SKIP: Code {code[:8]} failed: {str(inner_e)}")

            # --- TASK E: SAVE ---
            output = {
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(final_results),
                "strategies": final_results
            }
            with open("data.json", "w") as f:
                json.dump(output, f, indent=4)
            print(f"MISSION SUCCESS: Saved {len(final_results)} items.")

        except Exception as e:
            print(f"CRITICAL MISSION FAILURE: {str(e)}")
            page.screenshot(path="mission_error.png")
            with open("data.json", "w") as f:
                json.dump({"error": str(e)}, f)
        
        browser.close()

if __name__ == "__main__":
    run_scraper()
