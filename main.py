import json, csv
import pandas as pd
import numpy as np
import requests
from datetime import timedelta, date, datetime
import calendar
import math

with open("secrets.json") as json_file:
    token = json.load(json_file)["auth"]

with open("config.json") as config_file:
    SYMBOL = json.load(config_file)["symbol"]
    DATE = json.load(config_file)["date"]

HEADERS = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
APISERVER = "https://sandbox.tradier.com" # Change here to use a different API
STRIKERANGE = 5 # Change here to get a larger or smaller range of options by their distance to the current price, number is percentage, percentage is 100 / x

def request(symbol: str, date: str):
    chain, calls, dates = call(symbol, date)
    chain, puts, dates = put(symbol, date)

    write_csv(calls, dates, puts, chain)

def request_history(symbol: str, start: str, end: str):
    response = requests.get(f'{APISERVER}/v1/markets/history', params={'symbol': symbol, 'start': start, 'end': end}, headers=HEADERS)

    history = response.json()
    with open("history.json", "w") as write_file:
        json.dump(history, write_file, indent=4, sort_keys=True)
    
    return history

def request_options_chains(symbol: str, expiration: str):
    
    expiration = datetime.strptime(expiration, "%Y-%m-%d")
    expiration = get_friday_last_year(expiration).strftime("%y%m%d")
    
    response = requests.get(f'{APISERVER}/v1/markets/options/chains', params={'symbol': symbol, "expiration": expiration}, headers=HEADERS)

    options_chains = response.json()
    with open("options_chains.json", "w") as write_file:
        json.dump(options_chains, write_file, indent=4, sort_keys=True)

    return options_chains

def request_chain(symbol: str, start: str):
    response = requests.get(f'{APISERVER}/v1/markets/history', params={'symbol': symbol, "start": start}, headers=HEADERS)

    chain = response.json()
    
    return chain

def get_day_price(symbol: str, date):
    
    date = f"{date[:2]}-{date[2:4]}-{date[4:6]}"
    history = request_history(symbol, datetime.strptime(date, '%y-%m-%d'), (datetime.strptime(date, '%y-%m-%d')) + timedelta(days=1))

    return history["history"]["day"]["high"]

def call(symbol: str, date: str):
    
    chain = []
    calls = []
    dates = []

    day = datetime.strptime(date, "%Y-%m-%d")
    day = get_friday_last_year(day).strftime("%y%m%d")

    price = math.floor(get_day_price(symbol, day))
    price_range = get_price_range(round(price - price / STRIKERANGE), round(price + price / STRIKERANGE))

    for price in price_range:
        
        option_chain = request_chain(f"{symbol}{day[0:2]}{day[2:4]}{day[4:6]}C{price:05d}000", datetime.strptime(day, "%y%m%d") - timedelta(days=5))
        
        if not option_chain["history"] == None:

            if not type(option_chain["history"]["day"]) == list:
                calls.append(option_chain["history"]["day"]["high"])
                dates.append(option_chain["history"]["day"]["date"])
                option_chain["history"]["day"]["strike"] = price
            else:
                for i in range(len(option_chain["history"]["day"])):
                    calls.append(option_chain["history"]["day"][i]["high"])
                    dates.append(option_chain["history"]["day"][i]["date"])
                    option_chain["history"]["day"][i]["strike"] = price
    
            chain.append(option_chain)

    with open("call.json", "w") as write_file:
        json.dump(chain, write_file, indent=4, sort_keys=True)

    return chain, calls, dates

def put(symbol: str, date: str):
    
    chain = []
    puts = []
    dates = []

    day = datetime.strptime(date, "%Y-%m-%d")
    day = get_friday_last_year(day).strftime("%y%m%d")

    price = math.floor(get_day_price(symbol, day))
    price_range = get_price_range(round(price - price / STRIKERANGE), round(price + price / STRIKERANGE))

    for price in price_range:
        
        option_chain = request_chain(f"{symbol}{day[0:2]}{day[2:4]}{day[4:6]}P{price:05d}000", datetime.strptime(day, "%y%m%d") - timedelta(days=5))
        
        if not option_chain["history"] == None:

            if not type(option_chain["history"]["day"]) == list:
                puts.append(option_chain["history"]["day"]["high"])
                dates.append(option_chain["history"]["day"]["date"])
                option_chain["history"]["day"]["strike"] = price
            else:
                for i in range(len(option_chain["history"]["day"])):
                    puts.append(option_chain["history"]["day"][i]["high"])
                    dates.append(option_chain["history"]["day"][i]["date"])
                    option_chain["history"]["day"][i]["strike"] = price
    
            chain.append(option_chain)

    with open("put.json", "w") as write_file:
        json.dump(chain, write_file, indent=4, sort_keys=True)

    return chain, puts, dates

def write_csv(calls, dates, puts, chain):
    
    strikes = get_strikes(chain)

    with open("options.csv", "a+", newline="") as output_file:
        wr = csv.writer(output_file)
        for i in range(len(strikes)):
            wr.writerow([calls[i], dates[i], strikes[i], puts[i]])
        
def get_strikes(chain):
    
    strikes = []
    for i in range(len(chain)):
        
        if type(chain[i]["history"]["day"]) == list:
            
            for e in range(len(chain[i]["history"]["day"])):
                strikes.append(chain[i]["history"]["day"][e]["strike"])
        
        else:
            strikes.append(chain[i]["history"]["day"]["strike"])

    return strikes

def third_fridays(d, n):
    """Given a date, calculates n next third fridays
    https://stackoverflow.com/questions/28680896/how-can-i-get-the-3rd-friday-of-a-month-in-python/28681097"""

    def next_third_friday(d):
        """Given a third friday find next third friday"""

        d += timedelta(weeks=4)
        return d if d.day >= 15 else d + timedelta(weeks=1)

    s = date(d.year, d.month, 15)
    result = [s + timedelta(days=(calendar.FRIDAY - s.weekday()) % 7)]

    if result[0] < d:
        result[0] = next_third_friday(result[0])

    for i in range(n - 1):
        result.append(next_third_friday(result[-1]))
 
    return result[0]

def get_friday_last_year(d):
    """Given a date, d, finds the next friday of the date 365 days prior"""
    
    d = last_year(d)
    d = next_friday(d)
    return d

def three_weeks_ago(d):
    """Given a date, d, finds the date 3 weeks prior"""
    
    return d - timedelta(days=21)

def three_weeks_ahead(d):
    """Given a date, d, finds the date in 3 weeks"""
    
    return d + timedelta(days=21)

def last_year(d):
    """Given a date, d, finds the date 365 days prior"""
    
    return d - timedelta(days=365)

def next_friday(d):
    """Given a date, d, finds the date of the next friday"""
    
    return d + timedelta((4-d.weekday()) % 7)

def get_price_range(start: int, end: int):
    """Returns a list of the numbers start to end, inclusive"""

    return list(range(start, end + 1))

request(SYMBOL, DATE)