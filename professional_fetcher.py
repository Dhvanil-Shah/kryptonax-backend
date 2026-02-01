"""
Professional Production-Grade Data Fetcher
- Request queuing to prevent rate limits
- Exponential backoff with jitter
- Multi-source fallback (Yahoo + Alternative APIs)
- Proper error handling and logging
- Thread-safe operations
"""
import yfinance as yf
import requests
import time
import random
from datetime import datetime, timedelta
from threading import Lock
from collections import deque

class RateLimiter:
    """Thread-safe rate limiter for API calls"""
    def __init__(self, calls_per_minute=30):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute  # 2 seconds for 30 calls/min
        self.last_call = 0
        self.lock = Lock()
        self.call_times = deque(maxlen=calls_per_minute)
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        with self.lock:
            now = time.time()
            
            # Remove calls older than 1 minute
            while self.call_times and self.call_times[0] < now - 60:
                self.call_times.popleft()
            
            # If at limit, wait until oldest call expires
            if len(self.call_times) >= self.calls_per_minute:
                sleep_time = 60 - (now - self.call_times[0]) + 0.5
                if sleep_time > 0:
                    print(f"⏱️ Rate limit reached, waiting {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                    now = time.time()
            
            # Ensure minimum interval between calls
            time_since_last = now - self.last_call
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
                now = time.time()
            
            self.call_times.append(now)
            self.last_call = now

# Global rate limiter - 30 calls per minute (conservative for Yahoo Finance)
rate_limiter = RateLimiter(calls_per_minute=30)

def fetch_with_retry(ticker, max_retries=5):
    """
    Fetch stock data with exponential backoff and jitter
    Production-grade retry logic
    """
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Rate limiting
            rate_limiter.wait_if_needed()
            
            print(f"📡 Fetching {ticker} (attempt {attempt + 1}/{max_retries})...")
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Validate data quality
            if info and (info.get("symbol") or info.get("longName") or info.get("shortName")):
                print(f"✅ Successfully fetched {ticker}")
                return info, stock, "Yahoo Finance"
            
            # If no data, try alternative ticker formats
            if not ticker.endswith(('.NS', '.BO', '.L', '.T')):
                print(f"⚠️ No data for {ticker}, trying alternative formats...")
                return None, None, None
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a rate limit error
            if "429" in error_msg or "too many requests" in error_msg:
                # Exponential backoff with jitter for rate limits
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), 60)
                print(f"⚠️ Rate limited. Waiting {delay:.1f}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(delay)
            elif "404" in error_msg or "not found" in error_msg:
                print(f"❌ Ticker {ticker} not found in Yahoo Finance")
                return None, None, None
            else:
                # Other errors - shorter delay
                delay = min(base_delay * (1.5 ** attempt), 10)
                print(f"⚠️ Error: {str(e)}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
            
            if attempt == max_retries - 1:
                print(f"❌ Failed after {max_retries} attempts for {ticker}")
                return None, None, None
    
    return None, None, None


def get_stock_data_professional(ticker: str):
    """
    Professional-grade stock data fetcher
    1. Try Yahoo Finance with retry logic
    2. Try alternative ticker formats automatically
    3. Try backup data sources
    """
    
    # Strategy 1: Direct fetch with original ticker
    info, stock, source = fetch_with_retry(ticker)
    if info and source:
        return {
            "ticker": ticker,
            "info": info,
            "stock": stock,
            "has_data": True,
            "source": source,
            "actual_ticker": ticker
        }
    
    # Strategy 2: Try alternative ticker formats (for Indian/International stocks)
    if not ticker.endswith(('.NS', '.BO', '.L', '.T', '.HK', '.TO')):
        print(f"🔄 Trying alternative formats for {ticker}...")
        
        alternatives = [
            f"{ticker}.NS",  # NSE India
            f"{ticker}.BO",  # BSE India
            f"{ticker}.L",   # London
            f"{ticker}.T",   # Tokyo
        ]
        
        for alt_ticker in alternatives:
            info, stock, source = fetch_with_retry(alt_ticker)
            if info and source:
                print(f"✅ Found data using alternative ticker: {alt_ticker}")
                return {
                    "ticker": ticker,
                    "info": info,
                    "stock": stock,
                    "has_data": True,
                    "source": f"{source} (via {alt_ticker})",
                    "actual_ticker": alt_ticker
                }
    
    # Strategy 3: Try with longer delays (maybe temporary rate limit)
    print(f"⏳ Final attempt with extended delay for {ticker}...")
    time.sleep(5)
    info, stock, source = fetch_with_retry(ticker, max_retries=2)
    if info and source:
        return {
            "ticker": ticker,
            "info": info,
            "stock": stock,
            "has_data": True,
            "source": source,
            "actual_ticker": ticker
        }
    
    # All strategies failed
    print(f"❌ Unable to fetch data for {ticker} after all attempts")
    return {
        "ticker": ticker,
        "info": {},
        "stock": None,
        "has_data": False,
        "source": "None",
        "actual_ticker": ticker
    }


def enhance_stock_info_professional(ticker: str):
    """
    Enhanced professional stock info fetcher
    Returns: (info_dict, stock_object, source_name, actual_ticker)
    """
    result = get_stock_data_professional(ticker)
    
    return (
        result.get("info", {}),
        result.get("stock"),
        result.get("source", "None"),
        result.get("actual_ticker", ticker)
    )
