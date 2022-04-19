from indicators import send_get_request, calc_rsi, calc_macd

# timeframe in minutes
def get_price_and_rsi(timeframe, start=None, end=None):
    timeframe *= 60 # adjust minutes to seconds
    if start == None or end == None:
        url = "/markets/BTC-PERP/candles?resolution=" + str(timeframe)
    else:
        url = "/markets/BTC-PERP/candles?resolution=" + str(timeframe) + "&start_time=" + str(start) + "&end_time=" + str(end)
    res = send_get_request(url)
    prices = res["result"]

    rsi = calc_rsi(prices, 14, "close", True)

    # merge prices and RSI data into single list
    data = []
    # only get for candles that have closed
    for i in range(len(rsi)-1):
        data.append({"price": prices[i+16]["close"], "rsi": rsi[i]})

    return data

# h1_data = get_price_and_rsi(60)
# h4_data = get_price_and_rsi(240)
# d1_data = get_price_and_rsi(1440)

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

# # H1 
# buy_30_sell_70_h1 = rsi_strategy_1(h1_data, 30, 70) # profit = 3011 (26 trades)
# buy_25_sell_75_h1 = rsi_strategy_1(h1_data, 25, 75) # profit = 4270 (21 trades)
# buy_20_sell_80_h1 = rsi_strategy_1(h1_data, 20, 80) # profit = -9694 (9 trades)
# print(buy_30_sell_70_h1, buy_25_sell_75_h1, buy_20_sell_80_h1)

# # H4
# buy_30_sell_70_h4 = rsi_strategy_1(h4_data, 30, 70) # profit = -14252 (33 trades)
# buy_25_sell_75_h4 = rsi_strategy_1(h4_data, 25, 75) # profit = -6054 (17 trades)
# buy_20_sell_80_h4 = rsi_strategy_1(h4_data, 20, 80) # profit = 14793 (5 trades)
# print(buy_30_sell_70_h4, buy_25_sell_75_h4, buy_20_sell_80_h4)

# # D1
# buy_30_sell_70_d1 = rsi_strategy_1(d1_data, 30, 70) # profit = -10813 (26 trades)
# buy_25_sell_75_d1 = rsi_strategy_1(d1_data, 25, 75) # profit = 12658 (15 trades)
# buy_20_sell_80_d1 = rsi_strategy_1(d1_data, 20, 80) # profit = -12871 (7 trades)
# print(buy_30_sell_70_d1, buy_25_sell_75_d1, buy_20_sell_80_d1)