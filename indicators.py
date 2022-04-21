import requests
import numpy as np

ohlc_types = ["open", "high", "low", "close"]

# function to get data from FTX exchange API
api_prefix = "https://ftx.com/api"

def send_get_request(endpoint):
    api_prefix = "https://ftx.com/api"
    url = api_prefix + endpoint
    response = requests.request("GET", url)
    return response.json()

# calculate simple moving averages - input data as slice FTX result and "open", "high", "low", "close"
def calc_sma(data, ohlc):
    periods = len(data)
    sum_price = 0
    for i in range(periods):
        sum_price += data[i][ohlc]
    avg = sum_price / periods
    return avg

# calculate exponential moving averages - input data as FTX result, no. of periods and "open", "high", "low", "close"
def calc_next_ema(today, yesterday, multiplier):
    ema = (today * multiplier) + (yesterday * (1-multiplier))
    return ema

def calc_ema(data, periods, ohlc, return_all):
    # data length check
    if len(data) < periods:
        raise Exception("not enough data")
    
    all_ema = []
    ema = calc_sma(data[0:periods], ohlc)
    all_ema.append(ema)
    multiplier = 2/(periods+1)
    for i in range(periods, len(data)):
        ema = calc_next_ema(data[i][ohlc], ema, multiplier)
        all_ema.append(ema)
        
    if return_all:
        return all_ema
    else:
        return ema

# calculate Relative Strength Index (RSI) - input data as FTX result, no. of periods and "open", "high", "low", "close", return list boolean
# returns either single rsi value or list of all calculated rsi values

def calc_rsi_step_one(data, periods, ohlc):
    total_gain = 0
    total_loss = 0
    for i in range(periods):
        change = data[i+1][ohlc] - data[i][ohlc]
        if change > 0:
            total_gain += change
        else: 
            total_loss += abs(change)
    avg_gain = total_gain / periods
    avg_loss = total_loss / periods
    
    rsi = 100 - (100 / (1 + (avg_gain / avg_loss)) )
    return {"avg_gain": avg_gain, "avg_loss": avg_loss, "rsi": rsi}
                 
def calc_rsi(data, periods, ohlc, return_all: bool):
    # type checks
    if type(return_all) is not bool or type(data) is not list or type(periods) is not int or ohlc not in ohlc_types:
        raise Exception("invalid input type")
    # data length check
    if len(data) < periods + 1:
        raise Exception("not enough data")
    
    # calculate rsi
    rsi_step_one = calc_rsi_step_one(data, periods, ohlc)
    if len(data) == periods + 1:
        return [rsi_step_one["rsi"]]
    else:
        all_rsi = []
        previous_avg_gain = rsi_step_one["avg_gain"]
        previous_avg_loss = rsi_step_one["avg_loss"]
        for i in range(periods + 1, len(data) - 1):
            change = data[i+1][ohlc] - data[i][ohlc]

            if change > 0:
                current_gain = change
                current_loss = 0
            elif change < 0:
                current_loss = abs(change)
                current_gain = 0
            else:
                current_gain = 0
                current_loss = 0
                
            avg_gain = ((previous_avg_gain*13) + current_gain) / 14
            avg_loss = ((previous_avg_loss*13) + current_loss) / 14
            
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + (rs)) )
            else:
                rsi = 100
                
            previous_avg_gain = avg_gain
            previous_avg_loss = avg_loss
            
            all_rsi.append(rsi)

        if return_all:
            return all_rsi
        else:
            return rsi

# Moving average convergence divergence (MACD)
def calc_macd(data, short_period, long_period):
    all_short_ema = calc_ema(data, short_period, "close", True)
    all_long_ema = calc_ema(data, long_period, "close", True)
    all_macds = []
    diff_in_periods = long_period - short_period
    for i in range(len(all_long_ema)):
        short_ema = all_short_ema[i + diff_in_periods]
        long_ema = all_long_ema[i]
        macd = short_ema - long_ema
        all_macds.append(macd)
    
    # signal line - 9 day EMA of macd line
    periods = 9
    sum_macd = 0
    for i in range(periods):
        sum_macd += all_macds[i]
    ema = sum_macd / periods

    signal_line = []
    signal_line.append(ema)
    
    multiplier = 2/(periods+1)
    for i in range(periods, len(all_macds)):
        ema = calc_next_ema(all_macds[i], ema, multiplier)
        signal_line.append(ema)
        
    macd_line = all_macds[len(all_macds) - 1]
    signal_line = signal_line[len(signal_line) - 1]
    
    return {"macd_line": macd_line, "signal_line": signal_line}

# Bollinger bands
def calc_bollinger_bands(data):
    # remove extra ohlc values so we can easily calc. std dev using numpy
    data_list = []
    for val in data:
        data_list.append(val["close"])

    # we want the bollinger band for all periods
    bands = []
    for i in range(len(data)-20):
        middle = calc_sma(data[i:20+i], "close")
        std_dev = np.std(data_list[i:20+i])
        upper = middle + (std_dev * 2)
        lower = middle - (std_dev * 2)
        band = {"upper": upper, "middle": middle, "lower": lower, "close_price": data[i+19]["close"], "high_price": data[i+19]["high"], "low_price": data[i+19]["low"]}
        bands.append(band)

    return bands

price_data = send_get_request("/markets/BTC-PERP/candles?resolution=3600")
bollinger_bands = calc_bollinger_bands(price_data["result"])
print(bollinger_bands[-1:])