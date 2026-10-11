"""Public Reddit discussion replies; only attributable, linked comments are reported."""
import json,re,urllib.request,urllib.parse,xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
A="{http://www.w3.org/2005/Atom}"
communities=["IndianStockMarket","IndianStreetBets","StockMarketIndia","IndianStocks"]
headers={"User-Agent":"PDMPPublicSentiment/1.0 (public academic research)","Accept":"application/atom+xml,application/rss+xml"}
comments=[];posts=[];errors=[];seen=set()
def get(url):
 req=urllib.request.Request(url,headers=headers)
 with urllib.request.urlopen(req,timeout=12) as r:return ET.fromstring(r.read(1500000))
def link(entry):
 el=entry.find(A+"link")
 return el.get("href","") if el is not None else ""
for community in communities:
 try:
  root=get("https://www.reddit.com/r/"+community+"/new/.rss?limit=25")
  for e in root.findall(A+"entry")[:12]:
   url=link(e)
   if not re.match(r"^https://www.reddit.com/r/[^/]+/comments/[a-z0-9]+/",url):continue
   posts.append({"title":e.findtext(A+"title",""),"url":url,"community":community})
 except Exception as ex:errors.append({"source":community,"error":type(ex).__name__})
for post in posts[:32]:
 try:
  root=get(post["url"].rstrip("/")+"/.rss?limit=100")
  for e in root.findall(A+"entry"):
   url=link(e);id=e.findtext(A+"id","")
   if not url or url in seen or "/comment/" not in url:continue
   seen.add(url)
   raw=e.findtext(A+"content","") or ""
   text=re.sub(r"<[^>]+>"," ",raw)
   text=re.sub(r"\s+"," ",text).strip()
   if not text or len(text)<12:continue
   author=e.find(A+"author")
   username=author.findtext(A+"name","") if author is not None else ""
   if username.lower() in ("automoderator","[deleted]"):continue
   comments.append({"platform":"Reddit","type":"public_reply","text":text[:1500],"published":e.findtext(A+"updated",""),"url":url,"post_title":post["title"],"post_url":post["url"],"author":username,"comment_id":id})
 except Exception as ex:errors.append({"source":post["url"],"error":type(ex).__name__})
out={"collected_at":datetime.now(timezone.utc).isoformat(),"platform":"Reddit","collection_type":"actual_public_replies","post_count":len(posts),"comment_count":len(comments),"comments":comments[:2000],"errors":errors[:30],"status":"available" if comments else "no_public_replies_retrieved"}
Path("reddit_comments.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("Reddit replies",len(comments),"posts",len(posts),"errors",len(errors))
