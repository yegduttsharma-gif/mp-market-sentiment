"""Save one real observation per India-local calendar day for each market.

Uses the latest successfully collected headline snapshot only; never backfills missing days.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

source=Path("data.json")
history=Path("sentiment_history.json")
if not source.exists():
    raise SystemExit("No news snapshot to record")
snapshot=json.loads(source.read_text(encoding="utf-8"))
try:
    saved=json.loads(history.read_text(encoding="utf-8"))
except (FileNotFoundError, ValueError):
    saved={"method":"daily_latest_verified_headline_snapshot_v1","markets":{}}
markets=saved.setdefault("markets",{})
statuses=snapshot.get("feed_status",{})
stamp=snapshot.get("updated_at")
if not stamp:
    raise SystemExit("No verified snapshot timestamp")
dt=datetime.fromisoformat(stamp.replace("Z","+00:00"))
day=dt.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat()
for name,info in snapshot.get("markets",{}).items():
    if statuses.get(name)!="updated":
        print(name, "skipped: feed not updated")
        continue
    up=sum(x.get("sentiment")=="bullish" for x in info.get("items",[]))
    down=sum(x.get("sentiment")=="bearish" for x in info.get("items",[]))
    directional=up+down
    if directional<1:
        continue
    observation={"date":day,"collected_at":stamp,"bullish":up,"bearish":down,
                 "neutral":sum(x.get("sentiment")=="neutral" for x in info.get("items",[])),
                 "directional":directional,"bullish_pct":round(100*up/directional),
                 "publishers":len({x.get("source","") for x in info.get("items",[]) if x.get("source")})}
    rows=markets.setdefault(name,[])
    rows=[x for x in rows if x.get("date")!=day]
    rows.append(observation)
    rows.sort(key=lambda x:x["date"])
    markets[name]=rows[-30:]
saved["last_recorded_at"]=datetime.now(timezone.utc).isoformat()
history.write_text(json.dumps(saved,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("Historical market counts:",{k:len(v) for k,v in markets.items()})
