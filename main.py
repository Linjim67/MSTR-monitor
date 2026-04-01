from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import requests
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Current MicroStrategy Stats (April 1, 2026)
BTC_HOLDINGS = 762099  
SHARES_OUTSTANDING = 325230000 

@app.get("/")
def read_root():
    return {"message": "MSTR API is live. Use /api/indicator for data."}

@app.get("/api/indicator")
def get_mstr_indicator():
    try:
        # Fetch MSTR Stock
        mstr = yf.Ticker("MSTR")
        mstr_price = mstr.history(period="1d")['Close'].iloc[-1]
        
        # Fetch BTC Price
        btc_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        btc_response = requests.get(btc_url).json()
        btc_price = btc_response['bitcoin']['usd']
        
        # NAV Calculation
        market_cap = mstr_price * SHARES_OUTSTANDING
        btc_value = BTC_HOLDINGS * btc_price
        premium_to_nav = market_cap / btc_value

        return {
            "mstr_price": round(mstr_price, 2),
            "btc_price": round(btc_price, 2),
            "premium_to_nav": round(premium_to_nav, 4),
            "timestamp": pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)