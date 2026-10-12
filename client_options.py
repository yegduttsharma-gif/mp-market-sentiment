"""Daily NSE client-category index-option long open-interest snapshot (not trades)."""
import csv, io, json, re, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST=timezone(timedelta(hours=5,minutes=30))
out=Path("client_options.json")
history_path=Path("client_options_history.json")
def get_report(day):
    url="https://archives.nseindia.com/content/nsccl/fao_participant_oi_"+day.strftime("%d%m%Y")+".csv"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; PDMP public-data dashboard)","Accept":"text/csv,*/*","Referer":"https://www.nseindia.com/"})
    with urllib.request.urlopen(req,timeout=18) as response:
        raw=response.read().decode("utf-8-sig",errors="replace")
    # NSE files may start with a report-title/date line before the CSV header.
    # Locate the real header instead of assuming it is line one.
    lines=raw.splitlines()
    header_index=next((i for i,line in enumerate(lines) if "client type" in line.lower() and "option index call long" in line.lower()),None)
    if header_index is None:
        raise ValueError("NSE CSV header missing: "+repr(lines[:2])[:160])
    rows=csv.DictReader(io.StringIO("\n".join(lines[header_index:])))
    for row in rows:
        cleaned={re.sub(r"\\s+"," ",str(k).strip().lower()):str(v or "").strip() for k,v in row.items() if k}
        if cleaned.get("client type","").lower()=="client":
            def value(name):
                return int(float(cleaned[name.lower()].replace(",","")))
            return {"date":day.isoformat(),"call_long":value("Option Index Call Long"),"put_long":value("Option Index Put Long"),"source":url}
    raise ValueError("Client row missing after valid header")
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
    try:
        history=json.loads(history_path.read_text()) if history_path.exists() else []
        if not isinstance(history,list):history=[]
    except (ValueError,OSError):history=[]
    if out.exists():
        try:
            prior=json.loads(out.read_text())
            history.append({k:prior[k] for k in ("date","call_long","put_long")})
        except (ValueError,OSError,KeyError,TypeError):pass
    history.append({k:snapshot[k] for k in ("date","call_long","put_long")})
    by_date={x["date"]:x for x in history if isinstance(x,dict) and isinstance(x.get("date"),str) and type(x.get("call_long")) is int and type(x.get("put_long")) is int}
    history=[by_date[k] for k in sorted(by_date)][-120:]
    history_path.write_text(json.dumps(history,indent=2)+"\\n")
    out.write_text(json.dumps(snapshot,indent=2)+"\n")
    print("Saved NSE Client index option long OI",snapshot["date"])
else:
    # Do not overwrite valid prior observations with fabricated zeros.
    print("NSE report unavailable; retained existing snapshot. "+("; ".join(errors[:2])))
