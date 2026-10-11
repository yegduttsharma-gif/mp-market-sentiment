"""Bounded official Hacker News API discovery of Indian market discussions."""
import json,re,urllib.request,html
from datetime import datetime,timezone,timedelta
from pathlib import Path
BASE="https://hacker-news.firebaseio.com/v0/"
TERMS=re.compile(r"\b(?:nifty\s*50|bank\s*nifty|sensex|nse\s+india|bse\s+india|indian\s+(?:stocks|stock\s+market|equities|share\s+market))\b",re.I)
def get(path):
 req=urllib.request.Request(BASE+path,headers={"User-Agent":"PDMP-Research/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=12) as r:return json.load(r)
out={"collected_at":datetime.now(timezone.utc).isoformat(),"platform":"Hacker News","method":"official_api_limited_discovery_v1","status":"unavailable","stories_checked":0,"relevant_stories":0,"comments_checked":0,"directional_opinions_verified":0,"evidence":[]}
try:
 ids=get("newstories.json")[:100]
 for ident in ids:
  try:
   story=get("item/"+str(ident)+".json") or {}
   if story.get("type")!="story" or story.get("deleted"):continue
   out["stories_checked"]+=1
   title=html.unescape(re.sub(r"<[^>]+>"," ",story.get("title","")))
   if not TERMS.search(title+" "+story.get("text","")):continue
   out["relevant_stories"]+=1
   for cid in story.get("kids",[])[:20]:
    try:
     c=get("item/"+str(cid)+".json") or {}
     if c.get("type")!="comment" or c.get("deleted") or c.get("dead"):continue
     out["comments_checked"]+=1
     body=html.unescape(re.sub(r"<[^>]+>"," ",c.get("text","")))
     if not TERMS.search(body):continue
     out["evidence"].append({"url":"https://news.ycombinator.com/item?id="+str(cid),"author":c.get("by",""),"text":body[:500],"timestamp":c.get("time")})
    except Exception:pass
  except Exception:pass
 out["status"]="collected"
except Exception as e:out["error"]=type(e).__name__
# Discovery only: no unvalidated stance classifier, no addition to investor totals.
Path("hackernews_discovery.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print("HN discovery",out["status"],out["stories_checked"],out["relevant_stories"],out["comments_checked"])
