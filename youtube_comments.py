"""Collect attributable public YouTube viewer comments (not video titles)."""
import json,os,re,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
KEY=os.getenv("YOUTUBE_API_KEY","").strip()
if not KEY: raise SystemExit("YOUTUBE_API_KEY secret missing")
API="https://www.googleapis.com/youtube/v3/"
queries=["nifty 50 stock market india","bank nifty market analysis hindi","indian stock market stocks analysis hindi","sensex share market today"]
def call(endpoint,params):
 params=dict(params,key=KEY)
 url=API+endpoint+"?"+urllib.parse.urlencode(params)
 req=urllib.request.Request(url,headers={"User-Agent":"PDMP-Public-Comment-Research/1.0"})
 with urllib.request.urlopen(req,timeout=25) as response:return json.load(response)
def clean(s):return re.sub(r"<[^>]*>"," ",s or "").strip()
items=[];videos=[];errors=[];seen=set()
for query in queries:
 try:
  results=call("search",{"part":"snippet","q":query,"type":"video","order":"date","maxResults":8,"regionCode":"IN","relevanceLanguage":"hi","publishedAfter":datetime.fromtimestamp(time.time()-7*86400,timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
  for video in results.get("items",[]):
   vid=video.get("id",{}).get("videoId")
   if not vid or vid in seen:continue
   seen.add(vid);title=video.get("snippet",{}).get("title","")
   videos.append({"id":vid,"title":title,"url":"https://www.youtube.com/watch?v="+vid})
   try:
    result=call("commentThreads",{"part":"snippet","videoId":vid,"maxResults":100,"order":"time","textFormat":"plainText"})
    for thread in result.get("items",[]):
     top=thread.get("snippet",{}).get("topLevelComment",{})
     snippet=top.get("snippet",{});body=clean(snippet.get("textDisplay") or snippet.get("textOriginal"))
     cid=top.get("id")
     if not body or not cid:continue
     items.append({"platform":"YouTube","type":"viewer_comment","text":body[:1500],"published":snippet.get("publishedAt"),"likes":snippet.get("likeCount",0),"video_title":title,"video_url":"https://www.youtube.com/watch?v="+vid,"url":"https://www.youtube.com/watch?v="+vid+"&lc="+urllib.parse.quote(cid),"comment_id":cid})
   except Exception as e:errors.append({"video":vid,"error":type(e).__name__})
  if len(videos)>=24:break
 except Exception as e:errors.append({"query":query,"error":str(e)[:160]})
out={"collected_at":datetime.now(timezone.utc).isoformat(),"platform":"YouTube","collection_type":"actual_public_viewer_comments","video_count":len(videos),"comment_count":len(items),"queries":queries,"videos":videos,"comments":items[:1800],"errors":errors[:30]}
Path("youtube_comments.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("YouTube public viewer comments",len(items),"videos",len(videos),"errors",len(errors))
if not videos and errors:raise SystemExit("YouTube API collection failed; see youtube_comments.json errors")
