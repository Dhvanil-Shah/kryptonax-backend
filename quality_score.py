"""
Long-Term Quality Score Calculator for Stocks
Analyzes fundamental strength, dividend reliability, management quality, and business moat
"""
import yfinance as yf
from datetime import datetime, timedelta
import statistics

def calculate_quality_score(ticker: str):
    """
    Calculate comprehensive long-term quality score (0-100)
    Returns detailed breakdown of scores
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data for trend analysis
        hist = stock.history(period="5y")
        
        if hist.empty or not info:
            return None
        
        # 1. FUNDAMENTAL STRENGTH (0-100)
        fundamental_score = calculate_fundamental_strength(info, stock)
        
        # 2. DIVIDEND RELIABILITY (0-100)
        dividend_score = calculate_dividend_reliability(info, stock)
        
        # 3. MANAGEMENT QUALITY (0-100)
        management_score = calculate_management_quality(info)
        
        # 4. BUSINESS MOAT (0-100)
        moat_score = calculate_business_moat(info)
        
        # 5. CALCULATE OVERALL SCORE (weighted average)
        overall_score = int(
            fundamental_score * 0.35 +
            dividend_score * 0.20 +
            management_score * 0.25 +
            moat_score * 0.20
        )
        
        # 6. DETERMINE VERDICT
        verdict = get_verdict(overall_score)
        
        # 7. CALCULATE RISKS
        risks = calculate_risks(info, hist)
        
        # 8. PRICE TARGET PROJECTION
        target = calculate_price_target(info, hist)
        
        return {
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "overall_score": overall_score,
            "grade": get_grade(overall_score),
            "fundamental_score": fundamental_score,
            "dividend_score": dividend_score,
            "management_score": management_score,
            "moat_score": moat_score,
            "verdict": verdict,
            "risks": risks,
            "target": target,
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
            "details": {
                "fundamental": get_fundamental_details(info, stock),
                "dividend": get_dividend_details(info, stock),
                "management": get_management_details(info),
                "moat": get_moat_details(info)
            }
        }
    except Exception as e:
        print(f"Error calculating quality score for {ticker}: {str(e)}")
        return None


def calculate_fundamental_strength(info, stock):
    """Calculate fundamental strength score"""
    score = 0
    
    # Revenue growth (0-25 points)
    revenue_growth = info.get("revenueGrowth", 0) or 0
    if revenue_growth > 0.20:
        score += 25
    elif revenue_growth > 0.10:
        score += 20
    elif revenue_growth > 0.05:
        score += 15
    elif revenue_growth > 0:
        score += 10
    
    # Profit margins (0-25 points)
    profit_margin = info.get("profitMargins", 0) or 0
    if profit_margin > 0.15:
        score += 25
    elif profit_margin > 0.10:
        score += 20
    elif profit_margin > 0.05:
        score += 15
    elif profit_margin > 0:
        score += 10
    
    # Debt to equity (0-25 points)
    debt_to_equity = info.get("debtToEquity", 100) or 100
    if debt_to_equity < 30:
        score += 25
    elif debt_to_equity < 50:
        score += 20
    elif debt_to_equity < 80:
        score += 15
    elif debt_to_equity < 120:
        score += 10
    
    # Return on Equity (0-25 points)
    roe = info.get("returnOnEquity", 0) or 0
    if roe > 0.20:
        score += 25
    elif roe > 0.15:
        score += 20
    elif roe > 0.10:
        score += 15
    elif roe > 0.05:
        score += 10
    
    return min(score, 100)


def calculate_dividend_reliability(info, stock):
    """Calculate dividend reliability score"""
    score = 0
    
    try:
        # Check if company pays dividends
        dividend_yield = info.get("dividendYield", 0) or 0
        if dividend_yield <= 0:
            return 50  # Neutral score for growth stocks without dividends
        
        # Dividend yield (0-30 points)
        if dividend_yield > 0.04:
            score += 30
        elif dividend_yield > 0.03:
            score += 25
        elif dividend_yield > 0.02:
            score += 20
        elif dividend_yield > 0.01:
            score += 15
        
        # Payout ratio (0-35 points)
        payout_ratio = info.get("payoutRatio", 0) or 0
        if 0.2 < payout_ratio < 0.6:
            score += 35  # Sustainable range
        elif 0.1 < payout_ratio <= 0.7:
            score += 25
        elif payout_ratio > 0:
            score += 15
        
        # Dividend history (0-35 points)
        dividends = stock.dividends
        if len(dividends) > 0:
            years_of_dividends = (dividends.index[-1] - dividends.index[0]).days / 365
            if years_of_dividends >= 15:
                score += 35
            elif years_of_dividends >= 10:
                score += 30
            elif years_of_dividends >= 5:
                score += 25
            elif years_of_dividends >= 3:
                score += 20
            else:
                score += 10
    except:
        score = 50  # Default neutral score if calculation fails
    
    return min(score, 100)


def calculate_management_quality(info):
    """Calculate management quality score"""
    score = 0
    
    # Promoter/Insider holding (0-40 points)
    held_percent_insiders = info.get("heldPercentInsiders", 0) or 0
    if 0.2 < held_percent_insiders < 0.7:
        score += 40  # Good skin in the game
    elif 0.1 < held_percent_insiders:
        score += 30
    elif held_percent_insiders > 0:
        score += 20
    
    # Book value (indicator of asset quality) (0-30 points)
    book_value = info.get("bookValue", 0) or 0
    price_to_book = info.get("priceToBook", 100) or 100
    if 0 < price_to_book < 3:
        score += 30
    elif price_to_book < 5:
        score += 20
    elif price_to_book < 10:
        score += 10
    
    # Operating cash flow (0-30 points)
    operating_cashflow = info.get("operatingCashflow", 0) or 0
    free_cashflow = info.get("freeCashflow", 0) or 0
    if free_cashflow > 0 and operating_cashflow > 0:
        fcf_ratio = free_cashflow / operating_cashflow if operating_cashflow > 0 else 0
        if fcf_ratio > 0.7:
            score += 30
        elif fcf_ratio > 0.5:
            score += 20
        elif fcf_ratio > 0.3:
            score += 15
        elif fcf_ratio > 0:
            score += 10
    
    return min(score, 100)


def calculate_business_moat(info):
    """Calculate business moat/competitive advantage score"""
    score = 0
    
    # Market cap (size = moat) (0-25 points)
    market_cap = info.get("marketCap", 0) or 0
    if market_cap > 100_000_000_000:  # >$100B
        score += 25
    elif market_cap > 50_000_000_000:  # >$50B
        score += 20
    elif market_cap > 10_000_000_000:  # >$10B
        score += 15
    elif market_cap > 1_000_000_000:  # >$1B
        score += 10
    
    # Gross margins (pricing power indicator) (0-25 points)
    gross_margins = info.get("grossMargins", 0) or 0
    if gross_margins > 0.50:
        score += 25
    elif gross_margins > 0.40:
        score += 20
    elif gross_margins > 0.30:
        score += 15
    elif gross_margins > 0.20:
        score += 10
    
    # Current ratio (liquidity) (0-25 points)
    current_ratio = info.get("currentRatio", 0) or 0
    if current_ratio > 2.0:
        score += 25
    elif current_ratio > 1.5:
        score += 20
    elif current_ratio > 1.2:
        score += 15
    elif current_ratio > 1.0:
        score += 10
    
    # Return on Assets (efficiency) (0-25 points)
    roa = info.get("returnOnAssets", 0) or 0
    if roa > 0.10:
        score += 25
    elif roa > 0.07:
        score += 20
    elif roa > 0.05:
        score += 15
    elif roa > 0.03:
        score += 10
    
    return min(score, 100)


def calculate_risks(info, hist):
    """Identify key risks"""
    risks = []
    risk_level = "Low"
    
    # Volatility risk
    if len(hist) > 0:
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * (252 ** 0.5)  # Annualized
        if volatility > 0.40:
            risks.append("High volatility (40%+ annual)")
            risk_level = "High"
        elif volatility > 0.25:
            risks.append("Moderate volatility (25-40% annual)")
            risk_level = "Moderate"
    
    # Debt risk
    debt_to_equity = info.get("debtToEquity", 0) or 0
    if debt_to_equity > 100:
        risks.append("High debt levels (D/E > 1)")
        risk_level = "High" if risk_level != "High" else risk_level
    
    # Valuation risk
    pe_ratio = info.get("trailingPE", 0) or 0
    if pe_ratio > 40:
        risks.append("Expensive valuation (PE > 40)")
    
    # Sector-specific risks
    sector = info.get("sector", "")
    if sector in ["Energy", "Basic Materials"]:
        risks.append("Cyclical sector - commodity price dependent")
    
    if not risks:
        risks = ["Low risk profile", "Stable business model"]
        risk_level = "Low"
    
    return {"level": risk_level, "factors": risks}


def calculate_price_target(info, hist):
    """Calculate 5-10 year price target"""
    current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
    
    if not current_price or len(hist) < 252:
        return {
            "years_5": "N/A",
            "years_10": "N/A",
            "cagr": "N/A"
        }
    
    # Calculate historical CAGR
    try:
        old_price = hist['Close'].iloc[0]
        new_price = hist['Close'].iloc[-1]
        years = len(hist) / 252
        cagr = ((new_price / old_price) ** (1 / years) - 1) if old_price > 0 else 0
        
        # Conservative estimate (reduce by 20%)
        conservative_cagr = cagr * 0.8
        
        # Project future
        target_5y = current_price * ((1 + conservative_cagr) ** 5)
        target_10y = current_price * ((1 + conservative_cagr) ** 10)
        
        return {
            "years_5": round(target_5y, 2),
            "years_10": round(target_10y, 2),
            "cagr": round(conservative_cagr * 100, 1),
            "multiple": round(target_10y / current_price, 1)
        }
    except:
        return {
            "years_5": "N/A",
            "years_10": "N/A",
            "cagr": "N/A"
        }


def get_verdict(score):
    """Get investment verdict based on score"""
    if score >= 85:
        return {
            "text": "EXCELLENT LONG-TERM HOLD",
            "recommendation": "Strong Buy & Hold for 7-10 years",
            "emoji": "🟢"
        }
    elif score >= 70:
        return {
            "text": "GOOD LONG-TERM PROSPECT",
            "recommendation": "Buy & Hold for 5-7 years",
            "emoji": "🟢"
        }
    elif score >= 55:
        return {
            "text": "AVERAGE - PROCEED WITH CAUTION",
            "recommendation": "Suitable for diversification, 3-5 year hold",
            "emoji": "🟡"
        }
    else:
        return {
            "text": "WEAK FUNDAMENTALS",
            "recommendation": "Consider better alternatives for long-term",
            "emoji": "🔴"
        }


def get_grade(score):
    """Convert score to letter grade"""
    if score >= 90:
        return "A+"
    elif score >= 85:
        return "A"
    elif score >= 80:
        return "A-"
    elif score >= 75:
        return "B+"
    elif score >= 70:
        return "B"
    elif score >= 65:
        return "B-"
    elif score >= 60:
        return "C+"
    elif score >= 55:
        return "C"
    else:
        return "D"


def get_fundamental_details(info, stock):
    """Get detailed fundamental metrics"""
    revenue_growth = info.get("revenueGrowth", 0) or 0
    profit_margin = info.get("profitMargins", 0) or 0
    debt_to_equity = info.get("debtToEquity", 0) or 0
    roe = info.get("returnOnEquity", 0) or 0
    
    details = []
    
    if revenue_growth > 0.10:
        details.append(f"✅ Strong revenue growth: {revenue_growth*100:.1f}%")
    elif revenue_growth > 0:
        details.append(f"⚠️ Moderate revenue growth: {revenue_growth*100:.1f}%")
    else:
        details.append(f"❌ Declining revenue: {revenue_growth*100:.1f}%")
    
    if profit_margin > 0.10:
        details.append(f"✅ Healthy profit margin: {profit_margin*100:.1f}%")
    else:
        details.append(f"⚠️ Thin profit margin: {profit_margin*100:.1f}%")
    
    if debt_to_equity < 50:
        details.append(f"✅ Low debt: D/E {debt_to_equity:.1f}")
    elif debt_to_equity < 100:
        details.append(f"⚠️ Moderate debt: D/E {debt_to_equity:.1f}")
    else:
        details.append(f"❌ High debt: D/E {debt_to_equity:.1f}")
    
    if roe > 0.15:
        details.append(f"✅ Excellent ROE: {roe*100:.1f}%")
    elif roe > 0:
        details.append(f"⚠️ Moderate ROE: {roe*100:.1f}%")
    
    return details


def get_dividend_details(info, stock):
    """Get detailed dividend metrics"""
    dividend_yield = info.get("dividendYield", 0) or 0
    payout_ratio = info.get("payoutRatio", 0) or 0
    
    details = []
    
    if dividend_yield > 0:
        details.append(f"✅ Dividend yield: {dividend_yield*100:.2f}%")
        
        if 0.2 < payout_ratio < 0.6:
            details.append(f"✅ Sustainable payout: {payout_ratio*100:.0f}%")
        elif payout_ratio > 0:
            details.append(f"⚠️ Payout ratio: {payout_ratio*100:.0f}%")
        
        try:
            dividends = stock.dividends
            if len(dividends) > 0:
                years = (dividends.index[-1] - dividends.index[0]).days / 365
                details.append(f"✅ {int(years)} years of dividend history")
        except:
            pass
    else:
        details.append("ℹ️ No dividends (growth stock)")
    
    return details


def get_management_details(info):
    """Get management quality details"""
    held_percent_insiders = info.get("heldPercentInsiders", 0) or 0
    
    details = []
    
    if held_percent_insiders > 0.2:
        details.append(f"✅ Strong insider holding: {held_percent_insiders*100:.1f}%")
    elif held_percent_insiders > 0:
        details.append(f"⚠️ Moderate insider holding: {held_percent_insiders*100:.1f}%")
    
    free_cashflow = info.get("freeCashflow", 0)
    if free_cashflow and free_cashflow > 0:
        details.append("✅ Positive free cash flow")
    
    return details if details else ["ℹ️ Limited management data available"]


def get_moat_details(info):
    """Get business moat details"""
    market_cap = info.get("marketCap", 0) or 0
    gross_margins = info.get("grossMargins", 0) or 0
    
    details = []
    
    if market_cap > 50_000_000_000:
        details.append("✅ Large-cap company (market leader)")
    elif market_cap > 10_000_000_000:
        details.append("⚠️ Mid-cap company")
    
    if gross_margins > 0.40:
        details.append(f"✅ Strong pricing power: {gross_margins*100:.1f}% margin")
    elif gross_margins > 0.20:
        details.append(f"⚠️ Moderate margins: {gross_margins*100:.1f}%")
    
    sector = info.get("sector", "")
    if sector:
        details.append(f"ℹ️ Sector: {sector}")
    
    return details if details else ["ℹ️ Limited moat data available"]
