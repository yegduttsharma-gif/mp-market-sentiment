"""Check public TradingView Minds access; never infer retail votes from page availability."""
import json,re,urllib.request
from html.parser import HTMLParser
from datetime import datetime,timezone
from pathlib import Path
SOURCES={'NIFTY 50':'https://in.tradingview.com/symbols/NSE-NIFTY/community-minds/','BANK NIFTY':'https://in.tradingview.com/symbols/NSE-BANKNIFTY/community-minds/','SENSEX':'https://in.tradingview.com/symbols/BSE-SENSEX/community-minds/'}
class Visible(HTMLParser):
 def __init__(self):super().__init__();self.text=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.skip+=1
 def handle_endtag(self,tag):
  if tag in ('script','style') and self.skip:self.skip-=1
 def handle_data(self,data):
  if not self.skip:self.text.append(data)
out={'platform':'TradingView Minds','collected_at':datetime.now(timezone.utc).isoformat(),'method':'public_minds_page_access_only','included_in_retail_totals':False,'verified_directional_opinions':0,'sources':{}}
for name,url in SOURCES.items():
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; PDMP-Research/1.0)','Accept':'text/html'})
  with urllib.request.urlopen(req,timeout=18) as response:raw=response.read(1000000).decode('utf-8','replace');status=response.status
  parser=Visible();parser.feed(raw);visible=re.sub(r'\s+',' ',' '.join(parser.text)).strip()
  out['sources'][name]={'url':url,'status':'accessible' if status==200 and len(visible)>150 else 'insufficient_public_content','http_status':status,'visible_text_chars':len(visible),'contains_minds':bool(re.search(r'what traders are saying|community discussions|real-time market insights',visible,re.I))}
 except Exception as e:out['sources'][name]={'url':url,'status':'unavailable','error':type(e).__name__}
Path('tradingview_minds_discovery.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
