from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance import Client, enums
from decimal import Decimal
import pandas as pd
import requests
# import talib
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
            quantity=f"{float(quantity):.5f}"
        )
        if side == "BUY":
            sel_quantity = order["origQty"]
            status = True

        if side == "SELL":
            status = False


    except BinanceAPIException as e:
        print('Exception: ', e.message)
        print('Exception_code: ', e.status_code)
    print(order)
    sel_quantity = order["origQty"]
    print("koin", order["origQty"])
    print("USDT", order["cummulativeQuoteQty"])


while True:
    symbol = "YGGUSDT"
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

    # Рахуємо МА
    # print(df['close'].rolling(window=7).mean().iloc[-1])
    df['MA7'] = df['close'].rolling(window=7).mean()
    df['MA25'] = df['close'].rolling(window=25).mean()

    # Отримуємо дані МА за останні 2 свічки
    prev_sma7, prev_sma25 = df["MA7"].iloc[-2], df["MA25"].iloc[-2]
    last_sma7, last_sma25 = df["MA7"].iloc[-1], df["MA25"].iloc[-1]

    print(df[['close', 'MA7', 'MA25']].tail(1))

    # Перший варік це чекати саме перетину, тоді купувати, чекати перетину та продавати
    # Можна заходити в ордер по серед зростання ціни, коли МА7 більша за МА25
    # Ну і далі вже моніторити, та чекати перетину для продажі.
    # Також, можна попробувати більш короткі періоди.
    # Ще можна отримувати дані загального тренду, по МА якіхось 50 або 100
    # І на основі цієї інфи, планувати роботу далі.

    # signal = None
    # if prev_sma7 < prev_sma25 and last_sma7 > last_sma25:
    #     signal = "BUY"
    # elif prev_sma7 > prev_sma25 and last_sma7 < last_sma25:
    #     signal = "SELL"

    if status:
        print('Куплено. ждедм продажу')
        # if df['MA7'].iloc[-1] < df['MA25'].iloc[-1]:
        if prev_sma7 > prev_sma25 and last_sma7 < last_sma25:
            print('Такі продаємо')
            order_operation(symbol, "SELL", sel_quantity)
        else:
            print('Ждемо сигналу на продаж')
    else:
        print('Ждем сигналу на купівлю')
        # if df['MA7'].iloc[-1] > df['MA25'].iloc[-1]:
        if prev_sma7 < prev_sma25 and last_sma7 > last_sma25:
            print('Сигнал на купівлю')
            info = client.get_symbol_info(symbol)
            price_step = float([f['tickSize'] for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0])
            qty_step = float([f['stepSize'] for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0])

            actual_price = df['close'].iloc[-1]
            adjusted_price = adjust_to_step(actual_price, price_step)
            qty = adjust_to_step(20 / adjusted_price, qty_step)

            print('qty', qty)
            order_operation(symbol, "BUY", qty)
        else:
            print('Купувати поки рано')

    #
    # if df['MA7'].iloc[-1] > df['MA25'].iloc[-1]:
    #     print('Сигнал на купівлю')
    #     if status:
    #         print('Але в нас вже куплено, чекаєм на продаж')
    #     else:
    #         info = client.get_symbol_info(symbol)
    #         price_step = float([f['tickSize'] for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0])
    #         qty_step = float([f['stepSize'] for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0])
    #
    #         actual_price = df['close'].iloc[-1]
    #         adjusted_price = adjust_to_step(actual_price, price_step)
    #         qty = adjust_to_step(20 / adjusted_price, qty_step)
    #
    #         print('qty', qty)
    #         order_operation(symbol, "BUY", qty)
    #
    # if df['MA7'].iloc[-1] < df['MA25'].iloc[-1]:
    #     print('Сигнал на продаж')
    #     if status:
    #         print('Такі продаємо')
    #         order_operation(symbol, "SELL", sel_quantity)
    #     else:
    #         print('Так а шо, треба родвать, а нема шо ( ')

    time.sleep(2)
