"""Classify attributable Reddit replies with same rules as YouTube comments."""
import json
from pathlib import Path
from youtube_retail import classify,ASSETS
p=Path("reddit_comments.json")
if not p.exists():raise SystemExit("Reddit comments snapshot missing")
d=json.loads(p.read_text())
comments=[]
for c in d.get("comments",[]):
 row=dict(c,video_title=c.get("post_title",""))
 item=classify(row)
 item.pop("video_title",None)
 comments.append(item)
assets={}
for name in ASSETS:
 relevant=[c for c in comments if name in c.get("asset_tags",[])]
 bull=sum(c["sentiment"]=="bullish" for c in relevant)
 bear=sum(c["sentiment"]=="bearish" for c in relevant)
 assets[name]={"bullish":bull,"bearish":bear,"neutral":len(relevant)-bull-bear,"directional":bull+bear,"evidence":[c for c in relevant if c["sentiment"]!="neutral"][:100]}
out={"collected_at":d.get("collected_at"),"platform":"Reddit","method":"position_and_expectation_v1","comment_count":len(comments),"directional_count":sum(c["sentiment"]!="neutral" for c in comments),"assets":assets,"comments":comments,"source_errors":d.get("errors",[])}
Path("reddit_retail.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("Reddit classified",out["directional_count"],"directional of",len(comments))
