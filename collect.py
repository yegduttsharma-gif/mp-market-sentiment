"""Collect public Google News RSS headlines; standard library only."""
import json, re, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from collections import Counter
QUERIES={"NIFTY 50":"Nifty 50 Indian stock market","SENSEX":"BSE Sensex stock market","BANK NIFTY":"Bank Nifty banking index","GOLD":"gold price bullion markets","CRUDE OIL":"crude oil Brent WTI prices","BITCOIN":"Bitcoin BTC cryptocurrency price market sentiment"}
UP=set("rise rises rising rally rallies rallied gain gains gained higher surge surges surging jump jumps jumped bullish optimism optimistic rebound rebounds recovered recovery strength strong upside soar soars".split())
DOWN=set("fall falls falling decline declines declined drop drops dropped slump slumps slumped lower bearish pessimism pessimistic crash crashes crashed weak weakness downside plunge plunges loss losses".split())
def classify(title):
    words=re.findall(r"[a-z]+",title.lower())
    a=sum(w in UP for w in words); b=sum(w in DOWN for w in words)
    return "bullish" if a>b else "bearish" if b>a else "neutral"
# Bitcoin-specific contextual phrases. Match multiword expressions before individual words.
BTC_UP_PHRASES=("etf inflows","etf inflow","net inflows","net inflow","institutional buying","buying pressure","short squeeze","short liquidations","short liquidation","breaks above","breakout above","price recovery","bullish momentum","new all time high")
BTC_DOWN_PHRASES=("etf outflows","etf outflow","net outflows","net outflow","institutional selling","selling pressure","long liquidations","long liquidation","breaks below","drops below","bearish momentum","price correction")
BTC_UP_WORDS=set("climb climbs climbed climbing recover recovers recovering rebounds rebounding advance advances advanced advancing rallies rallying uptick gains gaining inflows inflow accumulation breakout tops".split())
BTC_DOWN_WORDS=set("slip slips slipped slipping tumble tumbles tumbled tumbling sink sinks sank sinking retreat retreats retreated retreating selloff selloffs outflows outflow liquidation liquidations correction corrected correcting dip dips dipped dipping plunge plunges plunging".split())
def classify_bitcoin(title):
    text=" ".join(re.findall(r"[a-z]+",title.lower()))
    # Phrase scoring prevents 'ETF inflows' being missed and avoids treating 'short liquidations' as bearish.
    up=sum(text.count(p) for p in BTC_UP_PHRASES)
    down=sum(text.count(p) for p in BTC_DOWN_PHRASES)
    for p in BTC_UP_PHRASES+BTC_DOWN_PHRASES:
        text=text.replace(p," ")
    words=text.split()
    up+=sum(w in UP or w in BTC_UP_WORDS for w in words)
    down+=sum(w in DOWN or w in BTC_DOWN_WORDS for w in words)
    return "bullish" if up>down else "bearish" if down>up else "neutral"
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
        out.append({"title":title,"url":link,"source":item.findtext("source") or "Google News","published":published,"sentiment":classify_bitcoin(title) if query==QUERIES["BITCOIN"] else classify(title)})
    return out
try:
    prior=json.loads(Path("data.json").read_text(encoding="utf-8"))
except (FileNotFoundError,ValueError):
    prior={"markets":{}}
out={"updated_at":datetime.now(timezone.utc).isoformat(),"method":"headline_three_way_lexicon_v4_bitcoin_context","markets":{},"feed_status":{}}
success=0
for name,query in QUERIES.items():
    try:
        items=collect(query)
        if not items: raise ValueError("empty RSS response")
        success+=1
        out["feed_status"][name]="updated"
    except Exception as error:
        print(f"{name}: {type(error).__name__}: {error}")
        saved=prior.get("markets",{}).get(name)
        if saved:
            for item in saved.get("items",[]):
                item["sentiment"]=(classify_bitcoin(item.get("title","")) if name=="BITCOIN" else classify(item.get("title","")))
            counts=Counter(item["sentiment"] for item in saved.get("items",[]))
            saved.update({"bullish":counts["bullish"],"bearish":counts["bearish"],"neutral":counts["neutral"]})
            out["markets"][name]=saved
            out["feed_status"][name]="retained_previous_snapshot"
            continue
        items=[]
        out["feed_status"][name]="unavailable"
    counts=Counter(x["sentiment"] for x in items)
    out["markets"][name]={"bullish":counts["bullish"],"bearish":counts["bearish"],"neutral":0,"sources":len({x["source"] for x in items}),"items":items}
    print(name,len(items))
if success==0:
    print("WARNING: All RSS feeds unavailable; preserving last saved headline snapshot.")
    if prior.get("markets"):
        out["markets"]=prior["markets"]
        for name,market in out["markets"].items():
            for item in market.get("items",[]):
                item["sentiment"]=classify(item.get("title",""))
            counts=Counter(item["sentiment"] for item in market.get("items",[]))
            market.update({"bullish":counts["bullish"],"bearish":counts["bearish"],"neutral":0})
        out["feed_status"]={name:"retained_previous_snapshot" for name in QUERIES}
        out["updated_at"]=prior.get("updated_at",out["updated_at"])
    else:
        print("WARNING: No prior news data available.")
out["updated_markets"]=success
out["collected_at"]=out["updated_at"]
Path("data.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
