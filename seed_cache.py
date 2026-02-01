import yfinance as yf
import pymongo
from datetime import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "")

client = pymongo.MongoClient(MONGO_URI)
db = client["kryptonax"]
company_data_collection = db["company_data"]

# Popular stocks to pre-cache
tickers_to_cache = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META",
    "BHEL.BO", "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", 
    "ICICIBANK.NS", "SBIN.NS", "WIPRO.NS", "LT.NS"
]

print("Starting to cache company data to MongoDB...")
print("=" * 60)

for ticker in tickers_to_cache:
    print(f"\nProcessing {ticker}...")
    try:
        time.sleep(2)  # Delay to avoid rate limits
        
        t = yf.Ticker(ticker)
        info = t.info
        
        if info and info.get("longName"):
            # Cache company history
            history_data = {
                "ticker": ticker,
                "company_name": info.get("longName", ticker),
                "founded": info.get("founded", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "country": info.get("country", "N/A"),
                "website": info.get("website", "N/A"),
                "description": info.get("longBusinessSummary", "No description available"),
                "headquarters": info.get("city", "") + ", " + info.get("state", ""),
                "employees": info.get("fullTimeEmployees", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "beta": info.get("beta", "N/A")
            }
            
            company_data_collection.update_one(
                {"ticker": ticker, "type": "history"},
                {"$set": {"data": history_data, "timestamp": datetime.utcnow()}},
                upsert=True
            )
            print(f"  ✅ Cached history for {info.get('longName')}")
            
            # Cache board members if available
            if "companyOfficers" in info and info["companyOfficers"]:
                officers = []
                for officer in info["companyOfficers"][:10]:
                    officers.append({
                        "name": officer.get("name", "N/A"),
                        "title": officer.get("title", "N/A"),
                        "pay": officer.get("totalPay", 0),
                        "photo_url": f"https://ui-avatars.com/api/?name={officer.get('name', 'NA').replace(' ', '+')}&background=random&size=128"
                    })
                
                board_data = {
                    "ticker": ticker,
                    "company_name": info.get("longName", ticker),
                    "leadership": officers[:2] if len(officers) >= 2 else [],
                    "board_members": officers[2:] if len(officers) > 2 else officers,
                    "board_size": len(officers)
                }
                
                company_data_collection.update_one(
                    {"ticker": ticker, "type": "board"},
                    {"$set": {"data": board_data, "timestamp": datetime.utcnow()}},
                    upsert=True
                )
                print(f"  ✅ Cached {len(officers)} board members")
        else:
            print(f"  ⚠️ No data available for {ticker}")
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

print("\n" + "=" * 60)
print(f"✅ Caching complete! Cached {len(tickers_to_cache)} companies to MongoDB")
print("Data will persist across server restarts and is valid for 24 hours")
