import yfinance as yf

ticker = yf.Ticker('BHEL.BO')
info = ticker.info

print(f'Name: {info.get("longName", "N/A")}')
print(f'Sector: {info.get("sector", "N/A")}')
print(f'Symbol: {info.get("symbol", "N/A")}')
print(f'Has symbol key: {"symbol" in info}')
print(f'Info keys: {list(info.keys())[:10]}')

hist = ticker.history(period='5y')
print(f'Historical data rows: {len(hist)}')
