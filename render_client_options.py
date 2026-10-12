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
history_path=Path("client_options_history.json")
try: history=json.loads(history_path.read_text())
except (ValueError,OSError):history=[]
previous=next((x for x in reversed(history) if x.get("date","")<date and x.get("call_long",0)+x.get("put_long",0)>0),None)
if previous:
 pc=int(previous["call_long"]);pp=int(previous["put_long"])
 ce_change=(ce-pc)*100/pc if pc else None
 pe_change=(pe-pp)*100/pp if pp else None
 prev_share=100*pc/(pc+pp)
 shift=100*ce/total-prev_share
 signal="Bullish shift" if shift>=1 else "Bearish shift" if shift<=-1 else "Neutral shift"
 tone="green" if shift>=1 else "red" if shift<=-1 else "muted"
 def delta(v):return "N/A" if v is None else f"{v:+.2f}%"
 body+=f'<div style="border-top:1px solid #405471;margin-top:16px;padding-top:14px"><strong>Change vs {html.escape(previous["date"])}</strong><div class="grid" style="margin-top:10px"><div class="muted">CE Long: <strong>{delta(ce_change)}</strong></div><div class="muted">PE Long: <strong>{delta(pe_change)}</strong></div></div><p><strong class="{tone}">{signal}</strong> · CE share change: {shift:+.2f} percentage points</p><p class="muted">Directional positioning shift, not a prediction. Neutral = change under 1 percentage point in either direction.</p></div>'
else:
 body+='<p class="muted">Daily % change and Bullish/Bearish/Neutral shift: awaiting a verified previous trading-day snapshot.</p>'
p=Path("client_options.html");source=p.read_text()
updated,n=re.subn(r'<!-- NSE_STATIC_START -->.*?<!-- NSE_STATIC_END -->','<!-- NSE_STATIC_START -->'+body+'<!-- NSE_STATIC_END -->',source,count=1,flags=re.S)
if n!=1:raise RuntimeError("Static NSE report markers missing")
updated=re.sub(r'(<div class="card muted" id="freshness">).*?(</div>)',lambda m:m.group(1)+'Latest verified report: '+date+' · End-of-day positions.'+m.group(2),updated,count=1,flags=re.S)
p.write_text(updated)
print("Static NSE report rendered:",date)
