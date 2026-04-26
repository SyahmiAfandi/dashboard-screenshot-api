from flask import Flask, send_file, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from io import BytesIO
import os
import time

app = Flask(__name__)
CORS(app)

# Use the internal Docker URL if possible, or ensure this is reachable
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://qordia.xyz/login")

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "service": "dashboard-screenshot-api"})

@app.route("/screenshot-dashboard", methods=["GET"])
def screenshot_dashboard():
    browser = None
    try:
        with sync_playwright() as p:
            # Added more flags for stability in Docker/Coolify
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-setuid-sandbox",
                    "--no-zygote"
                ]
            )

            # Use a single context to manage timeouts better
            context = browser.new_context(viewport={"width": 1440, "height": 1000})
            page = context.new_page()

            # FIX 1: Change 'networkidle' to 'load' to avoid 60s timeouts
            # FIX 2: Added a shorter timeout for the initial navigation
            page.goto(
                DASHBOARD_URL, 
                wait_until="load", 
                timeout=30000 
            )

            # FIX 3: Instead of waiting for the whole network, 
            # wait for a specific element that proves the dashboard loaded.
            # Replace '.login-form' or 'body' with a selector from your app.
            page.wait_for_selector("body", timeout=10000)

            # Optional: Small sleep to let animations finish
            time.sleep(2)

            screenshot_bytes = page.screenshot(full_page=True)
            browser.close()

            return send_file(
                BytesIO(screenshot_bytes),
                mimetype="image/png",
                as_attachment=False,
                download_name="dashboard.png"
            )

    except Exception as e:
        if browser:
            browser.close()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    # Coolify usually passes a PORT env variable, use it if available
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)