from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import requests
import pandas as pd

app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants as of April 2026
BTC_HOLDINGS = 762099  # Current total BTC in MSTR treasury
SHARES_OUTSTANDING = 325230000 # Approximate current share count

@app.get("/api/indicator")
def get_mstr_indicator():
    # 1. Fetch MSTR Stock Price
    mstr = yf.Ticker("MSTR")
    mstr_price = mstr.history(period="1d")['Close'].iloc[-1]
    
    # 2. Fetch BTC Price
    btc_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    btc_response = requests.get(btc_url).json()
    btc_price = btc_response['bitcoin']['usd']
    
    # 3. Calculate NAV and Premium
    market_cap = mstr_price * SHARES_OUTSTANDING
    btc_value_in_treasury = BTC_HOLDINGS * btc_price
    premium_to_nav = market_cap / btc_value_in_treasury

    return {
        "mstr_price": round(mstr_price, 2),
        "btc_price": round(btc_price, 2),
        "premium_to_nav": round(premium_to_nav, 4),
        "timestamp": pd.Timestamp.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)