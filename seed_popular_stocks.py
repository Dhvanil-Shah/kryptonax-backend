"""
Pre-seed cache with 50 popular stocks to avoid rate limiting
Run this locally to populate MongoDB with commonly searched stocks
"""
import time
from server import company_data_collection
from data_fetcher import enhance_stock_info
from quality_score import calculate_quality_score
from datetime import datetime

# Top 50 most searched stocks (US + Indian markets)
POPULAR_STOCKS = [
    # US Tech Giants
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    # US Finance
    "JPM", "BAC", "WFC", "GS", "C", "MS",
    # US Other
    "JNJ", "V", "PG", "UNH", "HD", "DIS", "NFLX", "COST", "PEP", "KO",
    # Indian Stocks (NSE)
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "WIPRO.NS",
    "BAJFINANCE.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS", "TATASTEEL.NS",
    # Indian Stocks (BSE)
    "RELIANCE.BO", "TCS.BO", "INFY.BO", "HDFCBANK.BO", "ICICIBANK.BO",
]

def cache_stock_data(ticker, delay=2):
    """Cache company history, board members, and quality score"""
    try:
        print(f"\n{'='*60}")
        print(f"Processing: {ticker}")
        print(f"{'='*60}")
        
        # 1. Company History
        print(f"Fetching company history...")
        info, stock, source, actual_ticker = enhance_stock_info(ticker)
        
        if info and info.get("longName"):
            history_data = {
                "ticker": ticker,
                "company_name": info.get("longName", ticker),
                "founded": info.get("founded", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "country": info.get("country", "N/A"),
                "website": info.get("website", "N/A"),
                "description": info.get("longBusinessSummary", "No description available"),
                "headquarters": f"{info.get('city', '')}, {info.get('state', '')}".strip(', '),
                "employees": info.get("fullTimeEmployees", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "beta": info.get("beta", "N/A")
            }
            
            company_data_collection.update_one(
                {"ticker": ticker, "type": "history"},
                {"$set": {"data": history_data, "timestamp": datetime.utcnow()}},
                upsert=True
            )
            print(f"✅ Cached company history for {ticker}")
        
        time.sleep(delay)
        
        # 2. Board Members (simplified - just cache basic structure)
        if info and info.get("companyOfficers"):
            board_data = {
                "ticker": ticker,
                "company_name": info.get("longName", ticker),
                "leadership": [],
                "board_members": [
                    {
                        "name": officer.get("name", "N/A"),
                        "title": officer.get("title", "N/A"),
                        "pay": officer.get("totalPay", 0),
                        "photo_url": f"https://ui-avatars.com/api/?name={officer.get('name', 'XX').replace(' ', '+')}&background=2962ff&color=fff&size=128"
                    }
                    for officer in info.get("companyOfficers", [])[:8]
                ],
                "board_size": len(info.get("companyOfficers", []))
            }
            
            company_data_collection.update_one(
                {"ticker": ticker, "type": "board"},
                {"$set": {"data": board_data, "timestamp": datetime.utcnow()}},
                upsert=True
            )
            print(f"✅ Cached board data for {ticker}")
        
        time.sleep(delay)
        
        # 3. Quality Score
        print(f"Calculating quality score...")
        quality_data = calculate_quality_score(ticker)
        
        if quality_data and "error" not in quality_data:
            company_data_collection.update_one(
                {"ticker": ticker, "type": "quality_score"},
                {"$set": {"data": quality_data, "timestamp": datetime.utcnow()}},
                upsert=True
            )
            print(f"✅ Cached quality score for {ticker}: {quality_data.get('overall_score')}/100 ({quality_data.get('grade')})")
        else:
            print(f"⚠️ Could not calculate quality score for {ticker}")
        
        print(f"✅ Completed {ticker}")
        return True
        
    except Exception as e:
        print(f"❌ Error caching {ticker}: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"Starting cache pre-seeding for {len(POPULAR_STOCKS)} stocks...")
    print("This will take approximately {:.0f} minutes".format(len(POPULAR_STOCKS) * 6 / 60))
    
    successful = 0
    failed = 0
    
    for i, ticker in enumerate(POPULAR_STOCKS, 1):
        print(f"\n[{i}/{len(POPULAR_STOCKS)}] Processing {ticker}...")
        if cache_stock_data(ticker, delay=2):
            successful += 1
        else:
            failed += 1
        
        # Extra delay between stocks to avoid rate limits
        if i < len(POPULAR_STOCKS):
            time.sleep(3)
    
    print(f"\n{'='*60}")
    print(f"Cache Seeding Complete!")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {successful/len(POPULAR_STOCKS)*100:.1f}%")
