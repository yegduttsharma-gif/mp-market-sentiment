"""Quota-aware YouTube public viewer-comment refresh. Discovery every 6 hours; comments every 15 minutes."""
import json,os,re,time,html,urllib.parse,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path
KEY=os.getenv("YOUTUBE_API_KEY","").strip()
if not KEY:raise SystemExit("YOUTUBE_API_KEY secret missing")
API="https://www.googleapis.com/youtube/v3/"
OUT=Path("youtube_comments.json")
old={}
if OUT.exists():
 try:old=json.loads(OUT.read_text())
 except (ValueError,OSError):pass
now=datetime.now(timezone.utc)
queries=["nifty 50 tomorrow prediction hindi","bank nifty tomorrow CE PE analysis","sensex tomorrow market prediction","nifty option traders public opinion","indian stock market stocks analysis hindi","kpit stock analysis"]
def call(endpoint,params):
 url=API+endpoint+"?"+urllib.parse.urlencode(dict(params,key=KEY))
 with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"PDMP-Public-Research/1.0"}),timeout=25) as response:return json.load(response)
def date(s):
 try:return datetime.fromisoformat(s.replace("Z","+00:00"))
 except (ValueError,AttributeError):return datetime(1970,1,1,tzinfo=timezone.utc)
videos={v["id"]:v for v in old.get("videos",[]) if v.get("id")}
errors=[];discovered=0
last=date(old.get("last_discovery_at"))
discover=(now-last).total_seconds()>=6*3600 or not videos
if discover:
 for query in queries:
  try:
   result=call("search",{"part":"snippet","q":query,"type":"video","order":"date","maxResults":15,"regionCode":"IN","publishedAfter":(now-timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")})
   for v in result.get("items",[]):
    vid=v.get("id",{}).get("videoId")
    if not vid:continue
    if vid not in videos:discovered+=1
    videos[vid]={"id":vid,"title":html.unescape(v.get("snippet",{}).get("title","")),"url":"https://www.youtube.com/watch?v="+vid,"published":v.get("snippet",{}).get("publishedAt","")}
  except Exception as e:errors.append({"query":query,"error":type(e).__name__})
# Keep fresh video set; poll newest first, rotating through older videos as capacity allows.
videos={k:v for k,v in videos.items() if not v.get("published") or date(v["published"])>=now-timedelta(days=8)}
ordered=sorted(videos.values(),key=lambda v:v.get("published",""),reverse=True)[:65]
prior={c.get("comment_id"):c for c in old.get("comments",[]) if c.get("comment_id") and date(c.get("published"))>=now-timedelta(days=7)}
fresh=0;checked=0
for v in ordered:
 vid=v["id"]
 try:
  result=call("commentThreads",{"part":"snippet","videoId":vid,"maxResults":100,"order":"time","textFormat":"plainText"})
  checked+=1
  for t in result.get("items",[]):
   top=t.get("snippet",{}).get("topLevelComment",{});sn=top.get("snippet",{});cid=top.get("id")
   if not cid:continue
   body=html.unescape(re.sub(r"<[^>]*>"," ",sn.get("textDisplay") or sn.get("textOriginal") or "")).strip()
   if not body:continue
   if cid not in prior:fresh+=1
   prior[cid]={"platform":"YouTube","type":"viewer_comment","text":body[:1500],"published":sn.get("publishedAt"),"likes":sn.get("likeCount",0),"video_title":v["title"],"video_url":v["url"],"url":v["url"]+"&lc="+urllib.parse.quote(cid),"comment_id":cid,"author_channel_id":sn.get("authorChannelId",{}).get("value","")}
 except Exception as e:errors.append({"video":vid,"error":type(e).__name__})
comments=sorted(prior.values(),key=lambda c:c.get("published") or "",reverse=True)[:3000]
if not checked and errors:raise SystemExit("All YouTube comment requests failed; previous snapshot preserved")
out={"collected_at":now.isoformat(),"last_discovery_at":now.isoformat() if discover and not any("query" in e for e in errors) else old.get("last_discovery_at"),"platform":"YouTube","collection_type":"actual_public_viewer_comments","refresh_minutes":15,"discovery_hours":6,"video_count":len(videos),"videos_checked":checked,"new_videos":discovered,"new_comments":fresh,"comment_count":len(comments),"queries":queries,"videos":ordered,"comments":comments,"errors":errors[:30]}
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("YouTube viewer comments",len(comments),"new",fresh,"videos checked",checked,"errors",len(errors))
