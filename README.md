# Amazon-ASN-Checking

Paste an Amazon.in `hidden-keywords` search URL and see which of its ASINs
don't show up in the search results.

## Running locally

```
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
streamlit run dashboard.py
```

## Proxy (needed on Streamlit Community Cloud)

Amazon blocks requests from Streamlit Community Cloud's datacenter IP range
outright (real `503` responses on every attempt), so the deployed app needs
to route through a residential/rotating proxy to get real results.

Set these in the app's **Settings → Secrets** (or in `.streamlit/secrets.toml`
locally, which is gitignored):

```toml
PROXY_SERVER = "http://proxy-host:port"
PROXY_USERNAME = "your-proxy-username"
PROXY_PASSWORD = "your-proxy-password"
```

`PROXY_USERNAME`/`PROXY_PASSWORD` are optional if your proxy provider doesn't
require auth. Without `PROXY_SERVER` set, the app connects directly — fine
for local runs from a residential IP, but likely to get blocked on Cloud.
