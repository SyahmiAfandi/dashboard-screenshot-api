from flask import Flask, send_file, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from io import BytesIO
import os
import traceback  # Added for better debugging

app = Flask(__name__)
CORS(app)

# Use environmental variable or fallback
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://qordia.xyz/login")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "service": "dashboard-screenshot-api"})

@app.route("/screenshot-dashboard", methods=["GET"])
def screenshot_dashboard():
    # Keep track of objects to close them in 'finally'
    browser = None
    playwright = None
    
    try:
        playwright = sync_playwright().start()
        
        # Launch browser with essential Docker flags
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--no-zygote",
                "--single-process" # Helps in low-resource environments
            ]
        )

        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            ignore_https_errors=True # Useful if qordia.xyz has SSL issues in Docker
        )
        
        page = context.new_page()

        # Set a reasonable default timeout for all actions
        page.set_default_timeout(20000) 

        # Navigate - 'commit' is faster than 'load' if you just need the page to start
        response = page.goto(DASHBOARD_URL, wait_until="domcontentloaded")
        
        if not response:
            raise Exception("Failed to load page: No response received")

        # Wait for a specific element. 'body' is too generic; 
        # try to use a selector like '.login-card' or '#app' if possible.
        page.wait_for_selector("body", state="visible")

        # Take the screenshot
        screenshot_bytes = page.screenshot(full_page=True)

        return send_file(
            BytesIO(screenshot_bytes),
            mimetype="image/png",
            as_attachment=False,
            download_name="dashboard.png"
        )

    except Exception as e:
        # Print the error to your console/logs
        print(f"Error occurred: {e}")
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc() # Returns the full error to the browser
        }), 500

    finally:
        # Crucial: Ensure the browser closes even if an error occurs
        if browser:
            browser.close()
        if playwright:
            playwright.stop()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)