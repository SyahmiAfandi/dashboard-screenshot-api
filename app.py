from flask import Flask, send_file, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from io import BytesIO
import os
import traceback
import time

app = Flask(__name__)
CORS(app)

# CONFIGURATION
# If qordia.xyz is on the same server, try http://localhost:port or the Docker service name
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://qordia.xyz/login")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "service": "dashboard-screenshot-api"})

@app.route("/screenshot-dashboard", methods=["GET"])
def screenshot_dashboard():
    playwright = None
    browser = None
    
    try:
        # Start Playwright
        playwright = sync_playwright().start()
        
        # Launch Chromium with Docker-optimized flags
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--no-zygote"
            ]
        )

        # Create context with a real User-Agent to bypass bot detection
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True  # Bypass SSL certificate issues
        )
        
        page = context.new_page()

        # Set a generous timeout (60 seconds) for VPS environments
        page.set_default_timeout(60000)

        print(f"Navigating to: {DASHBOARD_URL}")
        
        # Navigate to the URL
        # 'domcontentloaded' is usually enough and faster than 'networkidle'
        response = page.goto(DASHBOARD_URL, wait_until="domcontentloaded")
        
        if not response:
            raise Exception("No response received from the URL. Check DNS or Firewall.")

        # Wait for the body to be visible or a specific selector 
        # (e.g. wait_for_selector(".login-form"))
        page.wait_for_selector("body", state="visible", timeout=30000)

        # Optional: wait a moment for any JS animations to settle
        time.sleep(1)

        # Take full page screenshot
        screenshot_bytes = page.screenshot(full_page=True)

        # Return the image
        return send_file(
            BytesIO(screenshot_bytes),
            mimetype="image/png",
            as_attachment=False,
            download_name="dashboard.png"
        )

    except Exception as e:
        print(f"Error caught: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }), 500

    finally:
        # Crucial cleanup to prevent memory leaks and zombie processes
        if browser:
            browser.close()
        if playwright:
            playwright.stop()

if __name__ == "__main__":
    # Use PORT from environment (Coolify/Heroku/Railway) or default to 5000
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)