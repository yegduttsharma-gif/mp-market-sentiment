"""Collect attributable public Reddit replies via approved OAuth access, with RSS fallback."""
import json, os, re, time, urllib.request, urllib.parse, urllib.error, xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
A="{http://www.w3.org/2005/Atom}"
communities=["IndianStockMarket","IndianStreetBets","StockMarketIndia","IndianStocks","DalalStreetTalks"]
ua=os.getenv("REDDIT_USER_AGENT","script:pdmp-market-sentiment:1.1 (public sentiment research)")
comments=[];posts=[];errors=[];seen=set()
def request(url,headers=None,data=None):
 req=urllib.request.Request(url,data=data,headers=headers or {"User-Agent":ua})
 with urllib.request.urlopen(req,timeout=15) as r:return r.read(2000000)
def oauth_token():
 cid=os.getenv("REDDIT_CLIENT_ID");secret=os.getenv("REDDIT_CLIENT_SECRET")
 if not cid or not secret:return None
 import base64
 auth=base64.b64encode((cid+":"+secret).encode()).decode()
 payload=urllib.parse.urlencode({"grant_type":"client_credentials"}).encode()
 response=json.loads(request("https://www.reddit.com/api/v1/access_token",{"Authorization":"Basic "+auth,"User-Agent":ua,"Content-Type":"application/x-www-form-urlencoded"},payload))
 return response.get("access_token")
def add_comment(body,author,url,post_title,published,comment_id,post_url):
 if not body or len(body.strip())<12 or author.lower() in ("automoderator","[deleted]","[removed]") or comment_id in seen:return
 seen.add(comment_id)
 comments.append({"platform":"Reddit","type":"public_reply","text":body[:1500],"published":published,"url":url,"post_title":post_title,"post_url":post_url,"author":author,"comment_id":comment_id})
def walk(nodes,post):
 for node in nodes:
  if node.get("kind")!="t1":continue
  d=node.get("data",{})
  url="https://www.reddit.com"+d.get("permalink","")
  add_comment(d.get("body",""),d.get("author",""),url,post["title"],datetime.fromtimestamp(d.get("created_utc",0),timezone.utc).isoformat(),d.get("name",d.get("id","")),post["url"])
  replies=d.get("replies")
  if isinstance(replies,dict):walk(replies.get("data",{}).get("children",[]),post)
token=None
try:token=oauth_token()
except Exception as e:errors.append({"source":"oauth","error":type(e).__name__})
if token:
 headers={"Authorization":"bearer "+token,"User-Agent":ua,"Accept":"application/json"}
 for community in communities:
  try:
   url="https://oauth.reddit.com/r/"+community+"/new?limit=25&raw_json=1"
   listing=json.loads(request(url,headers))
   for node in listing.get("data",{}).get("children",[])[:15]:
    d=node.get("data",{})
    if d.get("id") and not d.get("over_18") and not d.get("stickied"):
     posts.append({"id":d["id"],"title":d.get("title",""),"url":"https://www.reddit.com"+d.get("permalink",""),"community":community})
  except Exception as e:errors.append({"source":community,"error":type(e).__name__})
 unique={p["id"]:p for p in posts};posts=list(unique.values())
 for post in posts[:35]:
  try:
   url="https://oauth.reddit.com/r/"+post["community"]+"/comments/"+post["id"]+"?limit=100&depth=4&sort=new&raw_json=1"
   response=json.loads(request(url,headers))
   if isinstance(response,list) and len(response)>1:walk(response[1].get("data",{}).get("children",[]),post)
  except Exception as e:errors.append({"source":post["url"],"error":type(e).__name__})
  time.sleep(0.3)
else:
 headers={"User-Agent":ua,"Accept":"application/atom+xml,application/rss+xml"}
 for community in communities:
  try:
   root=ET.fromstring(request("https://www.reddit.com/r/"+community+"/new/.rss?limit=25",headers))
   for e in root.findall(A+"entry")[:12]:
    el=e.find(A+"link");url=el.get("href","") if el is not None else ""
    if re.match(r"^https://www.reddit.com/r/[^/]+/comments/[a-z0-9]+/",url):posts.append({"title":e.findtext(A+"title",""),"url":url,"community":community})
  except Exception as e:errors.append({"source":community,"error":type(e).__name__})
 for post in posts[:32]:
  try:
   root=ET.fromstring(request(post["url"].rstrip("/")+"/.rss?limit=100",headers))
   for e in root.findall(A+"entry"):
    el=e.find(A+"link");url=el.get("href","") if el is not None else ""
    if "/comment/" not in url:continue
    raw=e.findtext(A+"content","") or ""
    body=re.sub(r"\\s+"," ",re.sub(r"<[^>]+>"," ",raw)).strip()
    author=e.find(A+"author");username=author.findtext(A+"name","") if author is not None else ""
    add_comment(body,username,url,post["title"],e.findtext(A+"updated",""),e.findtext(A+"id",url),post["url"])
  except Exception as e:errors.append({"source":post["url"],"error":type(e).__name__})
out={"collected_at":datetime.now(timezone.utc).isoformat(),"platform":"Reddit","collection_type":"actual_public_replies","access_method":"oauth" if token else "public_rss","post_count":len(posts),"comment_count":len(comments),"comments":comments[:2000],"errors":errors[:30],"status":"available" if comments else "unavailable_or_no_public_replies"}
Path("reddit_comments.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\\n")
print("Reddit",out["access_method"],"replies",len(comments),"posts",len(posts),"errors",len(errors))
