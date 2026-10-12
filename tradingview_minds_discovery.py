"""Extract only attributable, linked public TradingView Minds views."""
import json,re,urllib.request
from html.parser import HTMLParser
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlparse
from forum_direction import direction
SOURCES={'NIFTY 50':'https://in.tradingview.com/symbols/NSE-NIFTY/community-minds/','BANK NIFTY':'https://in.tradingview.com/symbols/NSE-BANKNIFTY/community-minds/','SENSEX':'https://in.tradingview.com/symbols/BSE-SENSEX/community-minds/'}
class Extract(HTMLParser):
 def __init__(self):
  super().__init__();self.anchors=[];self.stack=[];self.skip=0;self.visible=[]
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag in ('script','style'):self.skip+=1
  if tag=='a' and not self.skip:self.stack.append({'href':attrs.get('href',''),'text':[]})
 def handle_endtag(self,tag):
  if tag=='a' and self.stack:
   a=self.stack.pop();a['text']=' '.join(a['text']).strip();self.anchors.append(a)
  if tag in ('script','style') and self.skip:self.skip-=1
 def handle_data(self,data):
  if self.skip:return
  self.visible.append(data)
  for a in self.stack:a['text'].append(data)
out={'platform':'TradingView Minds','collected_at':datetime.now(timezone.utc).isoformat(),'method':'conservative_attributed_linked_minds_v1','sources':{},'assets':{},'verified_directional_opinions':0,'included_in_retail_totals':False}
for asset,url in SOURCES.items():
 opinions={};candidates=0
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; PDMP-Research/1.0)','Accept':'text/html'})
  with urllib.request.urlopen(req,timeout=18) as response:raw=response.read(1200000).decode('utf-8','replace');status=response.status
  p=Extract();p.feed(raw);visible=re.sub(r'\s+',' ',' '.join(p.visible)).strip()
  # Minds discussions must have an attributable individual post link.
  # A generic symbol page, user profile, navigation link or headline is not an opinion.
  for a in p.anchors:
   href=urljoin(url,a['href']);path=urlparse(href).path
   match=re.search(r'/minds/([A-Za-z0-9_-]{5,})/?$',path)
   if not match:continue
   body=re.sub(r'\s+',' ',a['text']).strip()
   if len(body)<25:continue
   candidates+=1
   # The anchor text alone does not prove who authored the view.
   # Do not count unattributed text or assume a post author.
  out['sources'][asset]={'url':url,'status':'accessible' if status==200 else 'unavailable','http_status':status,'visible_text_chars':len(visible),'post_link_candidates':candidates,'verified_authored_opinions':0}
 except Exception as e:out['sources'][asset]={'url':url,'status':'unavailable','error':type(e).__name__}
 out['assets'][asset]={'bullish':0,'bearish':0,'directional':0,'evidence':[]}
Path('tradingview_minds_discovery.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
