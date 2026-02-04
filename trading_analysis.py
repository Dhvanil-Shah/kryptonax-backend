"""
Professional Trading Analysis System - Optimized for Speed
Provides real-time analysis for different trading strategies
Supports: Equity/Long-term, Intraday, Swing, Positional, Scalping, Options
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from professional_fetcher import enhance_stock_info_professional
import statistics


def safe_get(info, key, default=0):
    """Safely get value from dict"""
    try:
        val = info.get(key, default)
        return val if val and not pd.isna(val) else default
    except:
        return default


def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index - Optimized"""
    try:
        if len(prices) < period + 1:
            return 50
        
        deltas = np.diff(prices[-period-1:])
        gains = deltas.copy()
        losses = deltas.copy()
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = np.abs(losses)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    except:
        return 50


def calculate_macd(prices):
    """Calculate MACD - Optimized"""
    try:
        if len(prices) < 26:
            return {"macd": 0, "signal": 0, "histogram": 0}
        
        prices_series = pd.Series(prices[-50:])  # Limit to last 50 for speed
        ema_12 = prices_series.ewm(span=12, adjust=False).mean()
        ema_26 = prices_series.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            "macd": float(macd_line.iloc[-1]),
            "signal": float(signal_line.iloc[-1]),
            "histogram": float(histogram.iloc[-1])
        }
    except:
        return {"macd": 0, "signal": 0, "histogram": 0}


def calculate_bollinger_bands(prices, period=20):
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return {"upper": prices[-1], "middle": prices[-1], "lower": prices[-1]}
    
    sma = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    
    return {
        "upper": sma + (2 * std),
        "middle": sma,
        "lower": sma - (2 * std)
    }


def calculate_support_resistance(hist_data):
    """Calculate support and resistance levels"""
    if hist_data.empty:
        return {"support": [], "resistance": []}
    
    highs = hist_data['High'].values
    lows = hist_data['Low'].values
    closes = hist_data['Close'].values
    
    # Find pivot points
    support_levels = []
    resistance_levels = []
    
    for i in range(2, len(closes) - 2):
        # Local minimum for support
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            support_levels.append(lows[i])
        
        # Local maximum for resistance
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            resistance_levels.append(highs[i])
    
    # Return top 3 support and resistance
    support_levels = sorted(support_levels, reverse=True)[:3]
    resistance_levels = sorted(resistance_levels)[:3]
    
    return {
        "support": [round(s, 2) for s in support_levels],
        "resistance": [round(r, 2) for r in resistance_levels]
    }


def calculate_volatility(prices):
    """Calculate historical volatility"""
    if len(prices) < 2:
        return 0
    
    returns = np.diff(prices) / prices[:-1]
    volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized volatility
    return round(volatility, 2)


def analyze_equity_longterm(ticker: str):
    """
    Equity/Long-term Investment Analysis - Optimized
    Focus: Fundamentals, Value, Growth potential, Dividend yields
    Timeframe: 1-5+ years
    """
    try:
        info, stock, source, actual_ticker = enhance_stock_info_professional(ticker)
        
        if not info or not stock:
            return {"error": "Unable to fetch stock data. Please verify the ticker symbol."}
        
        # Get historical data with timeout
        try:
            hist = stock.history(period="1y")  # Reduced from 5y for speed
            if hist.empty:
                return {"error": "No historical data available for this ticker"}
        except Exception as e:
            return {"error": f"Historical data unavailable: {str(e)}"}
        
        prices = hist['Close'].values
        if len(prices) == 0:
            return {"error": "Insufficient price data"}
            
        current_price = float(prices[-1])
        
        # Fundamental metrics with safe defaults
        market_cap = safe_get(info, "marketCap", 0)
        pe_ratio = safe_get(info, "trailingPE", 0)
        pb_ratio = safe_get(info, "priceToBook", 0)
        dividend_yield = safe_get(info, "dividendYield", 0) * 100
        roe = safe_get(info, "returnOnEquity", 0) * 100
        debt_to_equity = safe_get(info, "debtToEquity", 0)
        profit_margin = safe_get(info, "profitMargins", 0) * 100
        revenue_growth = safe_get(info, "revenueGrowth", 0) * 100
        
        # Calculate valuation score
        valuation_score = 50
        if 0 < pe_ratio < 20:
            valuation_score += 15
        elif 20 <= pe_ratio < 30:
            valuation_score += 10
        
        if 0 < pb_ratio < 3:
            valuation_score += 15
        elif 3 <= pb_ratio < 5:
            valuation_score += 10
        
        if dividend_yield > 3:
            valuation_score += 10
        elif dividend_yield > 1:
            valuation_score += 5
        
        if roe > 15:
            valuation_score += 10
        
        # Investment verdict
        if valuation_score >= 80:
            verdict = "STRONG BUY - Excellent fundamentals"
            action = "buy"
        elif valuation_score >= 65:
            verdict = "BUY - Good long-term potential"
            action = "buy"
        elif valuation_score >= 50:
            verdict = "HOLD - Average fundamentals"
            action = "hold"
        else:
            verdict = "AVOID - Weak fundamentals"
            action = "sell"
        
        # Price targets (conservative for long-term)
        avg_growth = revenue_growth if revenue_growth else 10
        target_1y = round(current_price * (1 + avg_growth / 100), 2)
        target_3y = round(current_price * ((1 + avg_growth / 100) ** 3), 2)
        
        return {
            "type": "Equity / Long-term Investment",
            "timeframe": "1-5+ years",
            "score": valuation_score,
            "verdict": verdict,
            "action": action,
            "current_price": round(current_price, 2),
            "targets": {
                "1_year": target_1y,
                "3_year": target_3y,
                "conservative": round(current_price * 1.1, 2),
                "optimistic": round(current_price * 1.5, 2)
            },
            "fundamentals": {
                "market_cap": market_cap,
                "pe_ratio": round(pe_ratio, 2) if pe_ratio else "N/A",
                "pb_ratio": round(pb_ratio, 2) if pb_ratio else "N/A",
                "dividend_yield": round(dividend_yield, 2),
                "roe": round(roe, 2),
                "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity else "N/A",
                "profit_margin": round(profit_margin, 2),
                "revenue_growth": round(revenue_growth, 2)
            },
            "key_strengths": get_equity_strengths(info, valuation_score),
            "risks": get_equity_risks(info, debt_to_equity, pe_ratio),
            "recommendation": get_equity_recommendation(valuation_score, dividend_yield, roe)
        }
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}


def analyze_intraday(ticker: str):
    """
    Intraday Trading Analysis
    Focus: Technical indicators, momentum, volume, volatility
    Timeframe: Same day (5min - 1hr candles)
    """
    info, stock, source, actual_ticker = enhance_stock_info_professional(ticker)
    
    if not info or not stock:
        return {"error": "Unable to fetch stock data"}
    
    # Get intraday data
    hist = stock.history(period="5d", interval="15m")
    if hist.empty:
        hist = stock.history(period="5d")
    
    prices = hist['Close'].values
    volumes = hist['Volume'].values
    current_price = prices[-1] if len(prices) > 0 else info.get("currentPrice", 0)
    
    # Technical indicators
    rsi = calculate_rsi(prices, period=14)
    macd = calculate_macd(prices)
    bollinger = calculate_bollinger_bands(prices, period=20)
    volatility = calculate_volatility(prices)
    
    # Volume analysis
    avg_volume = np.mean(volumes) if len(volumes) > 0 else 0
    current_volume = volumes[-1] if len(volumes) > 0 else 0
    volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 1
    
    # Calculate trading score
    trading_score = 50
    
    # RSI signals
    if 30 <= rsi <= 40:
        trading_score += 15  # Oversold
    elif 60 <= rsi <= 70:
        trading_score += 10  # Bullish momentum
    elif rsi > 70:
        trading_score -= 10  # Overbought
    elif rsi < 30:
        trading_score += 5  # Extremely oversold
    
    # MACD signals
    if macd['histogram'] > 0 and macd['macd'] > macd['signal']:
        trading_score += 15  # Bullish crossover
    elif macd['histogram'] < 0:
        trading_score -= 10  # Bearish
    
    # Volume confirmation
    if volume_ratio > 1.5:
        trading_score += 10  # High volume
    
    # Bollinger Band position
    bb_position = (current_price - bollinger['lower']) / (bollinger['upper'] - bollinger['lower'])
    if bb_position < 0.2:
        trading_score += 10  # Near lower band
    elif bb_position > 0.8:
        trading_score -= 5  # Near upper band
    
    # Trading verdict
    if trading_score >= 75:
        verdict = "STRONG BUY - Bullish momentum"
        action = "buy"
        entry = round(current_price * 0.998, 2)
        stop_loss = round(current_price * 0.985, 2)
        target = round(current_price * 1.02, 2)
    elif trading_score >= 60:
        verdict = "BUY - Positive signals"
        action = "buy"
        entry = round(current_price * 0.999, 2)
        stop_loss = round(current_price * 0.99, 2)
        target = round(current_price * 1.015, 2)
    elif trading_score <= 35:
        verdict = "SELL - Bearish signals"
        action = "sell"
        entry = round(current_price * 1.002, 2)
        stop_loss = round(current_price * 1.015, 2)
        target = round(current_price * 0.98, 2)
    else:
        verdict = "NO TRADE - Wait for better setup"
        action = "hold"
        entry = current_price
        stop_loss = round(current_price * 0.985, 2)
        target = round(current_price * 1.015, 2)
    
    return {
        "type": "Intraday Trading",
        "timeframe": "Same day",
        "score": trading_score,
        "verdict": verdict,
        "action": action,
        "current_price": round(current_price, 2),
        "entry_price": entry,
        "stop_loss": stop_loss,
        "target": target,
        "risk_reward": round((target - entry) / (entry - stop_loss), 2) if action in ["buy", "sell"] else 0,
        "technical_indicators": {
            "rsi": round(rsi, 2),
            "rsi_signal": "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral",
            "macd": round(macd['macd'], 4),
            "macd_signal": round(macd['signal'], 4),
            "macd_histogram": round(macd['histogram'], 4),
            "macd_status": "Bullish" if macd['histogram'] > 0 else "Bearish",
            "bollinger_upper": round(bollinger['upper'], 2),
            "bollinger_middle": round(bollinger['middle'], 2),
            "bollinger_lower": round(bollinger['lower'], 2),
            "volatility": volatility,
            "volume_ratio": round(volume_ratio, 2)
        },
        "trading_strategy": get_intraday_strategy(rsi, macd, volume_ratio),
        "key_levels": {
            "resistance": round(bollinger['upper'], 2),
            "support": round(bollinger['lower'], 2)
        }
    }


def analyze_swing(ticker: str):
    """
    Swing Trading Analysis
    Focus: Medium-term trends, technical patterns, momentum
    Timeframe: 3-10 days
    """
    info, stock, source, actual_ticker = enhance_stock_info_professional(ticker)
    
    if not info or not stock:
        return {"error": "Unable to fetch stock data"}
    
    # Get swing trading data
    hist = stock.history(period="3mo")
    prices = hist['Close'].values
    volumes = hist['Volume'].values
    current_price = prices[-1] if len(prices) > 0 else info.get("currentPrice", 0)
    
    # Technical analysis
    rsi = calculate_rsi(prices, period=14)
    macd = calculate_macd(prices)
    levels = calculate_support_resistance(hist)
    
    # Moving averages
    ma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else current_price
    ma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else current_price
    
    # Calculate swing score
    swing_score = 50
    
    # Trend analysis
    if current_price > ma_20 > ma_50:
        swing_score += 20  # Strong uptrend
    elif current_price > ma_20:
        swing_score += 10  # Uptrend
    
    # RSI for swing
    if 40 <= rsi <= 60:
        swing_score += 15  # Ideal range
    elif rsi > 70:
        swing_score -= 15  # Overbought
    
    # MACD confirmation
    if macd['macd'] > macd['signal'] and macd['histogram'] > 0:
        swing_score += 15
    
    # Support/Resistance proximity
    nearest_support = levels['support'][0] if levels['support'] else current_price * 0.95
    nearest_resistance = levels['resistance'][0] if levels['resistance'] else current_price * 1.05
    
    if current_price < nearest_support * 1.02:
        swing_score += 10  # Near support
    
    # Verdict
    if swing_score >= 75:
        verdict = "STRONG BUY - Excellent swing setup"
        action = "buy"
    elif swing_score >= 60:
        verdict = "BUY - Good swing opportunity"
        action = "buy"
    elif swing_score <= 40:
        verdict = "SELL - Bearish swing pattern"
        action = "sell"
    else:
        verdict = "HOLD - No clear swing setup"
        action = "hold"
    
    # Swing targets (3-5% moves)
    entry = round(current_price * 0.995, 2)
    stop_loss = round(nearest_support * 0.98, 2) if action == "buy" else round(nearest_resistance * 1.02, 2)
    target = round(nearest_resistance * 1.02, 2) if action == "buy" else round(nearest_support * 0.98, 2)
    
    return {
        "type": "Swing Trading",
        "timeframe": "3-10 days",
        "score": swing_score,
        "verdict": verdict,
        "action": action,
        "current_price": round(current_price, 2),
        "entry_price": entry,
        "stop_loss": stop_loss,
        "target": target,
        "risk_reward": round(abs(target - entry) / abs(entry - stop_loss), 2) if action != "hold" else 0,
        "technical_indicators": {
            "rsi": round(rsi, 2),
            "ma_20": round(ma_20, 2),
            "ma_50": round(ma_50, 2),
            "trend": "Uptrend" if current_price > ma_20 > ma_50 else "Downtrend" if current_price < ma_20 < ma_50 else "Sideways",
            "macd_status": "Bullish" if macd['histogram'] > 0 else "Bearish"
        },
        "key_levels": {
            "support": levels['support'][:2],
            "resistance": levels['resistance'][:2]
        },
        "holding_period": "3-7 days",
        "strategy_notes": get_swing_strategy(swing_score, current_price, ma_20, ma_50)
    }


def analyze_positional(ticker: str):
    """
    Positional Trading Analysis
    Focus: Medium-term trends, fundamentals + technicals
    Timeframe: 2 weeks - 3 months
    """
    info, stock, source, actual_ticker = enhance_stock_info_professional(ticker)
    
    if not info or not stock:
        return {"error": "Unable to fetch stock data"}
    
    # Get positional data
    hist = stock.history(period="1y")
    prices = hist['Close'].values
    current_price = prices[-1] if len(prices) > 0 else info.get("currentPrice", 0)
    
    # Fundamental factors
    pe_ratio = info.get("trailingPE", 0)
    revenue_growth = info.get("revenueGrowth", 0) * 100 if info.get("revenueGrowth") else 0
    profit_margin = info.get("profitMargins", 0) * 100 if info.get("profitMargins") else 0
    
    # Technical factors
    rsi = calculate_rsi(prices, period=14)
    macd = calculate_macd(prices)
    
    # Moving averages for trend
    ma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else current_price
    ma_200 = np.mean(prices[-200:]) if len(prices) >= 200 else current_price
    
    # Calculate positional score (blend of fundamental + technical)
    pos_score = 50
    
    # Fundamental component (40%)
    if 0 < pe_ratio < 25:
        pos_score += 10
    if revenue_growth > 10:
        pos_score += 10
    if profit_margin > 10:
        pos_score += 10
    
    # Technical component (60%)
    if current_price > ma_50 > ma_200:
        pos_score += 15  # Golden cross territory
    elif current_price > ma_50:
        pos_score += 10
    
    if 40 <= rsi <= 65:
        pos_score += 10
    
    if macd['histogram'] > 0:
        pos_score += 10
    
    # Verdict
    if pos_score >= 75:
        verdict = "STRONG BUY - Excellent position"
        action = "buy"
    elif pos_score >= 60:
        verdict = "BUY - Good positional trade"
        action = "buy"
    elif pos_score <= 40:
        verdict = "SELL - Weak position"
        action = "sell"
    else:
        verdict = "HOLD - Average setup"
        action = "hold"
    
    # Positional targets (5-15% moves)
    entry = round(current_price * 0.99, 2)
    stop_loss = round(current_price * 0.92, 2)
    target_1 = round(current_price * 1.08, 2)
    target_2 = round(current_price * 1.15, 2)
    
    return {
        "type": "Positional Trading",
        "timeframe": "2 weeks - 3 months",
        "score": pos_score,
        "verdict": verdict,
        "action": action,
        "current_price": round(current_price, 2),
        "entry_price": entry,
        "stop_loss": stop_loss,
        "targets": {
            "target_1": target_1,
            "target_2": target_2
        },
        "risk_reward": round((target_1 - entry) / (entry - stop_loss), 2) if action != "hold" else 0,
        "fundamental_metrics": {
            "pe_ratio": round(pe_ratio, 2) if pe_ratio else "N/A",
            "revenue_growth": round(revenue_growth, 2),
            "profit_margin": round(profit_margin, 2)
        },
        "technical_indicators": {
            "rsi": round(rsi, 2),
            "ma_50": round(ma_50, 2),
            "ma_200": round(ma_200, 2),
            "trend": "Bullish" if current_price > ma_50 > ma_200 else "Bearish" if current_price < ma_50 < ma_200 else "Neutral"
        },
        "holding_period": "1-3 months",
        "strategy": get_positional_strategy(pos_score)
    }


def analyze_scalping(ticker: str):
    """
    Scalping Analysis
    Focus: Very short-term, quick profits, high frequency
    Timeframe: Seconds to minutes
    """
    info, stock, source, actual_ticker = enhance_stock_info_professional(ticker)
    
    if not info or not stock:
        return {"error": "Unable to fetch stock data"}
    
    # Get very recent data
    hist = stock.history(period="1d", interval="1m")
    if hist.empty:
        hist = stock.history(period="5d", interval="5m")
    
    prices = hist['Close'].values
    volumes = hist['Volume'].values
    current_price = prices[-1] if len(prices) > 0 else info.get("currentPrice", 0)
    
    # Quick technical indicators
    rsi = calculate_rsi(prices, period=5)  # Shorter period for scalping
    
    # Momentum
    momentum_5 = ((prices[-1] - prices[-5]) / prices[-5] * 100) if len(prices) >= 5 else 0
    
    # Volume spike
    avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else 0
    current_volume = volumes[-1] if len(volumes) > 0 else 0
    volume_spike = (current_volume / avg_volume) if avg_volume > 0 else 1
    
    # Bid-ask spread (simulated based on volatility)
    volatility = calculate_volatility(prices)
    spread_pct = min(volatility / 100, 0.5)  # Cap at 0.5%
    
    # Calculate scalping score
    scalp_score = 50
    
    # High volatility is good for scalping
    if volatility > 2:
        scalp_score += 20
    elif volatility > 1:
        scalp_score += 10
    
    # Volume is crucial
    if volume_spike > 2:
        scalp_score += 15
    elif volume_spike > 1.5:
        scalp_score += 10
    
    # Momentum
    if abs(momentum_5) > 0.5:
        scalp_score += 15
    
    # RSI extremes (for quick reversals)
    if rsi > 75 or rsi < 25:
        scalp_score += 10
    
    # Verdict
    if scalp_score >= 70 and volume_spike > 1.5:
        verdict = "SCALP OPPORTUNITY - High volume & volatility"
        action = "scalp"
    elif scalp_score >= 55:
        verdict = "POTENTIAL SCALP - Monitor closely"
        action = "watch"
    else:
        verdict = "NO SCALP - Low activity"
        action = "avoid"
    
    # Scalping targets (0.2-0.5% moves)
    entry = round(current_price, 2)
    stop_loss = round(current_price * 0.997, 2)
    target = round(current_price * 1.003, 2)
    
    return {
        "type": "Scalping",
        "timeframe": "Seconds to minutes",
        "score": scalp_score,
        "verdict": verdict,
        "action": action,
        "current_price": round(current_price, 2),
        "entry_price": entry,
        "stop_loss": stop_loss,
        "target": target,
        "risk_reward": round((target - entry) / (entry - stop_loss), 2) if action == "scalp" else 0,
        "scalping_metrics": {
            "volatility": volatility,
            "volume_spike": round(volume_spike, 2),
            "momentum_5min": round(momentum_5, 3),
            "rsi_5": round(rsi, 2),
            "spread_estimate": round(spread_pct, 3)
        },
        "optimal_conditions": {
            "volatility_required": "> 1.5%",
            "volume_spike_required": "> 1.5x",
            "minimum_price": "> $10 (or ₹100)"
        },
        "warning": "⚠️ Scalping requires: Real-time data, Fast execution, Low latency, High discipline",
        "recommended": "Best suited for experienced traders with professional tools"
    }


def analyze_options(ticker: str):
    """
    Options Trading Analysis
    Focus: Implied volatility, Greeks, option strategies
    Timeframe: Varies by strategy
    """
    info, stock, source, actual_ticker = enhance_stock_info_professional(ticker)
    
    if not info or not stock:
        return {"error": "Unable to fetch stock data"}
    
    # Get historical data
    hist = stock.history(period="6mo")
    prices = hist['Close'].values
    current_price = prices[-1] if len(prices) > 0 else info.get("currentPrice", 0)
    
    # Calculate historical volatility (IV proxy)
    volatility = calculate_volatility(prices)
    
    # Technical indicators
    rsi = calculate_rsi(prices, period=14)
    
    # Price range analysis
    price_52w_high = max(prices) if len(prices) > 0 else current_price
    price_52w_low = min(prices) if len(prices) > 0 else current_price
    price_position = ((current_price - price_52w_low) / (price_52w_high - price_52w_low) * 100) if price_52w_high != price_52w_low else 50
    
    # Moving averages
    ma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else current_price
    
    # Determine best option strategy
    if volatility < 20 and 40 <= rsi <= 60:
        strategy = "Covered Call / Cash Secured Put"
        rationale = "Low volatility - ideal for premium collection"
        expected_return = "1-3% per month"
    elif volatility > 40:
        strategy = "Straddle / Strangle"
        rationale = "High volatility - expect big move"
        expected_return = "10-50% on directional move"
    elif current_price < ma_20 and rsi < 40:
        strategy = "Bull Call Spread"
        rationale = "Bullish setup with limited risk"
        expected_return = "20-100% on upward move"
    elif current_price > ma_20 and rsi > 60:
        strategy = "Bear Put Spread"
        rationale = "Bearish signals with defined risk"
        expected_return = "20-100% on downward move"
    else:
        strategy = "Iron Condor"
        rationale = "Neutral market - collect premium"
        expected_return = "5-10% of width"
    
    # Options score
    options_score = 50
    
    # Volatility scoring
    if 25 <= volatility <= 45:
        options_score += 20  # Sweet spot
    elif volatility > 50:
        options_score += 15  # High premium
    
    # Trend clarity
    if abs(current_price - ma_20) / ma_20 > 0.05:
        options_score += 15  # Clear trend
    
    # Price position
    if 30 <= price_position <= 70:
        options_score += 15  # Middle range (room to move)
    
    return {
        "type": "Options Trading",
        "timeframe": "Varies by strategy",
        "score": options_score,
        "recommended_strategy": strategy,
        "rationale": rationale,
        "expected_return": expected_return,
        "current_price": round(current_price, 2),
        "volatility_metrics": {
            "historical_volatility": volatility,
            "volatility_regime": "High" if volatility > 40 else "Medium" if volatility > 20 else "Low",
            "iv_percentile_proxy": round(price_position, 1)
        },
        "technical_context": {
            "rsi": round(rsi, 2),
            "price_vs_ma20": round(((current_price - ma_20) / ma_20 * 100), 2),
            "52w_position": round(price_position, 1)
        },
        "strategy_details": get_options_strategy_details(strategy, current_price, volatility),
        "greeks_estimate": {
            "delta": "Call: 0.5, Put: -0.5 (ATM estimate)",
            "gamma": "Higher near ATM, decays with time",
            "theta": "Accelerates in final 30 days",
            "vega": f"High sensitivity (IV: {volatility}%)"
        },
        "risk_warning": "⚠️ Options carry significant risk. Only trade with capital you can afford to lose.",
        "note": "For accurate Greeks and IV, use professional options platform"
    }


# Helper functions for detailed insights

def get_equity_strengths(info, score):
    """Get key strengths for equity investment"""
    strengths = []
    if score >= 80:
        strengths.append("✅ Strong fundamental metrics")
    if info.get("dividendYield", 0) > 0.02:
        strengths.append("✅ Regular dividend payments")
    if info.get("returnOnEquity", 0) > 0.15:
        strengths.append("✅ High return on equity")
    if info.get("profitMargins", 0) > 0.1:
        strengths.append("✅ Healthy profit margins")
    
    return strengths if strengths else ["Review fundamentals carefully"]


def get_equity_risks(info, debt_to_equity, pe_ratio):
    """Identify equity investment risks"""
    risks = []
    if debt_to_equity and debt_to_equity > 2:
        risks.append("⚠️ High debt levels")
    if pe_ratio and pe_ratio > 40:
        risks.append("⚠️ Potentially overvalued")
    if not info.get("dividendYield"):
        risks.append("ℹ️ No dividend history")
    
    return risks if risks else ["Manageable risk profile"]


def get_equity_recommendation(score, dividend, roe):
    """Generate investment recommendation"""
    if score >= 75 and dividend > 2:
        return "Excellent for long-term wealth creation. Consider SIP/regular investment."
    elif score >= 60:
        return "Good for diversified portfolio. Monitor quarterly results."
    else:
        return "Better opportunities available. Consider alternatives."


def get_intraday_strategy(rsi, macd, volume):
    """Get intraday trading strategy"""
    if rsi < 30 and macd['histogram'] > 0:
        return "Oversold bounce play. Buy dips with tight stop-loss."
    elif rsi > 70:
        return "Overbought zone. Wait for pullback or avoid long positions."
    elif volume > 1.5:
        return "High volume breakout. Ride momentum with trailing stop."
    else:
        return "No clear setup. Wait for confirmation signals."


def get_swing_strategy(score, price, ma20, ma50):
    """Get swing trading strategy"""
    if score >= 70 and price > ma20 > ma50:
        return "Strong uptrend. Buy pullbacks to MA20. Target MA50 + 5%."
    elif score <= 40:
        return "Weak trend. Avoid or consider short positions with proper risk management."
    else:
        return "Choppy market. Wait for clear breakout or breakdown."


def get_positional_strategy(score):
    """Get positional trading strategy"""
    if score >= 75:
        return "Build position in 2-3 tranches. Hold for 8-12 weeks. Partial booking at targets."
    elif score >= 60:
        return "Enter with 50% capital. Add on confirmation. Monitor weekly."
    else:
        return "Avoid new positions. Exit existing positions on bounce."


def get_options_strategy_details(strategy, price, volatility):
    """Get detailed options strategy breakdown"""
    strategies = {
        "Covered Call / Cash Secured Put": {
            "setup": f"Sell {price*1.05:.2f} Call or {price*0.95:.2f} Put (OTM)",
            "capital": f"${price:.2f} x 100 shares or cash equivalent",
            "max_profit": "Premium collected",
            "max_loss": "Unlimited (covered) / Premium collected (CSP)"
        },
        "Straddle / Strangle": {
            "setup": f"Buy {price:.2f} Call + Put or OTM variants",
            "capital": "High premium due to volatility",
            "max_profit": "Unlimited",
            "max_loss": "Net premium paid"
        },
        "Bull Call Spread": {
            "setup": f"Buy {price:.2f} Call, Sell {price*1.05:.2f} Call",
            "capital": "Net debit (difference in premiums)",
            "max_profit": "Spread width - Net debit",
            "max_loss": "Net debit paid"
        },
        "Bear Put Spread": {
            "setup": f"Buy {price:.2f} Put, Sell {price*0.95:.2f} Put",
            "capital": "Net debit (difference in premiums)",
            "max_profit": "Spread width - Net debit",
            "max_loss": "Net debit paid"
        },
        "Iron Condor": {
            "setup": f"Sell {price*1.03:.2f} Call, Buy {price*1.05:.2f} Call, Sell {price*0.97:.2f} Put, Buy {price*0.95:.2f} Put",
            "capital": "Net credit collected",
            "max_profit": "Net credit collected",
            "max_loss": "Spread width - Net credit"
        }
    }
    
    return strategies.get(strategy, {"setup": "Consult options expert", "capital": "Varies", "max_profit": "Varies", "max_loss": "Varies"})


def get_trading_analysis(ticker: str, trading_type: str):
    """
    Main function to get trading analysis based on type - Optimized with error handling
    """
    try:
        trading_type = trading_type.lower().replace(" ", "_").replace("/", "_")
        
        # Route to appropriate analysis function
        if "equity" in trading_type or "long" in trading_type:
            result = analyze_equity_longterm(ticker)
        elif "intraday" in trading_type:
            result = analyze_intraday(ticker)
        elif "swing" in trading_type:
            result = analyze_swing(ticker)
        elif "positional" in trading_type:
            result = analyze_positional(ticker)
        elif "scalp" in trading_type:
            result = analyze_scalping(ticker)
        elif "option" in trading_type:
            result = analyze_options(ticker)
        else:
            return {"error": "Invalid trading type. Choose from: equity_longterm, intraday, swing, positional, scalping, options"}
        
        return result
        
    except Exception as e:
        return {
            "error": f"Analysis failed: {str(e)}",
            "type": trading_type,
            "message": "Please try again or contact support if the issue persists."
        }
