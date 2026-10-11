"""Check public Moneycontrol message-board accessibility, without scraping comments."""
import json
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

URLS = {
    "Moneycontrol message board": "https://mmb.moneycontrol.com/",
    "Moneycontrol main site": "https://www.moneycontrol.com/",
}
out = {
    "collected_at": datetime.now(timezone.utc).isoformat(),
    "platform": "Moneycontrol",
    "method": "public_accessibility_check_only",
    "verified_directional_opinions": 0,
    "sources": {},
}
for name, url in URLS.items():
    try:
        request = urllib.request.Request(url, headers={
            "User-Agent": "PDMP-Research/1.0",
            "Accept": "text/html",
        })
        with urllib.request.urlopen(request, timeout=15) as response:
            status = response.status
            size = len(response.read(100000))
        out["sources"][name] = {
            "url": url,
            "status": "accessible" if status == 200 and size > 1000 else "unverified",
            "http_status": status,
            "verified_comments": 0,
        }
    except Exception as exc:
        out["sources"][name] = {
            "url": url,
            "status": "unavailable",
            "error": type(exc).__name__,
            "verified_comments": 0,
        }
Path("moneycontrol_discovery.json").write_text(json.dumps(out, indent=2) + "\n")
print("Moneycontrol accessibility:", out["sources"])
