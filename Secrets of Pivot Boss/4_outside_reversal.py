#%%
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import numpy as np
import datetime

import matplotlib.pyplot as plt
import mplfinance as mpf

# %%
ohlc_data = TvDatafeed().get_hist("NIFTY", "NSE", n_bars=5000, fut_contract=1)
# %%


def outside_reversal_indicator(df: pd.DataFrame, lookback=21):
    # claculate the candle range for size comparision
    c_range = df["high"] - df["low"]

    # bullish reversal : lk<l[1] and c>h[1]
    bullish_reversal = (df["low"] < df["low"].shift()) & (
        df["close"] > df["high"].shift()
    )

    # bearish reversal" h>h[1] and c<l[1]
    bearish_reversal = (df["high"] > df["high"].shift()) & (
        df["close"] < df["low"].shift()
    )

    # join bullish and bearish reversal
    cond_1 = bullish_reversal * 1 - bearish_reversal * 1

    # compare the size of engulfing bar
    cond_2 = c_range > c_range.rolling(window=lookback).mean() * 1.25

    outside_reversal = cond_1 * cond_2

    return outside_reversal


ohlc_data["outside_reversal"] = outside_reversal_indicator(ohlc_data)
# %%
bullish_reversal = ohlc_data["outside_reversal"].replace([-1, 0], np.nan)
bearish_reversal = ohlc_data["outside_reversal"].replace([1, 0], np.nan)

addplot = [
    mpf.make_addplot(
        bullish_reversal * ohlc_data["low"] * 0.99,
        type="scatter",
        marker="^",
        markersize=200,
    ),
    mpf.make_addplot(
        bearish_reversal * ohlc_data["high"] * (-1.01),
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


def price_channel_indicator(df: pd.DataFrame, lookback=21):
    ub = df["high"].rolling(window=lookback).max()
    lb = df["low"].rolling(window=lookback).min()

    ub.name = "ub"
    lb.name = "lb"

    return ub, lb


price_channel = price_channel_indicator(ohlc_data)

addplot = [mpf.make_addplot(price_channel[0]), mpf.make_addplot(price_channel[1])]
mpf.plot(
    ohlc_data,
    addplot=addplot,
    style="yahoo",
    type="candle",
    scale_padding=dict(left=0.25, right=0.6, top=0.5, bottom=0.6),
)
# %%


def doji_reversal_indicator(df: pd.DataFrame):
    # calcualte the candlestick range and body size
    c_range = df["high"] - df["low"]
    c_body = (df["close"] - df["open"]).abs()

    # find all doji candles , body<range*0.1
    doji = c_body <= c_range * 0.1

    # compare doji high/low with sma
    bullish_doji_c1 = doji & (df["high"] < df["close"].rolling(window=10).mean())

    # check of confirmation candles
    bullish_doji = (bullish_doji_c1.shift() & (df["close"] > df["high"].shift())) | (
        bullish_doji_c1.shift(2) & (df["close"] > df["high"].shift(2))
    )

    bearish_doji_c1 = doji & (df["low"] > df["close"].rolling(window=10).mean())

    bearish_doji = (bearish_doji_c1.shift() & (df["close"] < df["low"].shift())) | (
        bearish_doji_c1.shift(2) & (df["close"] < df["low"].shift(2))
    )

    doji_reversal = bullish_doji * 1 - bearish_doji * 1

    return doji_reversal


ohlc_data["doji_reversal"] = doji_reversal_indicator(ohlc_data)
# %%
bullish_reversal = ohlc_data["doji_reversal"].replace([-1, 0], np.nan)
bearish_reversal = ohlc_data["doji_reversal"].replace([1, 0], np.nan)

addplot = [
    mpf.make_addplot(
        bullish_reversal * ohlc_data["low"] * 0.99,
        type="scatter",
        marker="^",
        markersize=200,
    ),
    mpf.make_addplot(
        bearish_reversal * ohlc_data["high"] * (-1.01),
        type="scatter",
        marker="v",
        markersize=200,
    ),
    mpf.make_addplot(ohlc_data["close"].rolling(window=10).mean()),
]
mpf.plot(
    ohlc_data,
    addplot=addplot,
    style="yahoo",
    type="candle",
    scale_padding=dict(left=0.25, right=0.6, top=0.5, bottom=0.6),
)
# %%
