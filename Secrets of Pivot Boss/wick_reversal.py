#%%
from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import mplfinance as mpf

tv = TvDatafeed()
# %%
ohlc_data = tv.get_hist("NIFTY", "NSE", Interval.in_daily, n_bars=5000, fut_contract=1)
# %%

ohlc_data = ohlc_data.assign(
    c_range=ohlc_data["high"] - ohlc_data["low"],
    c_body=ohlc_data["close"] - ohlc_data["open"],
    u_wick=ohlc_data["high"] - ohlc_data[["open", "close"]].max(axis=1),
    l_wick=ohlc_data[["open", "close"]].min(axis=1) - ohlc_data["low"],
)

# %%
close_crit = 0.35

ohlc_data["close_crit"] = np.where(
    ohlc_data["high"] - ohlc_data["close"] <= ohlc_data["c_range"] * close_crit,
    1,
    np.where(
        ohlc_data["close"] - ohlc_data["low"] <= ohlc_data["c_range"] * close_crit,
        -1,
        0,
    ),
)

ohlc_data["wb_r"] = (
    ohlc_data[["u_wick", "l_wick"]].max(axis=1) / ohlc_data["c_body"].abs()
)

thresold_wb_r = 3.5

ohlc_data["wb_r"] = ohlc_data["wb_r"].replace(np.inf, thresold_wb_r)

ohlc_data["wick_reversal"] = (ohlc_data["wb_r"] >= thresold_wb_r) * ohlc_data[
    "close_crit"
]

# %%
bullish_wick = ohlc_data["wick_reversal"].replace([-1, 0], np.nan)
bearish_wick = ohlc_data["wick_reversal"].replace([1, 0], np.nan)

addplot = [
    mpf.make_addplot(
        bullish_wick * ohlc_data["low"] * 0.99,
        type="scatter",
        marker="^",
        markersize=200,
    ),
    mpf.make_addplot(
        -bearish_wick * ohlc_data["high"] * 1.01,
        type="scatter",
        marker="v",
        markersize=200,
    ),
]

mpf.plot(ohlc_data, addplot=addplot, type="candle", style="yahoo")

# %%
window = 21

ohlc_data["hh"] = ohlc_data["high"].rolling(window=window).max()
ohlc_data["ll"] = ohlc_data["low"].rolling(window=window).min()

proximity = 0.2
bullish_wick = (
    (ohlc_data["wick_reversal"] == 1)
    & (
        ohlc_data["close"]
        <= ohlc_data["ll"] + proximity * (ohlc_data["hh"] - ohlc_data["ll"])
    )
).replace(False, np.nan)
bearish_wick = (
    (ohlc_data["wick_reversal"] == -1)
    & (
        ohlc_data["close"]
        >= ohlc_data["hh"] - proximity * (ohlc_data["hh"] - ohlc_data["ll"])
    )
).replace(False, np.nan)


addplot = [
    mpf.make_addplot(
        bullish_wick * ohlc_data["low"] * 0.99,
        type="scatter",
        marker="^",
        markersize=200,
    ),
    mpf.make_addplot(
        bearish_wick * ohlc_data["high"] * 1.01,
        type="scatter",
        marker="v",
        markersize=200,
    ),
    mpf.make_addplot(ohlc_data[["hh", "ll"]]),
]

mpf.plot(ohlc_data, addplot=addplot, type="candle", style="yahoo")


# %%


def wick_reversal_indicator(df: pd.DataFrame, window=21, proximity=0.2):
    df = df.assign(
        c_range=df["high"] - df["low"],
        c_body=df["close"] - df["open"],
        u_wick=df["high"] - df[["open", "close"]].max(axis=1),
        l_wick=df[["open", "close"]].min(axis=1) - df["low"],
    )

    close_crit = 0.35

    df["close_crit"] = np.where(
        df["high"] - df["close"] <= df["c_range"] * close_crit,
        1,
        np.where(
            df["close"] - df["low"] <= df["c_range"] * close_crit,
            -1,
            0,
        ),
    )

    df["wb_r"] = df[["u_wick", "l_wick"]].max(axis=1) / df["c_body"].abs()

    thresold_wb_r = 3.5

    df["wb_r"] = df["wb_r"].replace(np.inf, thresold_wb_r)

    df["wick_reversal"] = (df["wb_r"] >= thresold_wb_r) * df["close_crit"]

    # window = 21

    df["hh"] = df["high"].rolling(window=window).max()
    df["ll"] = df["low"].rolling(window=window).min()

    # proximity = 0.2
    bullish_wick = (df["wick_reversal"] == 1) & (
        df["close"] <= df["ll"] + proximity * (df["hh"] - df["ll"])
    )
    bearish_wick = (df["wick_reversal"] == -1) & (
        df["close"] >= df["hh"] - proximity * (df["hh"] - df["ll"])
    )

    df["wick_reversal"] = bullish_wick + bearish_wick * (-1)

    return df["wick_reversal"]


ohlc_data["wick_reversal"] = wick_reversal_indicator(ohlc_data)
# %%
ohlc_data["entry_signal"] = ohlc_data["wick_reversal"].shift()

ohlc_data["exit_signal"] = ohlc_data["wick_reversal"].shift(4)

ohlc_data["entry_price"] = ohlc_data["open"] * ohlc_data["entry_signal"].abs()
ohlc_data["exit_price"] = ohlc_data["close"] * ohlc_data["exit_signal"].abs()

ohlc_data['entry_price']=ohlc_data['entry_price'].replace(0,np.nan).ffill()

ohlc_data['pnl']=(ohlc_data['exit_price']-ohlc_data['entry_price'])*ohlc_data['exit_signal']
# %%
ohlc_data['dd']=ohlc_data['pnl'].cumsum()-ohlc_data['pnl'].cumsum().cummax()
# %%
