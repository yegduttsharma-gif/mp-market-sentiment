"""Conservative Indian retail forum direction detection (English, Hindi, Hinglish)."""
import re
BULL=[
 r"\\b(?:bullish|buy on dips|upside ahead|going higher|remain bullish)\\b",
 r"\\b(?:nifty|bank\\s*nifty|banknifty|sensex|kpit|market|index)\\b.{0,45}\\b(?:upar\\s+(?:jayega|jaega|jayegi)|badhega|badhegi|chadhega|chadhegi|rally\\s+(?:aayegi|ayegi)|bounce\\s+(?:aayega|ayega))\\b",
 r"\\b(?:i\\s+(?:am|remain)\\s+bullish|i\\s+expect\\s+(?:a\\s+)?(?:rise|rally|bounce)|i\\s+(?:bought|am buying|will buy|am holding))\\b",
 r"\\b(?:ce|call)\\s*(?:buy|bought|holding|hold|long|liya|liye|kharida)\\b",
 r"\\b(?:buy|bought|holding|hold|long|liya|liye|kharida)\\s*(?:ce|call)\\b",
 r"(?:बढ़ेगा|बढ़ेगी|ऊपर जाएगा|ऊपर जाएगी|तेजी आएगी)"
]
BEAR=[
 r"\\b(?:bearish|downside ahead|going lower|remain bearish|avoid buying)\\b",
 r"\\b(?:nifty|bank\\s*nifty|banknifty|sensex|kpit|market|index)\\b.{0,45}\\b(?:girega|giregi|neeche\\s+(?:jayega|jaega)|crash\\s+(?:hoga|ayega)|girne\\s+wala)\\b",
 r"\\b(?:i\\s+(?:am|remain)\\s+bearish|i\\s+expect\\s+(?:a\\s+)?(?:fall|crash|drop)|i\\s+(?:sold|am selling|will sell|am short))\\b",
 r"\\b(?:pe|put)\\s*(?:buy|bought|holding|hold|long|liya|liye|kharida)\\b",
 r"\\b(?:buy|bought|holding|hold|long|liya|liye|kharida)\\s*(?:pe|put)\\b",
 r"(?:गिरेगा|गिरेगी|नीचे जाएगा|नीचे जाएगी|मंदी आएगी)"
]
B=[re.compile(x,re.I) for x in BULL]
D=[re.compile(x,re.I) for x in BEAR]
QUESTION=re.compile(r"\\b(?:should i|can i|shall i|what if|whether|how to|is it good to|kya\\s+(?:karu|kare|hoga)|buy or sell)\\b",re.I)
HISTORIC=re.compile(r"\\b(?:yesterday|last week|last month|previously|had risen|had fallen)\\b",re.I)
def direction(text):
 text=re.sub(r"\\s+"," ",text or "").strip()
 if not text or QUESTION.search(text) or "?" in text or HISTORIC.search(text):return "neutral"
 up=any(p.search(text) for p in B)
 down=any(p.search(text) for p in D)
 return "bullish" if up and not down else "bearish" if down and not up else "neutral"
