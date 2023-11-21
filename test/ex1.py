import yfinance

yahoo_data = yfinance.Ticker("RELIANCE.NS")

print(yahoo_data.info['date'])