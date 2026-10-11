"""Read limited public TradingQnA posts; publish directional author counts, not comments."""
import json,re,html,urllib.request,urllib.parse
from pathlib import Path
from datetime import datetime,timezone,timedelta
BASE="https://www.tradingqna.com";now=datetime.now(timezone.utc)
ASSETS={"NIFTY 50":r"\b(?:nifty\s*50|nifty50|nifty index|nifty)\b","BANK NIFTY":r"\b(?:bank\s*nifty|banknifty|nifty\s*bank)\b","SENSEX":r"\b(?:sensex|bse\s*sensex)\b","KPIT":r"\bkpit\b"}
UP=re.compile(r"\b(?:i am bullish|i'm bullish|i expect (?:a )?(?:rise|rally|bounce)|i (?:bought|am buying|will buy|am holding|remain bullish)|my target is higher|going higher|upside ahead|buy on dips)\b",re.I)
DOWN=re.compile(r"\b(?:i am bearish|i'm bearish|i expect (?:a )?(?:fall|crash|drop)|i (?:sold|am selling|will sell|am short|remain bearish)|going lower|downside ahead|avoid buying)\b",re.I)
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":"PDMP-Research/1.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=18) as r:return json.load(r)
out={"collected_at":now.isoformat(),"platform":"TradingQnA","method":"public_forum_unique_author_explicit_direction_v1","source_health":{},"assets":{},"posts_checked":0}
posts=[]
try:
 listing=get(BASE+"/latest.json");topics=listing.get("topic_list",{}).get("topics",[])[:10]
 out["source_health"]["latest"]={"status":"ok","topics":len(topics)}
except Exception as e:
 topics=[];out["source_health"]["latest"]={"status":"unavailable","error":type(e).__name__}
# Search public posts for index-specific topics; gracefully retain latest fallback.
search_health={}
known={str(t["id"]):t for t in topics}
for term in ("nifty","bank nifty","sensex","kpit"):
 try:
  result=get(BASE+"/search.json?"+urllib.parse.urlencode({"q":term+" order:latest"}))
  found=result.get("topics",[])
  for topic in found[:12]:
   if topic.get("id"):known[str(topic["id"])]=topic
  search_health[term]={"status":"ok","topics":len(found)}
 except Exception as e:search_health[term]={"status":"unavailable","error":type(e).__name__}
topics=list(known.values())[:45]
out["source_health"]["targeted_search"]=search_health
errors=0
for t in topics:
 try:
  d=get(BASE+"/t/"+str(t["id"])+".json")
  for p in d.get("post_stream",{}).get("posts",[])[:35]:
   author=p.get("username") or ""
   if not author or author.lower() in ("system","discobot"):continue
   dt=datetime.fromisoformat((p.get("created_at") or "").replace("Z","+00:00"))
   if now-dt>timedelta(days=30):continue
   body=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]*>"," ",p.get("cooked","")))).strip()
   if len(body)<20:continue
   posts.append({"text":body[:2500],"author":author,"topic":t.get("title",""),"url":BASE+"/t/"+str(t["id"])+"/"+str(p.get("post_number",1))})
 except Exception:errors+=1
out["posts_checked"]=len(posts)
out["source_health"]["topics"]={"attempted":len(topics),"errors":errors}
for asset,pattern in ASSETS.items():
 votes={};neutral=0;sample=[]
 for p in posts:
  body=p["text"];title=p["topic"]
  if not re.search(pattern,body,re.I) and not re.search(pattern,title,re.I):continue
  if asset=="NIFTY 50" and re.search(ASSETS["BANK NIFTY"],title+" "+body,re.I) and not re.search(r"\bnifty\s*50\b",title+" "+body,re.I):continue
  up=bool(UP.search(body));down=bool(DOWN.search(body))
  if up==down:neutral+=1;continue
  stance="bullish" if up else "bearish"
  votes.setdefault(p["author"],set()).add(stance)
  if len(sample)<8:sample.append({"url":p["url"],"sentiment":stance})
 bull=sum(v=={"bullish"} for v in votes.values());bear=sum(v=={"bearish"} for v in votes.values())
 out["assets"][asset]={"bullish":bull,"bearish":bear,"neutral":neutral,"directional":bull+bear,"independent_authors":bull+bear,"conflicting_authors_excluded":sum(len(v)>1 for v in votes.values()),"evidence":sample}
out["status"]="collected" if posts else "no_public_posts_retrieved"
Path("tradingqna_sentiment.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("TradingQnA posts",len(posts),"errors",errors,"directional",sum(v["directional"] for v in out["assets"].values()))
