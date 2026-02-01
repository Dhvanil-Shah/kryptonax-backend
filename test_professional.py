from professional_fetcher import enhance_stock_info_professional
import json

# Test multiple stocks
test_stocks = ["JPM", "AAPL", "BHEL", "RELIANCE.NS"]

for ticker in test_stocks:
    print(f"\n{'='*60}")
    print(f"Testing: {ticker}")
    print(f"{'='*60}")
    
    info, stock, source, actual = enhance_stock_info_professional(ticker)
    
    print(f"Source: {source}")
    print(f"Actual Ticker: {actual}")
    print(f"Company Name: {info.get('longName', 'N/A')}")
    print(f"Sector: {info.get('sector', 'N/A')}")
    print(f"Market Cap: {info.get('marketCap', 'N/A')}")
    print(f"Has Data: {bool(info)}")
