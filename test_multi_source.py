from data_fetcher import enhance_stock_info

# Test BHEL without suffix
print("Testing BHEL...")
info, stock, source, actual = enhance_stock_info('BHEL')
print(f"Source: {source}")
print(f"Actual Ticker: {actual}")
print(f"Company Name: {info.get('longName', 'N/A')}")
print(f"Sector: {info.get('sector', 'N/A')}")
print(f"Market Cap: {info.get('marketCap', 'N/A')}")
print()

# Test BHEL.BO directly
print("Testing BHEL.BO...")
info2, stock2, source2, actual2 = enhance_stock_info('BHEL.BO')
print(f"Source: {source2}")
print(f"Company Name: {info2.get('longName', 'N/A')}")
print(f"Sector: {info2.get('sector', 'N/A')}")
