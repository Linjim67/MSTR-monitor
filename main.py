from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import os
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2026 Constants
BTC_HOLDINGS = 762099
SHARES_OUTSTANDING = 325230000

@app.get("/api/history")
def get_history():
    # Retrieve 1-month historical data
    mstr_data = yf.Ticker("MSTR").history(period="1mo")['Close']
    btc_data = yf.Ticker("BTC-USD").history(period="1mo")['Close']

    df = pd.DataFrame({'mstr_price': mstr_data, 'btc_price': btc_data}).dropna()
    df['nav_per_share'] = (BTC_HOLDINGS * df['btc_price']) / SHARES_OUTSTANDING
    df['ratio'] = df['mstr_price'] / df['nav_per_share']
    
    # Format for Frontend
    history = []
    for date, row in df.iterrows():
        history.append({
            "date": date.strftime('%Y-%m-%d'),
            "mstr_price": round(row['mstr_price'], 2),
            "nav_per_share": round(row['nav_per_share'], 2),
            "ratio": round(row['ratio'], 4)
        })
    
    return history


genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3-flash-preview')


@app.get("/api/ai-summary")
def get_ai_summary():
    try:
        # 1. Get the latest data for context
        mstr = yf.Ticker("MSTR").history(period="1mo")
        btc = yf.Ticker("BTC-USD").history(period="1mo")
        
        current_mstr = round(mstr['Close'].iloc[-1], 2)
        current_btc = round(btc['Close'].iloc[-1], 2)
        
        # 2. Calculate current ratio
        nav_per_share = (762099 * current_btc) / 325230000
        ratio = current_mstr / nav_per_share
        status = "Premium" if ratio > 1 else "Discount"
        
        # 3. Construct the Prompt
        prompt = f"""
        Act as a professional crypto-equity analyst. Analyze the following MicroStrategy (MSTR) data:
        - Current MSTR Price: ${current_mstr}
        - Current BTC Price: ${current_btc}
        - Current Premium/Discount to NAV: {round(ratio, 4)} ({status})
        - Context: MSTR holds 762,099 BTC.
        
        Provide a 3-sentence summary:
        1. Explain what the current ratio means for investors.
        2. Analyze the relationship with Bitcoin price behavior.
        3. Provide a hypothesis on whether the stock is currently over or undervalued relative to its treasury.
        """
        
        response = model.generate_content(prompt)
        return {"summary": response.text}
        
    except Exception as e:
        return {"summary": "AI Insight currently unavailable. Please check API configuration."}


if __name__ == "__main__":
    import uvicorn
    # Read the PORT from environment variables, default to 8000 if not found
    port = int(os.environ.get("PORT", 8000)) 
    uvicorn.run(app, host="0.0.0.0", port=port)