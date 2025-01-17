import sys
import json
import yfinance as yf
import numpy
from datetime import datetime
import pytz
from forex_python.converter import CurrencyRates, CurrencyCodes
from gui_utils import GUIUtils as Utils

input_ticker = Utils.decrypt(sys.argv[1])

ticker = yf.Ticker(input_ticker)

company_name = input_ticker.replace("^", "") + "-INDEX"
if "longName" in ticker.info and ticker.info["longName"] is not None:
    company_name = ticker.info["longName"]

print(company_name)


# Value
history = ticker.history(period="1d", interval="1m")
i = -1
while i < 1000:
    if history.get("Close")[i]:
        worth = history.get("Close")[i]
        print(Utils.format_money(worth))

        # Value Symbol 
        codes = CurrencyCodes()
        print("|".join([str(ord(char)) for char in codes.get_symbol(ticker.info["currency"])]))

        # Converted
        rates = CurrencyRates()
        print(Utils.format_money(rates.convert(ticker.info["currency"], "EUR", worth)))
        break
    else:
        i += 1


# Local Time
timezone = pytz.timezone(ticker.info["exchangeTimezoneName"])
print(datetime.now(timezone).strftime("%d %B %Y"))
print(datetime.now(timezone).strftime("%z").replace("0", ""))


# Graph
history = ticker.history(period="1d", interval="1m")
dateArrRaw = list(history.index.values)
closeArr = []
splitArr = []
dividendsArr = []
for i in history.index:
    closeArr.append(Utils.formatClose(history.get("Close")[i]))
    splitArr.append(Utils.formatSplit(history.get("Stock Splits")[i]))
    dividendsArr.append(Utils.formatDividend(history.get("Dividends")[i]))

dateArr = []
for raw in dateArrRaw:
    dateArr.append(Utils.formatDate(raw, "day"))

dateArr = []
for raw in dateArrRaw:
    dateArr.append(datetime.utcfromtimestamp(raw.tolist()/1e9).strftime("%H:%M"))

print("|".join(dateArr))
print("|".join(closeArr))
print("|".join(splitArr))
print("|".join(dividendsArr))

sys.stdout.flush()
