import yfinance as yf

tickers = ['BHEL.BO', 'RELIANCE.NS', 'TCS.NS', 'AAPL', 'MSFT']

print('Testing realtime data availability:\n')
for t in tickers:
    ticker_obj = yf.Ticker(t)
    info = ticker_obj.info
    print(f'{t:12} - {info.get("longName", "No data"):40} | Sector: {info.get("sector", "N/A")}')
    print(f'             Employees: {info.get("fullTimeEmployees", "N/A")} | Has Officers: {bool(info.get("companyOfficers"))}')
    print()
