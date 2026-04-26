from flask import Flask, send_file, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from io import BytesIO
import os
import time

app = Flask(__name__)
CORS(app)

DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://160.187.210.192.nip.io/login")


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "ok",
        "service": "dashboard-screenshot-api"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok"
    })


@app.route("/screenshot-dashboard", methods=["GET"])
def screenshot_dashboard():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )

            page = browser.new_page(
                viewport={
                    "width": 1440,
                    "height": 1000
                }
            )

            page.goto(
                DASHBOARD_URL,
                wait_until="networkidle",
                timeout=60000
            )

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
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
