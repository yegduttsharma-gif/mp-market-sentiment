"""Store dated India VIX checkpoints without mislabeling stale quotes as live."""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta, time
IST=timezone(timedelta(hours=5,minutes=30))
p=Path("vix_history.json")
try: h=json.loads(p.read_text(encoding="utf-8"))
except (FileNotFoundError,ValueError): h={"sessions":{}}
h.setdefault("sessions",{})
snapshot=json.loads(Path("market.json").read_text(encoding="utf-8"))
now=datetime.now(IST)
quotes=snapshot.get("quotes",{})
def local_quote(key):
    q=quotes.get(key)
    if not q or not q.get("as_of") or not isinstance(q.get("value"),(int,float)): return None
    t=datetime.fromisoformat(q["as_of"]).astimezone(IST)
    if t.date()!=now.date() or now-t>timedelta(minutes=45) or t>now+timedelta(minutes=2): return None
    return q
if now.weekday()<5:
    v=local_quote("vix")
    n=local_quote("nifty")
    s=local_quote("sensex")
    if v:
        day=now.date().isoformat()
        session=h["sessions"].setdefault(day,{"checkpoints":[]})
        # The quote provider's previous_close is a reported previous-session close,
        # NOT our own independently verified official exchange close.
        if isinstance(v.get("previous_close"),(int,float)) and v["previous_close"]>0:
            session["previous_vix_close_reported"]=v["previous_close"]
        if time(9,15)<=now.time()<=time(16,15):
            stamp=v["as_of"]
            if not any(x["vix_as_of"]==stamp for x in session["checkpoints"]):
                session["checkpoints"].append({"collected_at":now.isoformat(),"vix":v["value"],"vix_as_of":stamp,"nifty":n["value"] if n else None,"sensex":s["value"] if s else None,"nifty_as_of":n["as_of"] if n else None,"sensex_as_of":s["as_of"] if s else None})
            if now.time()>=time(15,30):
                session["closing_session_vix_observed"]={"value":v["value"],"as_of":stamp}
        print("Stored VIX checkpoint",day,stamp)
    else: print("No fresh same-day VIX quote: keeping existing history")
h["sessions"]=dict(sorted(h["sessions"].items())[-40:])
p.write_text(json.dumps(h,indent=2),encoding="utf-8")
