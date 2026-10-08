# PDMP — Public Market Psychology

Free mobile-friendly headline sentiment dashboard for Nifty 50, Sensex, Bank Nifty, Gold, Crude Oil.

## Publish
In repository Settings → Pages, select Deploy from a branch → main → /(root) → Save.
Expected site: https://yegduttsharma-gif.github.io/mp-market-sentiment/

## Get real public data
Open Actions → Update public sentiment → Run workflow. GitHub Actions also attempts scheduled collection twice hourly. Scheduled jobs can be delayed or paused. Check the timestamp on the site.

## Limitations
Version 1 scores only public news headlines, NOT actual retail or influencer consensus. The keyword model is simplistic, cannot reliably handle negation or context, and cannot infer price direction for other assets. No technical indicators, no paid APIs, and no trade recommendations. RSS availability may change. Missing or stale snapshots are clearly labeled.
