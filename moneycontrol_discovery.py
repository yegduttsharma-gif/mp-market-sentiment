"""Moneycontrol permission status. No automated website access or comment extraction."""
import json
from pathlib import Path
from datetime import datetime, timezone
out={
 "collected_at":datetime.now(timezone.utc).isoformat(),
 "platform":"Moneycontrol",
 "method":"terms_review_no_automated_access",
 "status":"permission_required",
 "verified_directional_opinions":0,
 "terms_url":"https://www.moneycontrol.com/cdata/termsofuse.php?classic=true",
 "reason":"Current terms section 4.4 restricts automated extraction and machine-readable databases without prior express written permission.",
 "sources":{"Moneycontrol message board":{"url":"https://mmb.moneycontrol.com/","status":"permission_required","verified_comments":0}}
}
Path("moneycontrol_discovery.json").write_text(json.dumps(out,indent=2)+"\n")
print("Moneycontrol: permission required; no requests made and no comments counted")
