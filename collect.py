"""Collect public Google News RSS headlines; standard library only."""
import json, re, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from collections import Counter
QUERIES={"NIFTY 50":"Nifty 50 Indian stock market","SENSEX":"BSE Sensex stock market","BANK NIFTY":"Bank Nifty banking index","GOLD":"gold price bullion markets","CRUDE OIL":"crude oil Brent WTI prices"}
UP=set("rise rises rising rally rallies rallied gain gains gained higher surge surges surging jump jumps jumped bullish optimism optimistic rebound rebounds recovered recovery strength strong upside soar soars".split())
DOWN=set("fall falls falling decline declines declined drop drops dropped slump slumps slumped lower bearish pessimism pessimistic crash crashes crashed weak weakness downside plunge plunges loss losses".split())
def classify(title):
    words=re.findall(r"[a-z]+",title.lower())
    a=sum(w in UP for w in words); b=sum(w in DOWN for w in words)
    return "bullish" if a>b else "bearish" if b>a else "neutral"
def collect(query):
    q=urllib.parse.quote(query+" when:1d")
    url=f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    req=urllib.request.Request(url,headers={"User-Agent":"PDMP-research/1.0"})
    with urllib.request.urlopen(req,timeout=25) as response: root=ET.fromstring(response.read(1500000))
    out=[]; seen=set()
    for item in root.findall(".//item")[:80]:
        title=(item.findtext("title") or "").strip(); link=(item.findtext("link") or "").strip()
        if not title or not link or title.lower() in seen: continue
        seen.add(title.lower())
        date=item.findtext("pubDate") or ""
        try: published=parsedate_to_datetime(date).astimezone(timezone.utc).isoformat()
        except Exception: published=None
        out.append({"title":title,"url":link,"source":item.findtext("source") or "Google News","published":published,"sentiment":classify(title)})
    return out
out={"updated_at":datetime.now(timezone.utc).isoformat(),"method":"headline_lexicon_v1","markets":{}}
success=0
for name,query in QUERIES.items():
    try:
        items=collect(query); success+=1
    except Exception as error:
        print(f"{name}: {type(error).__name__}: {error}"); items=[]
    counts=Counter(x["sentiment"] for x in items)
    out["markets"][name]={"bullish":counts["bullish"],"bearish":counts["bearish"],"neutral":counts["neutral"],"sources":len({x["source"] for x in items}),"items":items}
    print(name,len(items))
if success==0: raise RuntimeError("All RSS fetches failed; preserving prior data.")
Path("data.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
