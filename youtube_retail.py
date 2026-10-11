"""Classify actual YouTube viewer comments into retail positions and expectations."""
import json,re,html
from pathlib import Path
src=Path("youtube_comments.json")
if not src.exists():raise SystemExit("youtube_comments.json missing")
data=json.loads(src.read_text())
ASSETS={"NIFTY 50":r"\b(?:nifty\s*50|nifty50|nifty)\b","BANK NIFTY":r"\b(?:bank\s*nifty|banknifty)\b","SENSEX":r"\b(?:sensex)\b","KPIT":r"\b(?:kpit|kpittechnologies|kpittech)\b"}
BUY=r"\b(?:bought|purchased|buying|accumulating|added|holding|hold|long|invested|buy\s+kar\s+liya|le\s+liya|liya\s+hai|kharid\s+liya|aur\s+lunga|buy\s+kiya|buy\s+hai|buying\s+hai)\b"
SELL=r"\b(?:sold|selling|exited|exit\s+kar|shorted|shorting|booked\s+loss|bech\s+diya|bech\s+raha|nikal\s+gaya|sell\s+kar\s+diya)\b"
UP=r"\b(?:bullish|will\s+(?:rise|go\s+up|rally)|going\s+(?:up|higher)|expect\s+(?:upside|rise|bounce)|breakout\s+(?:soon|ahead)|upar\s+(?:jayega|jaega)|badhega|rocket\s+banega)\b"
DOWN=r"\b(?:bearish|will\s+(?:fall|crash|drop)|going\s+(?:down|lower)|expect\s+(?:fall|crash)|breakdown\s+(?:soon|ahead)|girega|girne\s+wala|neeche\s+jayega)\b"
QUESTION=r"(?:\?|\b(?:should\s+i|can\s+i|what\s+if|kya\s+(?:karu|kare|hoga)|buy\s+karu|sell\s+karu|entry\s+lu|target\s+kya|please\s+(?:suggest|advise))\b)"
def classify(c):
 text=html.unescape(c.get("text","")).strip()
 title=html.unescape(c.get("video_title",""))
 low=text.lower()
 assets=[name for name,pat in ASSETS.items() if re.search(pat,low,re.I)]
 # A comment on a single named stock's video may refer to that stock implicitly.
 if not assets:
  matches=[name for name,pat in ASSETS.items() if re.search(pat,title,re.I)]
  if len(matches)==1:assets=matches
 if "BANK NIFTY" in assets and "NIFTY 50" in assets and not re.search(r"\bnifty\s*50\b",low,re.I):assets.remove("NIFTY 50")
 b=bool(re.search(BUY,low,re.I));s=bool(re.search(SELL,low,re.I))
 u=bool(re.search(UP,low,re.I));d=bool(re.search(DOWN,low,re.I))
 if re.search(QUESTION,low,re.I) or (b or u) and (s or d):stance="neutral";kind="question_or_mixed"
 elif b and not s and not d:stance="bullish";kind="positioning"
 elif s and not b and not u:stance="bearish";kind="positioning"
 elif u and not d:stance="bullish";kind="expectation"
 elif d and not u:stance="bearish";kind="expectation"
 else:stance="neutral";kind="discussion_or_noise"
 return dict(c,asset_tags=assets,sentiment=stance,evidence_type=kind)
comments=[classify(c) for c in data.get("comments",[])]
assets={}
for name in ASSETS:
 relevant=[c for c in comments if name in c["asset_tags"]]
 bull=sum(c["sentiment"]=="bullish" for c in relevant)
 bear=sum(c["sentiment"]=="bearish" for c in relevant)
 assets[name]={"bullish":bull,"bearish":bear,"neutral":len(relevant)-bull-bear,"directional":bull+bear,"bullish_pct":round(100*bull/(bull+bear)) if bull+bear else None,"evidence":[c for c in relevant if c["sentiment"]!="neutral"][:100]}
out={"collected_at":data.get("collected_at"),"method":"youtube_position_and_expectation_v1","platform":"YouTube","note":"Heuristic, nonrepresentative public-comment sample; a position is not a forecast","comment_count":len(comments),"directional_count":sum(c["sentiment"]!="neutral" for c in comments),"assets":assets,"comments":comments}
Path("youtube_retail.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print("YouTube classified",out["directional_count"],"directional of",len(comments))
