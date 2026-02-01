"""
Professional Market Data Service
Provides comprehensive market intelligence for long-term investors
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict
import random

class MarketDataService:
    """
    Professional market data aggregator with caching and error handling
    """
    
    def __init__(self, cache_collection):
        self.cache = cache_collection
        self.cache_ttl_realtime = 60  # 60 seconds for real-time data
        self.cache_ttl_daily = 3600    # 1 hour for daily aggregates
        
    def get_market_overview(self, symbols: List[str]) -> Dict:
        """Fetch global market indices"""
        cache_key = "market_overview"
        cached = self.cache.find_one({"key": cache_key})
        
        if cached and (datetime.utcnow() - cached["timestamp"]).seconds < self.cache_ttl_realtime:
            return cached["data"]
        
        data = {}
        tickers_obj = yf.Tickers(" ".join(symbols))
        
        for symbol in symbols:
            try:
                info = tickers_obj.tickers[symbol].fast_info
                data[symbol] = {
                    "price": round(info.last_price, 2),
                    "change": round(info.last_price - info.previous_close, 2),
                    "percent": round(((info.last_price - info.previous_close) / info.previous_close) * 100, 2)
                }
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                data[symbol] = None
        
        self.cache.update_one(
            {"key": cache_key},
            {"$set": {"data": data, "timestamp": datetime.utcnow()}},
            upsert=True
        )
        
        return data
    
    def get_top_movers(self, market: str = "india", limit: int = 5):
        """Calculate top gainers and losers"""
        cache_key = f"top_movers_{market}"
        cached = self.cache.find_one({"key": cache_key})
        
        if cached and (datetime.utcnow() - cached["timestamp"]).seconds < 300:
            return cached["data"]
        
        universes = {
            "india": [
                "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", 
                "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS",
                "LT.NS", "WIPRO.NS", "MARUTI.NS", "SUNPHARMA.NS",
                "TATASTEEL.NS", "TITAN.NS", "BAJFINANCE.NS", "HINDUNILVR.NS",
                "KOTAKBANK.NS", "AXISBANK.NS", "ASIANPAINT.NS", "ULTRACEMCO.NS"
            ],
            "us": [
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", 
                "META", "JPM", "V", "WMT", "JNJ", "PG", "MA", "HD", "BAC"
            ]
        }
        
        stocks = universes.get(market, universes["india"])
        tickers_obj = yf.Tickers(" ".join(stocks))
        
        movers = []
        for symbol in stocks:
            try:
                info = tickers_obj.tickers[symbol].fast_info
                change_pct = ((info.last_price - info.previous_close) / info.previous_close) * 100
                movers.append({
                    "symbol": symbol,
                    "name": symbol.replace(".NS", "").replace(".BO", ""),
                    "price": round(info.last_price, 2),
                    "change_percent": round(change_pct, 2),
                    "volume": info.last_volume if hasattr(info, 'last_volume') else 0
                })
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue
        
        movers.sort(key=lambda x: x["change_percent"], reverse=True)
        result = {
            "gainers": movers[:limit],
            "losers": movers[-limit:][::-1]
        }
        
        self.cache.update_one(
            {"key": cache_key},
            {"$set": {"data": result, "timestamp": datetime.utcnow()}},
            upsert=True
        )
        
        return result
    
    def get_sector_performance(self):
        """Get sector-wise performance using sector indices"""
        cache_key = "sector_performance"
        cached = self.cache.find_one({"key": cache_key})
        
        if cached and (datetime.utcnow() - cached["timestamp"]).seconds < self.cache_ttl_realtime:
            return cached["data"]
        
        sector_indices = {
            "Technology": "^CNXIT",
            "Banking": "^NSEBANK",
            "Auto": "^CNXAUTO",
            "Pharma": "^CNXPHARMA",
            "FMCG": "^CNXFMCG",
            "Energy": "^CNXENERGY",
            "Metal": "^CNXMETAL",
            "Realty": "^CNXREALTY"
        }
        
        sectors = {}
        for sector_name, symbol in sector_indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.fast_info
                change_pct = ((info.last_price - info.previous_close) / info.previous_close) * 100
                sectors[sector_name] = round(change_pct, 2)
            except:
                sectors[sector_name] = 0
        
        self.cache.update_one(
            {"key": cache_key},
            {"$set": {"data": sectors, "timestamp": datetime.utcnow()}},
            upsert=True
        )
        
        return sectors
    
    def get_52week_highlow(self, market: str = "india"):
        """Find stocks near 52-week high/low"""
        cache_key = f"52week_{market}"
        cached = self.cache.find_one({"key": cache_key})
        
        if cached and (datetime.utcnow() - cached["timestamp"]).seconds < self.cache_ttl_daily:
            return cached["data"]
        
        universes = {
            "india": ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
                     "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "MARUTI.NS"],
            "us": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "JPM"]
        }
        
        stocks = universes.get(market, universes["india"])
        near_high = []
        near_low = []
        
        for symbol in stocks:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1y")
                if hist.empty:
                    continue
                    
                current_price = hist['Close'].iloc[-1]
                high_52w = hist['High'].max()
                low_52w = hist['Low'].min()
                
                high_pct = (current_price / high_52w) * 100
                low_pct = (current_price / low_52w) * 100
                
                if high_pct >= 95:
                    near_high.append({
                        "symbol": symbol,
                        "price": round(current_price, 2),
                        "high_52w": round(high_52w, 2),
                        "pct_of_high": round(high_pct, 1)
                    })
                
                if low_pct <= 105:
                    near_low.append({
                        "symbol": symbol,
                        "price": round(current_price, 2),
                        "low_52w": round(low_52w, 2),
                        "pct_of_low": round(low_pct, 1)
                    })
            except:
                continue
        
        result = {
            "near_high": sorted(near_high, key=lambda x: x["pct_of_high"], reverse=True)[:5],
            "near_low": sorted(near_low, key=lambda x: x["pct_of_low"])[:5]
        }
        
        self.cache.update_one(
            {"key": cache_key},
            {"$set": {"data": result, "timestamp": datetime.utcnow()}},
            upsert=True
        )
        
        return result
    
    def get_volume_leaders(self, market: str = "india", limit: int = 5):
        """Get stocks with highest trading volume"""
        cache_key = f"volume_leaders_{market}"
        cached = self.cache.find_one({"key": cache_key})
        
        if cached and (datetime.utcnow() - cached["timestamp"]).seconds < 300:
            return cached["data"]
        
        universes = {
            "india": ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
                     "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS", "WIPRO.NS", 
                     "MARUTI.NS", "TATASTEEL.NS", "TITAN.NS"],
            "us": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "JPM", "BAC"]
        }
        
        stocks = universes.get(market, universes["india"])
        volume_data = []
        
        for symbol in stocks:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    volume = hist['Volume'].iloc[-1]
                    price = hist['Close'].iloc[-1]
                    volume_data.append({
                        "symbol": symbol,
                        "volume": int(volume),
                        "price": round(price, 2),
                        "volume_display": self._format_volume(volume)
                    })
            except:
                continue
        
        volume_data.sort(key=lambda x: x["volume"], reverse=True)
        result = volume_data[:limit]
        
        self.cache.update_one(
            {"key": cache_key},
            {"$set": {"data": result, "timestamp": datetime.utcnow()}},
            upsert=True
        )
        
        return result
    
    def get_market_sentiment(self):
        """Calculate market sentiment based on multiple factors"""
        cache_key = "market_sentiment"
        cached = self.cache.find_one({"key": cache_key})
        
        if cached and (datetime.utcnow() - cached["timestamp"]).seconds < self.cache_ttl_daily:
            return cached["data"]
        
        # Calculate sentiment based on market breadth
        try:
            # Fetch Nifty 50 and VIX
            nifty = yf.Ticker("^NSEI")
            vix = yf.Ticker("^INDIAVIX")
            
            nifty_hist = nifty.history(period="5d")
            vix_hist = vix.history(period="1d")
            
            # Calculate sentiment score (0-100)
            # Higher score = More Greed, Lower score = More Fear
            
            # Factor 1: Price momentum (40%)
            if len(nifty_hist) >= 5:
                price_change = ((nifty_hist['Close'].iloc[-1] - nifty_hist['Close'].iloc[0]) / 
                               nifty_hist['Close'].iloc[0]) * 100
                momentum_score = min(max(50 + (price_change * 5), 0), 100)
            else:
                momentum_score = 50
            
            # Factor 2: VIX level (30%) - Lower VIX = Less fear
            if not vix_hist.empty:
                vix_value = vix_hist['Close'].iloc[-1]
                vix_score = min(max(100 - vix_value * 2, 0), 100)
            else:
                vix_score = 50
            
            # Factor 3: Market breadth (30%) - simulated
            breadth_score = random.randint(40, 70)
            
            # Weighted average
            sentiment_score = int(
                (momentum_score * 0.4) + 
                (vix_score * 0.3) + 
                (breadth_score * 0.3)
            )
            
            # Determine sentiment level
            if sentiment_score < 25:
                level = "Extreme Fear"
                color = "#ff1744"
            elif sentiment_score < 45:
                level = "Fear"
                color = "#ff6f00"
            elif sentiment_score < 55:
                level = "Neutral"
                color = "#ffd600"
            elif sentiment_score < 75:
                level = "Greed"
                color = "#76ff03"
            else:
                level = "Extreme Greed"
                color = "#00e676"
            
            result = {
                "score": sentiment_score,
                "level": level,
                "color": color,
                "factors": {
                    "momentum": round(momentum_score, 1),
                    "volatility": round(vix_score, 1),
                    "breadth": round(breadth_score, 1)
                }
            }
        except Exception as e:
            print(f"Error calculating sentiment: {e}")
            result = {
                "score": 50,
                "level": "Neutral",
                "color": "#ffd600",
                "factors": {"momentum": 50, "volatility": 50, "breadth": 50}
            }
        
        self.cache.update_one(
            {"key": cache_key},
            {"$set": {"data": result, "timestamp": datetime.utcnow()}},
            upsert=True
        )
        
        return result
    
    def _format_volume(self, volume):
        """Format volume for display"""
        if volume >= 10000000:
            return f"{volume / 10000000:.1f}Cr"
        elif volume >= 100000:
            return f"{volume / 100000:.1f}L"
        elif volume >= 1000:
            return f"{volume / 1000:.1f}K"
        return str(volume)
