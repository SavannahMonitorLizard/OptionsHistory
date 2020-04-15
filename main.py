import json
import pandas as pd
import numpy as np
import requests
from datetime import timedelta, date, datetime
import calendar
import math

with open("secrets.json") as json_file:
    token = json.load(json_file)["auth"]

HEADERS = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

def request(symbol: str, date: str):
    #options_chains = request_options_chains(symbol, next_friday(last_year(date)))
    call1 = put(symbol, date)
    print(call1)

def request_history(symbol: str, start: str, end: str):
    response = requests.get(f'https://sandbox.tradier.com/v1/markets/history', params={'symbol': symbol, 'start': start, 'end': end}, headers=HEADERS)

    history = response.json()
    with open("history.json", "w") as write_file:
        json.dump(history, write_file, indent=4, sort_keys=True)
    
    return history

def request_options_chains(symbol: str, expiration: str):
    response = requests.get(f'https://sandbox.tradier.com/v1/markets/options/chains', params={'symbol': symbol, "expiration": expiration}, headers=HEADERS)

    options_chains = response.json()
    with open("options_chains.json", "w") as write_file:
        json.dump(options_chains, write_file, indent=4, sort_keys=True)

    return options_chains

def request_chain(symbol: str):
    response = requests.get(f'https://sandbox.tradier.com/v1/markets/history', params={'symbol': symbol}, headers=HEADERS)

    chain = response.json()
    with open("chain.json", "w") as write_file:
        json.dump(chain, write_file, indent=4, sort_keys=True)
    
    return chain

def get_day_price(symbol: str, date):
    
    history = request_history(symbol, three_weeks_ago(datetime.strptime(date, '%Y-%m-%d')), three_weeks_ahead(datetime.strptime(date, '%Y-%m-%d')))

    for day in history["history"]["day"]:
        if day["date"] == date:
            price = day["high"]
            return price

def call(symbol: str, date: str):
    day = datetime.strptime(date, "%Y-%m-%d")
    day = get_friday_last_year(day).strftime("%y%m%d")
    chain = request_chain(f"{symbol}{day[0:2]}{day[2:4]}{day[4:6]}C{math.ceil(get_day_price(symbol, date)):05d}000")
    return chain

def put(symbol: str, date: str):
    day = datetime.strptime(date, "%Y-%m-%d")
    day = get_friday_last_year(day).strftime("%y%m%d")
    #chain = request_chain(f"{symbol}{day[0:2]}{day[2:4]}{day[4:6]}P{math.ceil(get_day_price(symbol, date)):05d}000")
    chain = request_chain("VZ200417P00056000")
    return chain

def third_fridays(d, n):
 
    def next_third_friday(d):
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
    d = last_year(d)
    d = next_friday(d)
    return d

def three_weeks_ago(d):
    return d - timedelta(days=21)

def three_weeks_ahead(d):
    return d + timedelta(days=21)

def last_year(d):
    return d - timedelta(days=365)

def next_friday(d):
    return d + timedelta((4-d.weekday()) % 7)

request("GOOGL", "2020-01-17")