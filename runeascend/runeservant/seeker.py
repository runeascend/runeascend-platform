import time
import urllib.parse
from datetime import datetime

import pandas as pd
import requests
from requests import get

from runeascend.common.clickhouse import get_clickhouse_client
from runeascend.common.config import get_config
from runeascend.runespreader.spreader import Runespreader


def embed_field(name, value):
    return {"name": name, "value": value, "inline": True}


def refresh_vol_list(config):
    r = Runespreader()
    v_data = r.get_volumes()
    timestamp = v_data["timestamp"]
    volumes = v_data["data"]
    symbols_to_track = []
    for uuid, volume in volumes.items():
        if volume >= int(config.get("DAILY_VOL_THRESHOLD")):
            symbols_to_track.append(r.get_name_for_id(uuid))
    return timestamp, symbols_to_track


def main():
    ip = get("https://api.ipify.org").content.decode("utf8")
    config = get_config()
    profit_threshold = config.get("POTENTIAL_PROFIT")
    discord_url = config.get("BOT_WEBHOOK")

    deal_dict = {}
    timestamp, symbols_to_track = refresh_vol_list(config)
    while True:
        r = Runespreader()
        if timestamp - time.time() > 86400:
            timestamp, symbols_to_track = refresh_vol_list()
        client = get_clickhouse_client()
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
            now = pd.Timestamp(datetime.utcnow()).floor(freq="s")
            if last_sell["low_time"] < now - pd.Timedelta(
                "15 minutes"
            ) or last_buy["high_time"] < now - pd.Timedelta("15 minutes"):
                continue
            profit_per_item = (
                last_buy["high"] - (last_buy["high"] * 0.01)
            ) - last_sell["low"]
            limit = r.name_to_limit.get(symbol)
            potential_profit = profit_per_item * limit
            if potential_profit >= profit_threshold:
                now = pd.Timestamp(datetime.utcnow()).floor(freq="s")
                if deal_dict.get(symbol, 0) < time.time() - 300:
                    symbol_low_df = low_df[low_df["name"] == symbol]
                    symbol_high_df = high_df[high_df["name"] == symbol]
                    # 1 hour averages
                    symbol_low_df_15m = symbol_low_df[
                        symbol_low_df["low_time"]
                        > (now - pd.Timedelta("15 minutes"))
                    ]
                    symbol_high_df_15m = symbol_high_df[
                        symbol_high_df["high_time"]
                        > (now - pd.Timedelta("15 minutes"))
                    ]
                    m15_low = symbol_low_df_15m["low"].mean()
                    m15_high = symbol_high_df_15m["high"].mean()
                    symbol_low_df_30m = symbol_low_df[
                        symbol_low_df["low_time"]
                        > (now - pd.Timedelta("30 minutes"))
                    ]
                    symbol_high_df_30m = symbol_high_df[
                        symbol_high_df["high_time"]
                        > (now - pd.Timedelta("30 minutes"))
                    ]
                    m30_low = symbol_low_df_30m["low"].mean()
                    m30_high = symbol_high_df_30m["high"].mean()
                    symbol_low_df_1h = symbol_low_df[
                        symbol_low_df["low_time"]
                        > (now - pd.Timedelta("1 hour"))
                    ]
                    symbol_high_df_1h = symbol_high_df[
                        symbol_high_df["high_time"]
                        > (now - pd.Timedelta("1 hour"))
                    ]
                    h1_low = symbol_low_df_1h["low"].mean()
                    h1_high = symbol_high_df_1h["high"].mean()

                    fields = []

                    fields.append(
                        embed_field(
                            "Last sell",
                            f'{int(last_sell["low"])} <t:{int(last_sell["low_time"].timestamp())}:R>',
                        )
                    )
                    fields.append(
                        embed_field(
                            "Last buy",
                            f'{int(last_buy["high"])} <t:{int(last_buy["high_time"].timestamp())}:R>',
                        )
                    )

                    fields.append(
                        embed_field("15m sell avg", str(int(m15_low)))
                    )
                    fields.append(
                        embed_field("15m buy avg", str(int(m15_high)))
                    )
                    fields.append(
                        embed_field("30m sell avg", str(int(m30_low)))
                    )
                    fields.append(
                        embed_field("30m buy avg", str(int(m30_high)))
                    )
                    fields.append(embed_field("1h sell avg", str(int(h1_low))))
                    fields.append(embed_field("1h buy avg", str(int(h1_high))))
                    fields.append(embed_field("Limit", str(int(limit))))
                    fields.append(
                        embed_field(
                            "Profit per item", str(int(profit_per_item))
                        )
                    )
                    fields.append(
                        embed_field(
                            "Potential profit", str(int(potential_profit))
                        )
                    )

                    embed = {}
                    embed["title"] = symbol
                    embed["fields"] = fields
                    embed["thumbnail"] = {
                        "url": f"https://oldschool.runescape.wiki/images/{symbol.replace(' ', '_')}.png?cache"
                    }
                    embed["description"] = (
                        f"[Open in Grafana](http://{ip}:13300/d/b1e39934-2a88-4e7d-9336-de298905e4a5/mind-the-gap?orgId=1&from=now-1h&to=now&refresh=30s&var-Items={urllib.parse.quote_plus(symbol)})"
                    )

                    if profit_per_item < 25:
                        embed["color"] = 0xE81515
                    elif profit_per_item < 100:
                        embed["color"] = 0xE8B915
                    else:
                        embed["color"] = 0x1AE815

                    requests.post(
                        discord_url,
                        json={"embeds": [embed]},
                    )
                    # print(content)
                    deal_dict[symbol] = time.time()
        print(deal_dict)
        time.sleep(5)


if __name__ == "__main__":
    main()
