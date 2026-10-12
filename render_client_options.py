"""Embed latest verified NSE client option data in static HTML for browsers without JS."""
import json,re,html
from pathlib import Path
data=json.loads(Path("client_options.json").read_text())
date=data["date"];ce=int(data["call_long"]);pe=int(data["put_long"]);total=ce+pe
if total<=0 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date):raise ValueError("Invalid NSE report")
def fmt(n):return f"{n:,}".replace(",","_") if False else format(n,",")
def indian(n):
 s=str(n)
 return s if len(s)<=3 else (s[:-3][-2:] if False else (lambda a:a[0]+("," if a[0] else "")+",".join(a[1]) )( (s[:-3][:len(s[:-3])%2], [s[:-3][i:i+2] for i in range(len(s[:-3])%2,len(s[:-3]),2)]+[s[-3:]]) ))
# Use locale-independent Indian digit grouping.
def group(n):
 s=str(n)
 if len(s)<=3:return s
 prefix=s[:-3];parts=[]
 while prefix:parts.insert(0,prefix[-2:]);prefix=prefix[:-2]
 return ",".join(parts+[s[-3:]])
body=f'<p class="muted">NSE report date: <strong>{html.escape(date)}</strong></p><div class="grid"><div><div class="muted">CE Long (held)</div><div class="number green">{group(ce)}</div><strong>{100*ce/total:.1f}%</strong></div><div><div class="muted">PE Long (held)</div><div class="number red">{group(pe)}</div><strong>{100*pe/total:.1f}%</strong></div></div><p class="muted">Verified end-of-day NSE Client positions; not live trades.</p>'
p=Path("client_options.html");source=p.read_text()
updated,n=re.subn(r'<!-- NSE_STATIC_START -->.*?<!-- NSE_STATIC_END -->','<!-- NSE_STATIC_START -->'+body+'<!-- NSE_STATIC_END -->',source,count=1,flags=re.S)
if n!=1:raise RuntimeError("Static NSE report markers missing")
updated=re.sub(r'(<div class="card muted" id="freshness">).*?(</div>)',lambda m:m.group(1)+'Latest verified report: '+date+' · End-of-day positions.'+m.group(2),updated,count=1,flags=re.S)
p.write_text(updated)
print("Static NSE report rendered:",date)
