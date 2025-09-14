from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance import Client, enums
from decimal import Decimal
import pandas as pd
import requests
import talib
import json
import time


api_key = 'yDUH4jCbm8wfnvKPcTY13ZzVIvPl1F8RhGndvkAH2NnzOEflULwmhf9VjSemKfN4'
api_secret = 'S3MiHMxL0VPAhd4X0RylPDrJ1ma6DPxwE23PXPl9Ntae0L2y79PV1fCQQDtBSK1W'
client = Client(api_key, api_secret, testnet=True)


sel_quantity = 0
status = False

def adjust_to_step(value, step):
    step = Decimal(str(step))
    return float((Decimal(str(value)) // step) * step)


def order_operation(symbol, side, quantity):
    global sel_quantity
    global status

    try:
        order = client.create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=f"{quantity:.5f}"
        )
        if side == "BUY":
            print('BUY')

        if side == "SELL":
            print('SELL')

    except BinanceAPIException as e:
        print('Exception: ', e.message)
        print('Exception_code: ', e.status_code)
    print(order)
    sel_quantity = order["origQty"]
    print("koin", order["origQty"])
    print("USDT", order["cummulativeQuoteQty"])


while True:
    symbol = "TWTUSDT"
    # Завантаження даних з Binance (BTCUSDT, 1h, 200 свічок)
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1m",
        "limit": 50
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Створюємо DataFrame
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "trades",
        "taker_base_volume", "taker_quote_volume", "ignore"
    ])

    # Використаємо тільки ціни закриття
    df['close'] = df['close'].astype(float)

    df['MA7'] = df['close'].rolling(window=7).mean()
    df['MA25'] = df['close'].rolling(window=25).mean()

    print(df[['close', 'MA7', 'MA25']].tail(1))
    if df['MA7'] > df['MA25']:
        info = client.get_symbol_info(symbol)
        price_step = float([f['tickSize'] for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0])
        qty_step = float([f['stepSize'] for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0])

        actual_price = df['close'].iloc[-1]
        adjusted_price = adjust_to_step(actual_price, price_step)
        qty = adjust_to_step(20 / adjusted_price, qty_step)

        order_operation(symbol, "BUY", qty)

    time.sleep(2)