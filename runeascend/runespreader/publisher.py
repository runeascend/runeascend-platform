import json
import logging
import os
from datetime import datetime, timedelta

import pandas as pd
import structlog
from kafka import KafkaProducer
from twisted.internet import reactor, task

from runeascend.common.clickhouse import get_clickhouse_client
from runeascend.common.config import get_config
from runeascend.common.http import get_session
from runeascend.runespreader.spreader import Runespreader


def refresh_vol_list(config):
    r = Runespreader()
    v_data = r.get_volumes()
    timestamp = v_data["timestamp"]
    volumes = v_data["data"]
    symbols_to_track = {}
    for uuid, volume in volumes.items():
        if volume >= int(config.get("DAILY_VOL_THRESHOLD")):
            symbols_to_track[r.get_name_for_id(uuid)] = volume
    return timestamp, symbols_to_track


class publisher:
    def __init__(self, config, topic, base_iterations=60):
        self.config = config
        self.topic = topic
        self.base_iterations = base_iterations
        self.iterations = 0
        self.client = get_clickhouse_client()
        self.r = Runespreader()
        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO)
        )
        self.logger = structlog.get_logger()

    def publish(self, key, message):
        self.producer.send(
            topic=self.topic, key=str(key).encode("utf-8"), value=message
        )
        self.logger.debug("published_message", message=message, key=key)

    def create_message(self):
        pass

    def refresh(self):
        self.logger.info("Refreshing data, client TTL Expired")
        self.r = Runespreader()

    def run(self):
        self.logger.info("Publisher running", publisher=self.topic)
        self.iterations -= 1
        if self.iterations < 0:
            self.refresh()
            self.iterations = self.base_iterations

        key, value = self.create_message()
        self.publish(key, value)
        return 0


class ref_data_publisher(publisher):
    def __init__(self, config):
        super().__init__(config, "osrs-ref-data")

    def create_message(self):
        limits = self.r.name_to_limit
        mappings = {k: int(v) for k, v in self.r.name_to_id_mapping.items()}
        timestamp, high_volume_symbols = refresh_vol_list(self.config)
        value = {
            "limits": limits,
            "mappings": mappings,
            "high_volume_symbols": high_volume_symbols,
        }
        return timestamp, value


class mkt_data_publisher(publisher):
    def __init__(self, config):
        super().__init__(config, "osrs-mkt-data")

    def gather_data(self):
        data_array = []
        s = get_session()
        latest_data_dict = (
            s.get(
                f"https://prices.runescape.wiki/api/v1/osrs/latest/",
                headers=self.r.custom_headers,
                timeout=1,
            )
            .json()
            .get("data")
        )
        volume_data_dict = (
            s.get(
                f"https://prices.runescape.wiki/api/v1/osrs/5m/",
                headers=self.r.custom_headers,
                timeout=1,
            )
            .json()
            .get("data")
        )
        for entry_key, entry_val in latest_data_dict.items():
            entry_val["name"] = self.r.get_name_for_id(int(entry_key))
            entry_val["time"] = datetime.now().isoformat()
            entry_val["id"] = int(entry_key)
            entry_val.update(volume_data_dict.get(entry_key, {}))
            if (
                not entry_val.get("high")
                or not entry_val.get("low")
                or not entry_val.get("name")
            ):
                continue
            entry_val["avg_high_price"] = (
                entry_val.get("avgHighPrice", 0)
                if isinstance(entry_val.get("avgHighPrice"), int)
                else 0
            )
            entry_val["avg_low_price"] = (
                entry_val.get("avgLowPrice", 0)
                if isinstance(entry_val.get("avgLowPrice"), int)
                else 0
            )
            entry_val["high_price_volume"] = entry_val.get("highPriceVolume", 0)
            entry_val["low_price_volume"] = entry_val.get("lowPriceVolume", 0)
            entry_val["high_time"] = datetime.fromtimestamp(
                entry_val.get("highTime", 0)
            ).isoformat()
            entry_val["low_time"] = datetime.fromtimestamp(
                entry_val.get("lowTime", 0)
            ).isoformat()
            keys_to_drop = [
                "highTime",
                "lowTime",
                "avgHighPrice",
                "avgLowPrice",
                "highPriceVolume",
                "lowPriceVolume",
            ]
            entry_val = {
                k: v for k, v in entry_val.items() if k not in keys_to_drop
            }
            data_array.append(entry_val)
        return data_array

    def create_message(self, symbol_data):
        key = str(symbol_data["id"])
        value = symbol_data
        return key, value

    def run(self):
        self.logger.info("Publisher running", publisher="mkt_data")
        self.iterations -= 1
        if self.iterations < 0:
            self.refresh()
            self.iterations = self.base_iterations
        data_array = self.gather_data()
        for symbol_data in data_array:
            key, value = self.create_message(symbol_data)
            self.publish(key, value)
        return 0


class hf_opp_publisher(publisher):
    def __init__(self, config):
        super().__init__(config, "osrs-hf-opp")
        self.ROI_RATIO = config.get("ROI_RATIO")

    def refresh(self):
        self.logger.info("Refreshing data, client TTL Expired")
        self.timestamp, symbol_data = refresh_vol_list(self.config)
        self.symbols_to_track = symbol_data.keys()

    def create_message(
        self,
        symbol,
        symbol_low_df,
        symbol_high_df,
        profit_per_item,
        limit,
        last_sell,
        last_buy,
    ):
        now = pd.Timestamp(datetime.utcnow()).floor(freq="s")
        id = self.r.get_id_for_name(symbol)
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
        value = {
            "time": datetime.now().isoformat(),
            "symbol": symbol,
            "id": id,
            "profit_per_item": profit_per_item,
            "limit": limit,
            "m15_low": float(m15_low),
            "m15_high": float(m15_high),
            "m30_low": float(m30_low),
            "m30_high": float(m30_high),
            "h1_low": float(h1_low),
            "h1_high": float(h1_high),
            "last_sell": float(last_sell["low"]),
            "last_sell_time": last_sell["low_time"].isoformat(),
            "last_buy": float(last_buy["high"]),
            "last_buy_time": last_buy["high_time"].isoformat(),
        }
        key = str(id)
        return key, value

    def run(self):
        self.logger.info("Publisher running", publisher="hf_opp")
        self.iterations -= 1
        if self.iterations < 0:
            self.refresh()
            self.iterations = self.base_iterations
        rs_sells = self.client.execute(
            f"select low, lowTime, name, id from rs_sells where lowTime >= now() - interval 1 hour"
        )
        rs_buys = self.client.execute(
            f"select high, highTime, name, id from rs_buys where highTime >= now() - interval 1 hour"
        )
        high_df = pd.DataFrame(
            rs_buys, columns=["high", "high_time", "name", "id"]
        ).sort_values(["high_time"], ascending=False)
        low_df = pd.DataFrame(
            rs_sells, columns=["low", "low_time", "name", "id"]
        ).sort_values(["low_time"], ascending=False)
        for symbol in self.symbols_to_track:
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
            limit = self.r.name_to_limit.get(symbol)
            if profit_per_item / last_sell["low"] > self.ROI_RATIO:
                symbol_low_df = low_df[low_df["name"] == symbol]
                symbol_high_df = high_df[high_df["name"] == symbol]
                key, value = self.create_message(
                    symbol,
                    symbol_low_df,
                    symbol_high_df,
                    profit_per_item,
                    limit,
                    last_sell,
                    last_buy,
                )
                self.publish(key, value)
        return 0


class mf_publisher(publisher):
    def __init__(self, config):
        super().__init__(config, "osrs-mf-opp")
        self.k_interval = 26
        self.d_interval = 12
        self.signal_interval = 6
        self.time_window = 60 * 10  # 10 Minutes

    def refresh(self):
        self.logger.info("Refreshing data, client TTL Expired")
        self.timestamp, symbol_data = refresh_vol_list(self.config)
        self.symbols_to_track = symbol_data.keys()

    def create_message(self, value):
        value["k_interval"] = self.k_interval
        value["d_interval"] = self.d_interval
        value["signal_interval"] = self.signal_interval
        value["time_window"] = self.time_window
        value["low_time"] = value["low_time"].isoformat()
        value["high_time"] = value["high_time"].isoformat()
        value["time"] = value["time"].isoformat()
        return value

    def run(self):
        self.logger.info("Publisher running", publisher="mf_opp")
        self.iterations -= 1
        if self.iterations < 0:
            self.refresh()
            self.iterations = self.base_iterations
        rs_sells = self.client.execute(
            f"select low, lowTime, name, id from rs_sells where lowTime >= now() - interval 6 hour"
        )
        rs_buys = self.client.execute(
            f"select high, highTime, name, id from rs_buys where highTime >= now() - interval 6 hour"
        )
        high_df = pd.DataFrame(
            rs_buys, columns=["high", "high_time", "name", "id"]
        ).sort_values(["high_time"], ascending=False)
        low_df = pd.DataFrame(
            rs_sells, columns=["low", "low_time", "name", "id"]
        ).sort_values(["low_time"], ascending=False)
        price_df = Runespreader.collate_dfs(
            high_df=high_df,
            low_df=low_df,
            symbol_list=self.symbols_to_track,
            interval=timedelta(seconds=self.time_window),
        )
        for symbol in self.symbols_to_track:
            symbol_price_df = price_df[price_df["name"] == symbol]
            if len(symbol_price_df) > 0:
                # Bad mid_price calculation but given this is meant to track trends I don't think it actually matters, can add vwap later if needed
                symbol_price_df["mid_price"] = (
                    symbol_price_df["low"] + symbol_price_df["high"]
                ) / 2
                k = (
                    symbol_price_df["mid_price"]
                    .ewm(
                        span=self.k_interval,
                        adjust=False,
                        min_periods=self.k_interval,
                    )
                    .mean()
                )
                d = (
                    symbol_price_df["mid_price"]
                    .ewm(
                        span=self.d_interval,
                        adjust=False,
                        min_periods=self.d_interval,
                    )
                    .mean()
                )
                macd = k - d
                signal = macd.ewm(
                    span=self.signal_interval,
                    adjust=False,
                    min_periods=self.signal_interval,
                ).mean()
                h = macd - signal
                macd_signal_crossover = (macd > signal) & (
                    macd.shift(1) <= signal
                )
                symbol_price_df["macd_signal_crossover"] = macd_signal_crossover
                symbol_price_df["macd_trigger"] = h
                symbol_price_df["macd_signal"] = signal
                symbol_price_df["k_ewm"] = k
                symbol_price_df["d_ewm"] = d
                value = symbol_price_df.to_dict("records")[-1]
                key = self.r.get_id_for_name(symbol)
                message = self.create_message(value)

                self.publish(key, message)
        return 0


class sweep_publisher(publisher):
    def __init__(self, config):
        super().__init__(config, "osrs-sweeps")
        self.SWEEP_THRESH = config.get("SWEEP_THRESH")

    def refresh(self):
        self.logger.info("Refreshing data, client TTL Expired")
        self.timestamp, symbol_data = refresh_vol_list(self.config)
        self.symbols_to_track = symbol_data.keys()

    def create_message(self, symbol, limit, sell_0, buy_0, sell_1, buy_1):
        now = pd.Timestamp(datetime.utcnow()).floor(freq="s")
        id = self.r.get_id_for_name(symbol)
        value = {
            "time": now.isoformat(),
            "symbol": symbol,
            "id": id,
            "limit": limit,
            "percent_sweep": ((sell_1["low"] - sell_0["low"]) / sell_1["low"])
            * 100,
            "last_sell": float(sell_0["low"]),
            "last_sell_time": sell_0["low_time"].isoformat(),
            "last_buy": float(buy_0["high"]),
            "last_buy_time": buy_0["high_time"].isoformat(),
            "second_to_last_sell": float(sell_1["low"]),
            "second_to_last_sell_time": sell_1["low_time"].isoformat(),
            "second_to_last_buy": float(buy_1["high"]),
            "second_to_last_buy_time": buy_1["high_time"].isoformat(),
        }
        key = str(id)
        return key, value

    def run(self):
        self.logger.info("Publisher running", publisher="sweeps")
        self.iterations -= 1
        if self.iterations < 0:
            self.refresh()
            self.iterations = self.base_iterations
        rs_sells = self.client.execute(
            f"select low, lowTime, name, id from rs_sells where lowTime >= now() - interval 15 minute"
        )
        rs_buys = self.client.execute(
            f"select high, highTime, name, id from rs_buys where highTime >= now() - interval 15 minute"
        )
        high_df = pd.DataFrame(
            rs_buys, columns=["high", "high_time", "name", "id"]
        ).sort_values(["high_time"], ascending=False)
        low_df = pd.DataFrame(
            rs_sells, columns=["low", "low_time", "name", "id"]
        ).sort_values(["low_time"], ascending=False)
        for symbol in self.symbols_to_track:
            try:
                sell_0 = low_df[low_df["name"] == symbol].iloc[0]
                buy_0 = high_df[high_df["name"] == symbol].iloc[0]
                sell_1 = low_df[low_df["name"] == symbol].iloc[1]
                buy_1 = high_df[high_df["name"] == symbol].iloc[1]
            except:
                continue
            now = pd.Timestamp(datetime.utcnow()).floor(freq="s")
            if sell_0["low_time"] < now - pd.Timedelta("1 minutes"):
                continue

            limit = self.r.name_to_limit.get(symbol)
            if (
                sell_0["low"] < sell_1["low"]
                and ((sell_1["low"] - sell_0["low"]) / sell_1["low"])
                > self.SWEEP_THRESH
            ):
                key, value = self.create_message(
                    symbol, limit, sell_0, buy_0, sell_1, buy_1
                )
                self.publish(key, value)


def main():
    config = get_config()

    r_pub = ref_data_publisher(config)
    m_pub = mkt_data_publisher(config)
    mf_pub = mf_publisher(config)
    h_pub = hf_opp_publisher(config)
    s_pub = sweep_publisher(config)

    r = task.LoopingCall(r_pub.run)
    m = task.LoopingCall(m_pub.run)
    mf = task.LoopingCall(mf_pub.run)
    h = task.LoopingCall(h_pub.run)
    s = task.LoopingCall(s_pub.run)

    r.start(config.get("REF_DATA_INTERVAL"))
    m.start(config.get("MKT_DATA_INTERVAL"))
    mf.start(config.get("MF_OPP_INTERVAL"))
    h.start(config.get("HF_OPP_INTERVAL"))
    s.start(config.get("SWEEP_INTERVAL"))

    reactor.run()


if __name__ == "__main__":
    main()
