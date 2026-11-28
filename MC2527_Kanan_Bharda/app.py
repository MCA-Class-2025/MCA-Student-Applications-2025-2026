import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from utils.extractor import extract_urls, extract_ips
from utils.excel_handler import save_record
from services.safe_browsing import check_safe_browsing
from services.virustotal import check_virustotal
from services.abuseipdb import check_abuseipdb
from services.phishtank import check_phishtank
from services.urlhaus import check_urlhaus
from services.gemini import analyze_with_gemini

load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.post("/api/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    supplied_url = (data.get("url") or "").strip()

    if not message:
        return jsonify({"error": "Please enter a message to analyze."}), 400

    urls = extract_urls(message)
    if supplied_url and supplied_url not in urls:
        urls.insert(0, supplied_url)

    primary_url = urls[0] if urls else ""

    # Five external data-collection APIs.
    api_results = {
        "safe_browsing": check_safe_browsing(primary_url) if primary_url else {"status": "not_checked", "reason": "No URL supplied"},
        "virustotal": check_virustotal(primary_url) if primary_url else {"status": "not_checked", "reason": "No URL supplied"},
        "phishtank": check_phishtank(primary_url) if primary_url else {"status": "not_checked", "reason": "No URL supplied"},
        "urlhaus": check_urlhaus(primary_url) if primary_url else {"status": "not_checked", "reason": "No URL supplied"},
        "abuseipdb": {"status": "not_checked", "reason": "No IP found"},
    }

    ips = extract_ips(message)
    if not ips and primary_url:
        # DNS resolution is local; AbuseIPDB itself is still the external data API.
        from socket import gethostbyname
        try:
            from urllib.parse import urlparse
            host = urlparse(primary_url).hostname
            if host:
                ips = [gethostbyname(host)]
        except Exception:
            pass

    if ips:
        api_results["abuseipdb"] = check_abuseipdb(ips[0])

    assessment = analyze_with_gemini(message, primary_url, api_results)

    record = {
        "message": message,
        "url": primary_url,
        "safe_browsing": api_results["safe_browsing"],
        "virustotal": api_results["virustotal"],
        "abuseipdb": api_results["abuseipdb"],
        "phishtank": api_results["phishtank"],
        "urlhaus": api_results["urlhaus"],
        "assessment": assessment,
    }
    save_record(record)

    return jsonify({
        "success": True,
        "message": message,
        "url": primary_url,
        "apis": api_results,
        "assessment": assessment,
    })

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
