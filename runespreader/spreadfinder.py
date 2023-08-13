import os
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import requests
import yaml
from clickhouse_driver import Client

from runespreader.main import Runespreader

config = yaml.load(open("/home/charles/.config/runespreader"), Loader=yaml.Loader)
profit_threshold = config.get("POTENTIAL_PROFIT")
discord_url = config.get("BOT_WEBHOOK")


def refresh_vol_list():
    r = Runespreader()
    v_data = r.get_volumes()
    timestamp = v_data["timestamp"]
    volumes = v_data["data"]
    symbols_to_track = []
    for uuid, volume in volumes.items():
        if volume >= int(config.get("DAILY_VOL_THRESHOLD")):
            symbols_to_track.append(r.get_name_for_id(uuid))
    return timestamp, symbols_to_track


deal_dict = {}
timestamp, symbols_to_track = refresh_vol_list()
while True:
    r = Runespreader()
    if timestamp - time.time() > 86400:
        timestamp, symbols_to_track = refresh_vol_list()
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
    rs_sells = client.execute(
        f"select low, lowTime, name, id from rs_sells where lowTime >= now() - interval 1 hour"
    )
    rs_buys = client.execute(
        f"select high, highTime, name, id from rs_buys where highTime >= now() - interval 1 hour"
    )
    high_df = pd.DataFrame(
        rs_buys, columns=["high", "high_time", "name", "id"]
    ).sort_values(["high_time"], ascending=False)
    low_df = pd.DataFrame(
        rs_sells, columns=["low", "low_time", "name", "id"]
    ).sort_values(["low_time"], ascending=False)
    for symbol in symbols_to_track:
        try:
            last_sell = low_df[low_df["name"] == symbol].iloc[0]
            last_buy = high_df[high_df["name"] == symbol].iloc[0]
        except:
            continue
        now = pd.Timestamp(datetime.utcnow()).floor(freq="S")
        if last_sell["low_time"] < now - pd.Timedelta("15 minutes") or last_buy[
            "high_time"
        ] < now - pd.Timedelta("15 minutes"):
            continue
        profit_per_item = (last_buy["high"] - (last_buy["high"] * 0.01)) - last_sell[
            "low"
        ]
        limit = r.name_to_limit.get(symbol)
        potential_profit = profit_per_item * limit
        if potential_profit >= profit_threshold:
            now = pd.Timestamp(datetime.utcnow()).floor(freq="S")
            if deal_dict.get(symbol, 0) < time.time() - 300:
                symbol_low_df = low_df[low_df["name"] == symbol]
                symbol_high_df = high_df[high_df["name"] == symbol]
                # 1 hour averages
                symbol_low_df_15m = symbol_low_df[
                    symbol_low_df["low_time"] > (now - pd.Timedelta("15 minutes"))
                ]
                symbol_high_df_15m = symbol_high_df[
                    symbol_high_df["high_time"] > (now - pd.Timedelta("15 minutes"))
                ]
                m15_low = symbol_low_df_15m["low"].mean()
                m15_high = symbol_high_df_15m["high"].mean()
                symbol_low_df_30m = symbol_low_df[
                    symbol_low_df["low_time"] > (now - pd.Timedelta("30 minutes"))
                ]
                symbol_high_df_30m = symbol_high_df[
                    symbol_high_df["high_time"] > (now - pd.Timedelta("30 minutes"))
                ]
                m30_low = symbol_low_df_30m["low"].mean()
                m30_high = symbol_high_df_30m["high"].mean()
                symbol_low_df_1h = symbol_low_df[
                    symbol_low_df["low_time"] > (now - pd.Timedelta("1 hour"))
                ]
                symbol_high_df_1h = symbol_high_df[
                    symbol_high_df["high_time"] > (now - pd.Timedelta("1 hour"))
                ]
                h1_low = symbol_low_df_1h["low"].mean()
                h1_high = symbol_high_df_1h["high"].mean()
                content = f"""
                ```
                    {symbol}
                    last_sell: {int(last_sell["low"])} @ {last_sell["low_time"]}
                    last_buy: {int(last_buy["high"])} @ {last_buy["high_time"]}
                    15m_sell_avg: {m15_low}
                    15m_buy_avg: {m15_high}
                    30m_sell_avg: {m30_low}
                    30m_buy_avg: {m30_high}
                    1h_sell_avg: {h1_low}
                    1h_buy_avg: {h1_high}
                    limit: {limit}
                    profit_per_item: {profit_per_item}
                    potential_profit: {potential_profit}
                ```
                """
                requests.post(discord_url, json={"content": content})
                # print(content)
                deal_dict[symbol] = time.time()
    print(deal_dict)
    time.sleep(5)
