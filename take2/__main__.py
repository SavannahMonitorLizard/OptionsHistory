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

if platform.system() == "Windows":
    APISERVER = "https://sandbox.tradier.com"
else:
    APISERVER = "https://api.tradier.com"

HEADERS = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
# APISERVER = "https://sandbox.tradier.com" # Change here to use a different API

def request_history(symbol: str, start: str, end: str, jsonyes=False, interval="daily"):
    """Start and end should be formmated as %Y-%m-%d"""

    response = requests.get(f'{APISERVER}/v1/markets/history', params={'symbol': symbol, "interval": interval, 'start': start, 'end': end}, headers=HEADERS)

    history = response.json()
    
    if jsonyes:
        with open("history.json", "w") as write_file:
            json.dump(history, write_file, indent=4, sort_keys=True)
    
    return history

def request_options_chains(symbol: str, expiration: str, greeks=False, jsonyes=False):
    """Expiration should be formatted as %Y-%m-%d"""
    
    response = requests.get(f'{APISERVER}/v1/markets/options/chains', params={'symbol': symbol, "expiration": expiration, "greeks": greeks}, headers=HEADERS)

    options_chains = response.json()
    if jsonyes:
        with open("options_chains.json", "w") as write_file:
            json.dump(options_chains, write_file, indent=4, sort_keys=True)

    return options_chains

def request_chain(symbol: str, start: str, jsonyes=False):
    response = requests.get(f'{APISERVER}/v1/markets/history', params={'symbol': symbol, "start": start}, headers=HEADERS)

    chain = response.json()
    if jsonyes:
        with open("chain.json", "w") as write_file:
            json.dump(chain, write_file, indent=4, sort_keys=True)

    return chain

print(request_chain(SYMBOL, DATE))