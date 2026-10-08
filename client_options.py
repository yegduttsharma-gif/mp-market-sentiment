"""Daily NSE client-category index-option long open-interest snapshot (not trades)."""
import csv, io, json, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST=timezone(timedelta(hours=5,minutes=30))
out=Path("client_options.json")
def get_report(day):
    url="https://archives.nseindia.com/content/nsccl/fao_participant_oi_"+day.strftime("%d%m%Y")+".csv"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; PDMP public-data dashboard)","Accept":"text/csv,*/*","Referer":"https://www.nseindia.com/"})
    with urllib.request.urlopen(req,timeout=18) as response:
        raw=response.read().decode("utf-8-sig",errors="replace")
    rows=list(csv.DictReader(io.StringIO(raw)))
    for row in rows:
        cleaned={str(k).strip().lower():str(v or "").strip() for k,v in row.items() if k}
        if cleaned.get("client type","").lower()=="client":
            def value(name):
                return int(float(cleaned[name.lower()].replace(",","")))
            return {"date":day.isoformat(),"call_long":value("Option Index Call Long"),"put_long":value("Option Index Put Long"),"source":url}
    raise ValueError("Client row missing")
now=datetime.now(IST)
today=now.date()
snapshot=None
errors=[]
for n in range(8):
    day=today-timedelta(days=n)
    if day.weekday()>4:continue
    try:
        snapshot=get_report(day)
        break
    except Exception as exc:
        errors.append(str(exc)[:140])
if snapshot:
    total=snapshot["call_long"]+snapshot["put_long"]
    snapshot.update({"call_share_pct":round(100*snapshot["call_long"]/total,1) if total else None,"put_share_pct":round(100*snapshot["put_long"]/total,1) if total else None,"collected_at":now.isoformat(),"scope":"All NSE index options combined; Client category includes non-retail clients. End-of-day outstanding long OI, NOT today's option buys."})
    out.write_text(json.dumps(snapshot,indent=2)+"\n")
    print("Saved NSE Client index option long OI",snapshot["date"])
else:
    # Do not overwrite valid prior observations with fabricated zeros.
    print("NSE report unavailable; retained existing snapshot. "+("; ".join(errors[:2])))
