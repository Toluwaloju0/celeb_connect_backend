""" a module to define the booking prices """

import requests as re
import os

booking_prices = {
    "One-Time": 4372,
    "Vacation": 7680,
    "Long-Meet": 10200
}

def price_converter(booking_type: str):
    """ a function to convert booking prices to the appopraite bitcoin """

    response = re.get("https://api.coingecko.com/api/v3/simple/price?vs_currencies=usd&ids=bitcoin&names=Bitcoin&symbols=btc", headers={"x-cg-demo-api-key": os.getenv("COIN_GECKO_API")})

    data = response.json()

    amount = int(data.get("bitcoin").get("usd"))

    price = booking_prices.get(booking_type)

    return {
        "usd": price,
        "btc": round(price / amount, 3)
    }
