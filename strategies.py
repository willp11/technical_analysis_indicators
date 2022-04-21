from indicators import send_get_request, calc_rsi, calc_macd, calc_bollinger_bands

# timeframe in minutes
def get_price_and_rsi(market, timeframe, start=None, end=None):
    timeframe *= 60 # adjust minutes to seconds
    if start == None or end == None:
        url = "/markets/" + market + "/candles?resolution=" + str(timeframe)
    else:
        url = "/markets/" + market + "/candles?resolution=" + str(timeframe) + "&start_time=" + str(start) + "&end_time=" + str(end)
    res = send_get_request(url)
    prices = res["result"]

    rsi = calc_rsi(prices, 14, "close", True)

    # merge prices and RSI data into single list
    data = []
    # only get for candles that have closed
    for i in range(len(rsi)-1):
        data.append({"price": prices[i+16]["close"], "rsi": rsi[i]})

    return data

# possible RSI strategies:

# 1.
# buy signal: H4 moves from below 30 to above 30, stop if goes back below 30, target RSI above 70. 
# sell signal: vice versa
# data must be list of dicts {"price": , "rsi" }
def rsi_strategy_1(data, buy_threshold, sell_threshold):
    waiting_to_buy = False
    waiting_to_sell = False
    trades = []
    current_trade = None
    for i in range(len(data)):
        rsi = data[i]["rsi"]
        price = data[i]["price"]

        # BUY SIDE TRADES
        # start waiting to buy - not in a trade and move below buy_threshold
        if current_trade == None and rsi < buy_threshold:
            waiting_to_buy = True

        # buy signal - waiting to buy and move above buy_threshold
        if waiting_to_buy == True and rsi > buy_threshold:
            current_trade = {"side": "buy", "entry": price, "exit": None}
            waiting_to_buy = False

        # SELL SIDE TRADES
        # start waiting to sell - not in a trade and move above sell_threshold
        if current_trade == None and rsi > sell_threshold:
            waiting_to_sell = True

        # sell signal - waiting to sell and move below sell_threshold
        if waiting_to_sell == True and rsi < sell_threshold:
            current_trade = {"side": "sell", "entry": price, "exit": None}
            waiting_to_sell = False

        # exit trade - in trade and move below buy_threshold (stopped out buy side, take profit sell side) 
        # or above sell_threshold (take profit buy side, stopped out sell side)
        if current_trade != None and (rsi < buy_threshold or rsi > sell_threshold):
            current_trade["exit"] = price
            trades.append(current_trade)
            current_trade = None

    total_profit = 0
    for trade in trades:
        # buy side
        if trade["side"] == "buy":
            trade["profit"] = trade["exit"] - trade["entry"]
            total_profit += trade["profit"]
        elif trade["side"] == "sell":
            trade["profit"] = trade["entry"] - trade["exit"]
            total_profit += trade["profit"]
        trade["cum_profit"] = total_profit

    return {"total_profit": total_profit, "trades": trades}

# Bollinger bands strategy
# if price touches upper band, buy middle band, target upper band and stop half way to lower band
def bollinger_strategy(data):
    bollinger_bands = calc_bollinger_bands(data)
    trades = []
    trade = None
    order = None
    for band in bollinger_bands:
        # if not in a trade and haven't set an order - if price closes above upper band, set buy order at middle band
        if trade == None and band["close_price"] >= band["upper"]:
            order = {"side": "buy", "price": band["middle"]}
        
        # if have an order set, if candle low went below middle band then buy order hit
        if trade == None and order != None and band["low_price"] <= order["price"]:
            trade = {"side": "buy", "entry": order["price"], "exit": None}
            order = None
        
        # if in a trade, if candle low below half way between middle and lower bands - stop loss hit
        if trade != None and band["low_price"] <= (band["middle"] + band["lower"]) / 2:
            trade["exit"] = (band["middle"] + band["lower"]) / 2
            trades.append(trade)
            trade = None

        # if in a trade, if candle high above upper band - target hit
        if trade != None and band["high_price"] >= band["upper"]:
            trade["exit"] = band["upper"]
            trades.append(trade)
            trade = None

    total_profit = 0
    for trade in trades:
        if trade["side"] == "buy":
            trade["profit"] = trade["exit"] - trade["entry"]
            total_profit += trade["profit"]
        elif trade["side"] == "sell":
            trade["profit"] = trade["entry"] - trade["exit"]
            total_profit += trade["profit"]
        trade["cum_profit"] = total_profit

    return {"total_profit": total_profit, "trades": trades}

price_data = send_get_request("/markets/BTC-PERP/candles?resolution=3600")
bollinger_results = bollinger_strategy(price_data["result"])
print(bollinger_results)