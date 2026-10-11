"""Record genuine India-local daily stock and sector sentiment snapshots.

One observation per stock per day; never fabricate missing dates.
"""
import json
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo

source=Path("retail_stocks.json")
target=Path("stock_sentiment_history.json")
if not source.exists():
    raise SystemExit("No retail snapshot available")
data=json.loads(source.read_text(encoding="utf-8"))
stamp=data.get("collected_at")
if not stamp or data.get("status")!="available":
    raise SystemExit("No valid retail snapshot")
date=datetime.fromisoformat(stamp.replace("Z","+00:00")).astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat()
try:
    saved=json.loads(target.read_text(encoding="utf-8"))
except (FileNotFoundError,ValueError):
    saved={"method":"actual_daily_investor_discussion_snapshots_v1","stocks":{}}
stocks=saved.setdefault("stocks",{})
for row in data.get("stocks",[]):
    name=row.get("name")
    if not name:
        continue
    up=int(row.get("bullish",0))
    down=int(row.get("bearish",0))
    observation={"date":date,"collected_at":stamp,"bullish":up,"bearish":down,
                 "neutral":int(row.get("neutral",0)),"directional":up+down,
                 "bullish_pct":round(100*up/(up+down)) if up+down else None,
                 "investor_mentions":int(row.get("investor_mentions",row.get("mentions",0))),
                 "commentary_mentions":int(row.get("commentary_mentions",0))}
    rows=[x for x in stocks.get(name,[]) if x.get("date")!=date]
    rows.append(observation)
    stocks[name]=sorted(rows,key=lambda x:x["date"])[-90:]
saved["last_recorded_at"]=datetime.now(timezone.utc).isoformat()
target.write_text(json.dumps(saved,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("Stock history saved",date,len(stocks),"stocks")
