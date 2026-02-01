"""
Multi-Source Data Fetcher
Tries multiple APIs and ticker formats to ensure we get data for ANY stock
"""
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time

def get_stock_data_multi_source(ticker: str):
    """
    Try multiple strategies to get stock data:
    1. Yahoo Finance with original ticker
    2. Try alternative ticker formats (.NS, .BO, etc.)
    3. NSE India API for Indian stocks
    4. Web scraping as last resort
    """
    
    # Strategy 1: Try Yahoo Finance with original ticker
    result = try_yfinance(ticker)
    if result and result.get("has_data"):
        print(f"✅ Got data from Yahoo Finance for {ticker}")
        return result
    
    # Strategy 2: Try alternative ticker formats for Indian stocks
    if not ticker.endswith(('.NS', '.BO')):
        alternatives = [
            f"{ticker}.NS",  # NSE (National Stock Exchange)
            f"{ticker}.BO",  # BSE (Bombay Stock Exchange)
        ]
        for alt_ticker in alternatives:
            result = try_yfinance(alt_ticker)
            if result and result.get("has_data"):
                print(f"✅ Got data from Yahoo Finance using {alt_ticker}")
                result["ticker"] = ticker  # Keep original ticker
                result["actual_ticker"] = alt_ticker
                return result
    
    # Strategy 3: Try NSE India API for Indian stocks
    if ticker.endswith('.NS') or ticker.endswith('.BO'):
        result = try_nse_india(ticker.replace('.NS', '').replace('.BO', ''))
        if result and result.get("has_data"):
            print(f"✅ Got data from NSE India for {ticker}")
            return result
    
    # Strategy 4: Return whatever partial data we have
    print(f"⚠️ Limited data available for {ticker}")
    return get_basic_data(ticker)


def try_yfinance(ticker: str, max_retries=3):
    """Try to fetch data from Yahoo Finance with retries"""
    for attempt in range(max_retries):
        try:
            time.sleep(0.5 * (attempt + 1))  # Exponential backoff
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Check if we got meaningful data
            has_name = info.get("longName") or info.get("shortName")
            has_sector = info.get("sector")
            has_market_cap = info.get("marketCap")
            
            if has_name or has_sector or has_market_cap:
                return {
                    "ticker": ticker,
                    "info": info,
                    "stock": stock,
                    "has_data": True,
                    "source": "Yahoo Finance"
                }
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {ticker}: {str(e)}")
            if attempt == max_retries - 1:
                return None
    
    return None


def try_nse_india(symbol: str):
    """
    Try to fetch data from NSE India official API
    Works for Indian stocks without .NS/.BO suffix
    """
    try:
        # NSE India API endpoint
        base_url = "https://www.nseindia.com/api/quote-equity"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # First get the session cookies
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        time.sleep(1)
        
        # Now fetch the data
        params = {'symbol': symbol.upper()}
        response = session.get(base_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant info
            info_data = data.get("info", {})
            metadata = data.get("metadata", {})
            price_info = data.get("priceInfo", {})
            
            return {
                "ticker": f"{symbol}.NS",
                "info": {
                    "longName": info_data.get("companyName", metadata.get("companyName")),
                    "symbol": symbol,
                    "sector": metadata.get("sector", "N/A"),
                    "industry": metadata.get("industry", "N/A"),
                    "currentPrice": price_info.get("lastPrice", 0),
                    "marketCap": price_info.get("marketCap", "N/A"),
                },
                "stock": None,
                "has_data": True,
                "source": "NSE India"
            }
    except Exception as e:
        print(f"NSE India API failed for {symbol}: {str(e)}")
        return None


def get_basic_data(ticker: str):
    """Return minimal data structure when all sources fail"""
    return {
        "ticker": ticker,
        "info": {
            "longName": ticker,
            "symbol": ticker,
            "sector": "N/A",
            "industry": "N/A",
            "currentPrice": 0,
        },
        "stock": None,
        "has_data": False,
        "source": "None"
    }


def enhance_stock_info(ticker: str):
    """
    Enhanced stock info fetcher that tries multiple sources
    Returns: (info_dict, stock_object, source_name)
    """
    result = get_stock_data_multi_source(ticker)
    
    if result:
        return (
            result.get("info", {}),
            result.get("stock"),
            result.get("source", "Unknown"),
            result.get("actual_ticker", ticker)
        )
    
    return ({}, None, "None", ticker)
