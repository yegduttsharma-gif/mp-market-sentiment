"""Conservative FrontPage public-post extraction; no invented votes."""
import json,re,urllib.request,html
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse
from pathlib import Path
from datetime import datetime,timezone
from forum_direction import direction
SOURCES={'stock_bets':'https://front.page/stock-bets','indices':'https://front.page/all-about-indices','comments':'https://front.page/comments','signals':'https://front.page/trading-systems-and-signals'}
ASSETS={'NIFTY 50':r'\b(?:nifty(?:\s*50)?|nifty50)\b','BANK NIFTY':r'\b(?:bank\s*nifty|banknifty|nifty\s*bank)\b','SENSEX':r'\bsensex\b','SBIN':r'\b(?:sbin|sbi)\b','RELIANCE':r'\breliance\b','INFY':r'\b(?:infy|infosys)\b','TCS':r'\btcs\b','HDFCBANK':r'\bhdfc\s*bank\b','ICICIBANK':r'\bicici\s*bank\b','KPIT':r'\bkpit\b'}
class Parse(HTMLParser):
 def __init__(self):super().__init__();self.stack=[];self.anchors=[];self.skip=0;self.visible=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag in ('script','style'):self.skip+=1
  if tag=='a' and not self.skip:self.stack.append({'href':d.get('href',''),'text':[]})
 def handle_endtag(self,tag):
  if tag=='a' and self.stack:
   a=self.stack.pop();a['text']=' '.join(a['text']).strip();self.anchors.append(a)
  if tag in ('script','style') and self.skip:self.skip-=1
 def handle_data(self,data):
  if self.skip:return
  self.visible.append(data)
  for a in self.stack:a['text'].append(data)
out={'platform':'FrontPage','collected_at':datetime.now(timezone.utc).isoformat(),'method':'linked_public_post_author_verification_v1','sources':{},'assets':{},'posts_checked':0,'verified_directional_opinions':0,'included_in_retail_totals':False}
links={}
for name,url in SOURCES.items():
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; PDMP-Research/1.0)','Accept':'text/html'})
  with urllib.request.urlopen(req,timeout=18) as response:raw=response.read(1100000).decode('utf-8','replace');status=response.status
  p=Parse();p.feed(raw);visible=re.sub(r'\s+',' ',' '.join(p.visible)).strip()
  for a in p.anchors:
   href=urljoin(url,a['href']);path=urlparse(href).path
   if urlparse(href).hostname not in ('front.page','www.front.page'):continue
   if re.fullmatch(r'/[a-zA-Z0-9_-]+/(?:\d{5,}|[A-Za-z0-9_-]{9,})/?',path) or re.fullmatch(r'/t/[A-Za-z0-9_-]{7,}/?',path):links[href]=True
  out['sources'][name]={'url':url,'status':'accessible' if status==200 else 'unavailable','http_status':status,'visible_text_chars':len(visible),'candidate_post_links':len(links)}
 except Exception as e:out['sources'][name]={'url':url,'status':'unavailable','error':type(e).__name__}
# Fetch a bounded sample of public individual post pages. A vote requires an
# explicit author and a clear directional statement in the same post record.
for link in list(links)[:18]:
 try:
  req=urllib.request.Request(link,headers={'User-Agent':'Mozilla/5.0 (compatible; PDMP-Research/1.0)'})
  with urllib.request.urlopen(req,timeout=12) as response:raw=response.read(700000).decode('utf-8','replace')
  p=Parse();p.feed(raw)
  # Plain page text includes comments, unrelated recommendations, and navigation.
  # Until an individual post's author/body boundary is reliably identified,
  # it is unsafe to assign direction to any user.
  out['posts_checked']+=1
 except Exception:pass
for asset in ASSETS:out['assets'][asset]={'bullish':0,'bearish':0,'directional':0,'evidence':[]}
out['candidate_post_links']=len(links)
out['extraction_status']='author_body_boundary_not_verified' if links else 'no_public_post_links_found'
Path('frontpage_discovery.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
