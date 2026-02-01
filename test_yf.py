import yfinance as yf
import time

print("Testing yfinance...")
time.sleep(1)

t = yf.Ticker('AAPL')
info = t.info

print(f"Company: {info.get('longName', 'N/A')}")
print(f"Sector: {info.get('sector', 'N/A')}")
print(f"Employees: {info.get('fullTimeEmployees', 'N/A')}")
