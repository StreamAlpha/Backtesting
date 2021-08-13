#%%
from historical_data import get
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import mplfinance as mpf

ohlc_data = get("TCS", "eq")
resampling_dict = {
    "open": "first",
    "high": "max",
    "low": "min",
    "close": "last",
    "volume": "sum",
}
ohlc_data = ohlc_data.resample("30min", offset="15min").apply(resampling_dict).dropna()
# %%
def extreme_reversal_indicator(df: pd.DataFrame, lookback=21):
    # calculate candlestick patameters
    df = df.assign(c_body=df["close"] - df["open"], c_range=df["high"] - df["low"])
    # calculate avg body size
    df["avg_candle_size"] = df["c_body"].abs().rolling(window=lookback).mean()
    # calculate body %
    df["body_pct"] = df["c_body"].abs() / df["c_range"]
    # calculate candle color
    df["c_color"] = df["c_body"].apply(np.sign)
    # find out when candle body > 2* avg candle size
    df["cond_1"] = df["c_body"].abs() > df["avg_candle_size"] * 2
    # find when body to range is bw 0.5 to 0.85
    df["cond_2"] = (df["body_pct"] > 0.5) & (df["body_pct"] < 0.85)

    # find out when todays candle and yesterdays candle are opposing
    df["cond_3"] = df["c_color"] != df["c_color"].shift()

    # combine all three conditions

    df["extreme_reversal"] = df["cond_1"].shift() & df["cond_2"].shift() & df["cond_3"]

    df["extreme_reversal"] = df["extreme_reversal"] * df["c_color"]

    return df["extreme_reversal"]


ohlc_data["extreme_reversal"] = extreme_reversal_indicator(ohlc_data)
# %%
bullish_reversal = ohlc_data["extreme_reversal"].replace([-1, 0], np.nan)
bearish_reversal = ohlc_data["extreme_reversal"].replace([1, 0], np.nan)

bullish_reversal = bullish_reversal * bullish_reversal.index.map(
    lambda x: 1 if x.time() < datetime.time(10, 15) else np.nan
)
bearish_reversal = bearish_reversal * bearish_reversal.index.map(
    lambda x: 1 if x.time() < datetime.time(10, 15) else np.nan
)
addplot = [
    mpf.make_addplot(
        bullish_reversal * ohlc_data["low"] * 0.99,
        type="scatter",
        marker="^",
        markersize=200,
    ),
    mpf.make_addplot(
        -bearish_reversal * ohlc_data["high"] * 1.01,
        type="scatter",
        marker="v",
        markersize=200,
    ),
]

mpf.plot(
    ohlc_data,
    addplot=addplot,
    style="yahoo",
    type="candle",
    scale_padding=dict(left=0.25, right=0.6, top=0.5, bottom=0.6),
)

# %%
entry_time = datetime.time(10, 15)

signal = (
    ohlc_data[ohlc_data.index.time < entry_time]["extreme_reversal"]
    .resample("D")
    .last()
    .dropna()
)

entry_price = (
    ohlc_data[ohlc_data.index.time >= entry_time]["open"].resample("D").first().dropna()
)

exit_price = (
    ohlc_data[ohlc_data.index.time >= entry_time]["close"].resample("D").last().dropna()
)


tradelog = pd.concat(
    [signal, entry_price, exit_price],
    keys=["signal", "entry_price", "exit_price"],
    axis=1,
)

tradelog = tradelog[tradelog["signal"] != 0].dropna()

tradelog["pnl"] = (tradelog["exit_price"] - tradelog["entry_price"]) * tradelog[
    "signal"
]

tradelog["returns"] = tradelog["pnl"] / tradelog["entry_price"]

tradelog["returns"].cumsum().plot()
# %%


def calculate_metrics(returns: pd.Series):
    returns = returns.dropna()

    metrics = pd.DataFrame(columns=["value"])
    metrics.loc["gross_return"] = returns.sum()

    metrics.loc["total_trades"] = len(returns)
    metrics.loc["no_of_winning_trades"] = (returns > 0).sum()
    metrics.loc["no_of_losing_trades"] = (returns <= 0).sum()
    metrics.loc["avg_profit_winners"] = returns[returns > 0].mean()
    metrics.loc["avg_loss_losers"] = returns[returns <= 0].mean()
    metrics.loc["avg_profit"] = returns.mean()

    metrics.loc["win_rate"] = sum(returns > 0) / len(returns)
    metrics.loc["win_loss_ratio"] = (
        metrics.loc["avg_profit_winners"] / metrics.loc["avg_loss_losers"].abs()
    )

    return metrics


calculate_metrics(tradelog["returns"])
# %%

import pynse

symbols_list = pynse.Nse().symbols[pynse.IndexSymbol.Nifty100.name]

# %%

for symbol in symbols_list:

    ohlc_data = get(symbol, "eq")

    ohlc_data = (
        ohlc_data.resample("30min", offset="15min").apply(resampling_dict).dropna()
    )

    ohlc_data["extreme_reversal"] = extreme_reversal_indicator(ohlc_data)
    # %%
    bullish_reversal = ohlc_data["extreme_reversal"].replace([-1, 0], np.nan)
    bearish_reversal = ohlc_data["extreme_reversal"].replace([1, 0], np.nan)

    bullish_reversal = bullish_reversal * bullish_reversal.index.map(
        lambda x: 1 if x.time() < datetime.time(10, 15) else np.nan
    )
    bearish_reversal = bearish_reversal * bearish_reversal.index.map(
        lambda x: 1 if x.time() < datetime.time(10, 15) else np.nan
    )
    addplot = [
        mpf.make_addplot(
            bullish_reversal * ohlc_data["low"] * 0.99,
            type="scatter",
            marker="^",
            markersize=200,
        ),
        mpf.make_addplot(
            -bearish_reversal * ohlc_data["high"] * 1.01,
            type="scatter",
            marker="v",
            markersize=200,
        ),
    ]

    mpf.plot(
        ohlc_data,
        addplot=addplot,
        style="yahoo",
        type="candle",
        scale_padding=dict(left=0.25, right=0.6, top=0.5, bottom=0.6),
    )

    # %%
    entry_time = datetime.time(10, 15)

    signal = (
        ohlc_data[ohlc_data.index.time < entry_time]["extreme_reversal"]
        .resample("D")
        .last()
        .dropna()
    )

    entry_price = (
        ohlc_data[ohlc_data.index.time >= entry_time]["open"]
        .resample("D")
        .first()
        .dropna()
    )

    exit_price = (
        ohlc_data[ohlc_data.index.time >= entry_time]["close"]
        .resample("D")
        .last()
        .dropna()
    )

    tradelog = pd.concat(
        [signal, entry_price, exit_price],
        keys=["signal", "entry_price", "exit_price"],
        axis=1,
    )

    tradelog = tradelog[tradelog["signal"] != 0].dropna()

    tradelog["pnl"] = (tradelog["exit_price"] - tradelog["entry_price"]) * tradelog[
        "signal"
    ]

    tradelog["returns"] = tradelog["pnl"] / tradelog["entry_price"]
