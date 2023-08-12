from runespreader.main import Runespreader
import pandas as pd
from clickhouse_driver import Client
import os
import time
import yaml
import datetime
import pandas as pd
import requests
config = yaml.load(open('/home/charles/.config/runespreader'), Loader=yaml.Loader)
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
    client = Client(host='localhost', password=config.get("CH_PASSWORD"))
    rs_sells = client.execute(f"select low, lowTime, name, id from rs_sells where lowTime >= now() - interval 15 minute")
    rs_buys = client.execute(f"select high, highTime, name, id from rs_buys where highTime >= now() - interval 15 minute")
    high_df = pd.DataFrame(rs_buys, columns=['high', 'high_time', 'name','id']).sort_values(["high_time"], ascending=False)
    low_df = pd.DataFrame(rs_sells, columns=['low', 'low_time', 'name','id']).sort_values(["low_time"], ascending=False)
    for symbol in symbols_to_track:
        try:
            last_sell = low_df[low_df["name"] == symbol].iloc[0]
            last_buy = high_df[high_df["name"] == symbol].iloc[0]
        except:
            continue
        profit_per_item = (last_buy["high"] - (last_buy["high"] * .01)) - last_sell["low"]
        limit = r.name_to_limit.get(symbol)
        potential_profit = profit_per_item * limit
        if potential_profit >= profit_threshold:
            if deal_dict.get(symbol, 0) < time.time() - 300:
                content = f"""
                ```
                    {symbol}
                    last_sell: {int(last_sell["low"])} @ {last_sell["low_time"]}
                    last_buy: {int(last_buy["high"])} @ {last_buy["high_time"]}
                    limit: {limit}
                    profit_per_item: {profit_per_item}
                    potential_profit: {potential_profit}
                ```
                """
                requests.post(discord_url, json={"content":content})
                deal_dict[symbol] = time.time()
    print(deal_dict)
    time.sleep(5)
