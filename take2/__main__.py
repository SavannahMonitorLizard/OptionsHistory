import json, csv
import pandas as pd
import numpy as np
import requests
from datetime import timedelta, date, datetime
import calendar
import math
import platform

with open("secrets.json") as json_file:
    token = json.load(json_file)["auth"]

with open("config.json") as config_file:
    config_json = json.load(config_file)
    
    SYMBOL = config_json["symbol"]
    DATE = config_json["date"]

if platform.system().lower() == "windows":
    APISERVER = "https://sandbox.tradier.com"
else:
    APISERVER = "https://api.tradier.com"

HEADERS = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
# APISERVER = "https://sandbox.tradier.com" # Change here to use a different API
STRIKERANGE = 5 # Change here to get a larger or smaller range of options by their distance to the current price, number is percentage, percentage is 100 / x

def request_history(symbol: str, start: str, end: str, jsonyes=False, interval="daily"):
    """Start and end should be formmated as %Y-%m-%d"""

    response = requests.get(f'{APISERVER}/v1/markets/history', params={'symbol': symbol, "interval": interval, 'start': start, 'end': end}, headers=HEADERS)

    history = response.json()
    
    if jsonyes:
        with open("history.json", "w") as write_file:
            json.dump(history, write_file, indent=4, sort_keys=True)
    
    return history

def request_options_chains(symbol: str, expiration: str, greeks=False, jsonyes=False):
    """Expiration should be formatted as %Y-%m-%d
    NOTE: Only works for options in the future"""

    response = requests.get(f'{APISERVER}/v1/markets/options/chains', params={'symbol': symbol, "expiration": expiration, "greeks": greeks}, headers=HEADERS)

    options_chains = response.json()
    if jsonyes:
        with open("options_chains.json", "w") as write_file:
            json.dump(options_chains, write_file, indent=4, sort_keys=True)

    return options_chains

def request_chain(symbol: str, start: str, jsonyes=False):
    """Start should be formmated as %Y-%m-%d"""

    response = requests.get(f'{APISERVER}/v1/markets/history', params={'symbol': symbol, "start": start}, headers=HEADERS)

    chain = response.json()
    if jsonyes:
        with open("chain.json", "w") as write_file:
            json.dump(chain, write_file, indent=4, sort_keys=True)

    return chain

def create_call_option_symbol(symbol: str, date: str, strike: int):
    """Date should be formmated as %Y-%m-%d"""

    dateObj = datetime.strptime(date, "%Y-%m-%d")
    dateShort = dateObj.strftime("%y%m%d")

    return f"{symbol}{dateShort[0:2]}{dateShort[2:4]}{dateShort[4:6]}C{strike:05d}000"

def create_put_option_symbol(symbol: str, date: str, strike: int):
    """Date should be formmated as %Y-%m-%d"""

    dateObj = datetime.strptime(date, "%Y-%m-%d")
    dateShort = dateObj.strftime("%y%m%d")

    return f"{symbol}{dateShort[0:2]}{dateShort[2:4]}{dateShort[4:6]}P{strike:05d}000"

def get_date_strike(symbol: str, date: str):
    """Date should be formmated as %Y-%m-%d"""
    
    dateObj = datetime.strptime(date, "%Y-%m-%d")
    dateObjEnd = dateObj + timedelta(days=1)
    dateEnd = dateObjEnd.strftime("%Y-%m-%d")

    history = request_history(symbol, date, dateEnd)

    if history["history"] is not None:
        return history["history"]["day"]["close"], date
    else:
        dateObj = datetime.strptime(date, "%Y-%m-%d")
        dateObj = dateObj - timedelta(days=1)
        date = dateObj.strftime("%Y-%m-%d")
        return get_date_strike(symbol, date)

def call(symbol: str, date: str, csvyes=False, jsonyes=False):

    chain = []
    calls = []
    dates = []

    price, date = get_date_strike(symbol, date)
    price = math.floor(price)

    price_range = get_price_range(round(price - price / STRIKERANGE), round(price + price / STRIKERANGE))

    for price in price_range:
        
        option_chain = request_chain(create_call_option_symbol(symbol, date, price), datetime.strptime(date, "%Y-%m-%d") - timedelta(days=5))
        
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

            if csvyes:
                    
                f = open("call.csv", "w")
                f.truncate()
                f.close()

                with open("call.csv", "a+", newline="") as output_file:
                    wr = csv.writer(output_file)
                    
                    if not type(option_chain["history"]["day"]) == list:
                        wr.writerow([option_chain["history"]["day"]["high"], option_chain["history"]["day"]["date"], option_chain["history"]["day"]["strike"]])
                    else:
                        for i in range(len(option_chain["history"]["day"])):
                            wr.writerow([option_chain["history"]["day"][i]["high"], option_chain["history"]["day"][i]["date"], option_chain["history"]["day"][i]["strike"]])

    if jsonyes:
        with open("call.json", "w") as write_file:
            json.dump(chain, write_file, indent=4, sort_keys=True)

    return chain, calls, dates

def put(symbol: str, date: str, csvyes=False, jsonyes=False):

    chain = []
    puts = []
    dates = []

    price, date = get_date_strike(symbol, date)
    price = math.floor(price)

    price_range = get_price_range(round(price - price / STRIKERANGE), round(price + price / STRIKERANGE))

    for price in price_range:
        
        option_chain = request_chain(create_put_option_symbol(symbol, date, price), datetime.strptime(date, "%Y-%m-%d") - timedelta(days=5))
        
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

            if csvyes:

                f = open("put.csv", "w")
                f.truncate()
                f.close()

                with open("put.csv", "a+", newline="") as output_file:
                    wr = csv.writer(output_file)
                    
                    if not type(option_chain["history"]["day"]) == list:
                        wr.writerow([option_chain["history"]["day"]["high"], option_chain["history"]["day"]["date"], option_chain["history"]["day"]["strike"]])
                    else:
                        for i in range(len(option_chain["history"]["day"])):
                            wr.writerow([option_chain["history"]["day"][i]["high"], option_chain["history"]["day"][i]["date"], option_chain["history"]["day"][i]["strike"]])

    if jsonyes:
        with open("put.json", "w") as write_file:
            json.dump(chain, write_file, indent=4, sort_keys=True)

    return chain, puts, dates

def get_price_range(start: int, end: int):
    """Returns a list of the numbers start to end, inclusive"""

    return list(range(start, end + 1))

def get_week_price(symbol: str, date):
    """Given a symbol and a date, gets the high price of that week"""

    history = request_history(symbol, datetime.strptime(date, '%Y-%m-%d') - timedelta(days=5), (datetime.strptime(date, '%Y-%m-%d')) + timedelta(days=1))

    return history

def remove_dates(dictionary):

    new_dict = {}
    new_val = {}

    for k, v in dictionary.items():
        for key, value in v.items():
            if key != "date":
                new_val.setdefault(key, value)
        new_dict.setdefault(k, new_val)

    return new_dict

def get_add_the_money_strikes(symbol: str, date: str, chain):

    history = get_week_price(symbol, date)

    date_price = {}
    date_add_the_money = {}
    dates = []
    over = []
    day_prices = []
    final = {}

    for day in history["history"]["day"]:
        date_price.setdefault(day["date"], day["close"])

    for i in chain:
        if type(i["history"]["day"]) == list:
            for day in i["history"]["day"]:
                dates.append(day["date"])
                if day["strike"] > date_price[day["date"]]:
                    over.append(day)
        else:
            dates.append(i["history"]["day"]["date"])
            if i["history"]["day"]["strike"] > date_price[i["history"]["day"]["date"]]:
                over.append(i["history"]["day"])

    for i in list(set(dates)):
        day_prices = []
        day_price = []
        for e in over:
            if e["date"] == i:
                day_prices.append(e)

        for price in day_prices:
            day_price.append(price["strike"])

        day_price.sort()
        final.setdefault(i, day_price[0])

    return final

def get_add_the_money(symbol: str, date: str, strikes, chain):
    
    final = {}

    for i in chain:
        if type(i["history"]["day"]) == list:
            for day in i["history"]["day"]:
                for k, v in strikes.items():
                    if day["strike"] == v:
                        if k != "date":
                            final.setdefault(k, day)
        else:
            for k, v in strikes.items():
                    if i["history"]["day"]["strike"] == v:
                        if k != "date":
                            final.setdefault(k, i["history"]["day"])

    return final

chain, calls, dates = call(SYMBOL, DATE, jsonyes=True)

strikes = get_add_the_money_strikes(SYMBOL, DATE, chain)
add_the_money_call = get_add_the_money(SYMBOL, DATE, strikes, chain)

add_the_money_call = remove_dates(add_the_money_call)

with open("add_the_money_call.json", "w") as write_file:
    json.dump(add_the_money_call, write_file, indent=4, sort_keys=True)

chain, puts, dates = put(SYMBOL, DATE, jsonyes=True)

strikes = get_add_the_money_strikes(SYMBOL, DATE, chain)
add_the_money_put = get_add_the_money(SYMBOL, DATE, strikes, chain)

add_the_money_put = remove_dates(add_the_money_put)

with open("add_the_money_put.json", "w") as write_file:
    json.dump(add_the_money_put, write_file, indent=4, sort_keys=True)