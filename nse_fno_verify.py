"""Verify NSE F&O underlyings from NSE's official table; fail closed."""
import json,re,urllib.request
from html.parser import HTMLParser
from datetime import datetime,timezone
from pathlib import Path
URL="https://www.nseindia.com/static/products-services/equity-derivatives-list-underlyings-information"
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None
 def handle_starttag(self,t,a):
  if t=="tr":self.row=[]
  if t in ("td","th") and self.row is not None:self.cell=[]
 def handle_data(self,d):
  if self.cell is not None:self.cell.append(d)
 def handle_endtag(self,t):
  if t in ("td","th") and self.cell is not None:self.row.append(" ".join("".join(self.cell).split()));self.cell=None
  if t=="tr" and self.row is not None:self.rows.append(self.row);self.row=None
def main():
 try:
  req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept":"text/html"})
  with urllib.request.urlopen(req,timeout=25) as f:html=f.read(3000000).decode("utf-8","replace")
  p=Parser();p.feed(html);symbols=set()
  for row in p.rows:
   if len(row)!=3 or not row[0].strip().isdigit() or not row[1].strip():continue
   v=row[2].strip().upper()
   if re.fullmatch(r"[A-Z0-9][A-Z0-9&.-]{1,19}",v) and v not in {"NIFTY","BANKNIFTY","FINNIFTY","MIDCPNIFTY","NIFTYNXT50","NIFTYFPI"}:symbols.add(v)
  if len(symbols)<150:raise ValueError("Incomplete NSE table: "+str(len(symbols))+" symbols")
  Path("nse_fno_underlyings.json").write_text(json.dumps({"status":"verified","source":URL,"checked_at":datetime.now(timezone.utc).isoformat(),"count":len(symbols),"symbols":sorted(symbols)},indent=2)+"\n")
  print("NSE official underlying symbols:",len(symbols))
 except Exception as e:print("NSE verification unavailable; retaining previous verified snapshot:",e)
if __name__=="__main__":main()
