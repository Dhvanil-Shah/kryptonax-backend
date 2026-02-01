from professional_fetcher import enhance_stock_info_professional

ticker = "BHEL.BO"
info, stock, source, actual_ticker = enhance_stock_info_professional(ticker)

print(f"Source: {source}")
print(f"Actual ticker: {actual_ticker}")
print(f"Has info: {bool(info)}")
print(f"Has stock: {bool(stock)}")
print(f"Symbol in info: {info.get('symbol') if info else 'NO INFO'}")
print(f"Long name: {info.get('longName') if info else 'NO INFO'}")
print(f"Info keys (first 10): {list(info.keys())[:10] if info else 'NO INFO'}")

# Test history
if stock:
    try:
        hist = stock.history(period="5y")
        print(f"Historical data rows: {len(hist)}")
    except Exception as e:
        print(f"History error: {e}")
