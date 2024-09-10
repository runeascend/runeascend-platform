from datetime import timedelta

import pandas as pd

from runeascend.common.clickhouse import get_clickhouse_client
from runeascend.common.config import get_config
from runeascend.common.http import get_session


class Runespreader:
    def __init__(self):
        self.custom_headers = {
            "User-Agent": "Runespreader Python-3.11, Discord @avg_white_male"
        }
        s = get_session()
        raw_list = s.get(
            "https://prices.runescape.wiki/api/v1/osrs/mapping",
            headers=self.custom_headers,
            timeout=1,
        ).json()
        self.id_to_name_mapping = {}
        self.name_to_id_mapping = {}
        self.id_to_limit = {}
        self.name_to_limit = {}
        for item in raw_list:
            self.id_to_name_mapping[str(item.get("id"))] = item.get("name")
            self.name_to_id_mapping[str(item.get("name"))] = str(item.get("id"))
            self.id_to_limit[str(item.get("id"))] = item.get("limit", 0)
            self.name_to_limit[str(item.get("name"))] = item.get("limit", 0)

    def get_id_for_name(self, name: str) -> str:
        return self.name_to_id_mapping.get(name)

    def get_name_for_id(self, uuid: str | int) -> str:
        return self.id_to_name_mapping.get(str(uuid))

    def get_latest_data_for_id(self, uuid: str | int) -> dict:
        uuid = str(uuid)
        s = get_session()
        data_dict = (
            s.get(
                f"https://prices.runescape.wiki/api/v1/osrs/latest/?id={uuid}",
                headers=self.custom_headers,
                timeout=1,
            )
            .json()
            .get("data")
            .get(uuid)
        )
        resp_json = s.get(
            "https://prices.runescape.wiki/api/v1/osrs/volumes",
            headers=self.custom_headers,
            timeout=1,
        ).json()
        data_dict["vol"] = resp_json.get("data").get(uuid)
        data_dict["vol_ts"] = resp_json.get("timestamp")
        return data_dict

    def get_volumes(self) -> dict:
        """
        returns a dict with timestamp: <daily time>
        and a list in a key called data. The keys of
        said list are the ids.
        """
        s = get_session()
        resp_json = s.get(
            "https://prices.runescape.wiki/api/v1/osrs/volumes",
            headers=self.custom_headers,
            timeout=1,
        ).json()
        return resp_json

    def get_item_data(self, name: str, interval: str) -> tuple:
        """
        queries clickhouse for an item on a specific time interval
        and returns the dataframes.

        returns a tuple with two df, first one is sells
        second one is buys
        """
        config = get_config()
        client = get_clickhouse_client()
        rs_sells = client.execute(
            f"select low, lowTime, name, id from rs_sells where lowTime >= now() - interval {interval} and name = '{name}'"
        )
        rs_buys = client.execute(
            f"select high, highTime, name, id from rs_buys where highTime >= now() - interval {interval} and name = '{name}'"
        )
        high_df = pd.DataFrame(
            rs_buys, columns=["high", "high_time", "name", "id"]
        ).sort_values(["high_time"], ascending=False)
        low_df = pd.DataFrame(
            rs_sells, columns=["low", "low_time", "name", "id"]
        ).sort_values(["low_time"], ascending=False)
        return low_df, high_df

    def get_latest_data_for_all_symbols(self) -> list:
        """
        returns a list of dicts containing entry values of highTime, high
        lowTime, low, name, and id
        """
        s = get_session()
        data_dict = (
            s.get(
                f"https://prices.runescape.wiki/api/v1/osrs/latest/",
                headers=self.custom_headers,
                timeout=1,
            )
            .json()
            .get("data")
        )
        data_array = []
        for entry_key, entry_val in data_dict.items():
            entry_val["name"] = self.get_name_for_id(int(entry_key))
            entry_val["id"] = int(entry_key)
            if (
                not entry_val.get("high")
                or not entry_val.get("low")
                or not entry_val.get("name")
            ):
                continue
            data_array.append(entry_val)
        return data_array

    def get_5_minute_data(self) -> list:
        s = get_session()
        data_dict = (
            s.get(
                f"https://prices.runescape.wiki/api/v1/osrs/5m",
                headers=self.custom_headers,
                timeout=1,
            )
            .json()
            .get("data")
        )
        data_array = []
        for entry_key, entry_val in data_dict.items():
            entry_val["name"] = self.get_name_for_id(int(entry_key))
            entry_val["id"] = int(entry_key)
            entry_val["avgHighPrice"] = (
                entry_val["avgHighPrice"]
                if isinstance(entry_val["avgHighPrice"], int)
                else 0
            )
            entry_val["avgLowPrice"] = (
                entry_val["avgLowPrice"]
                if isinstance(entry_val["avgLowPrice"], int)
                else 0
            )

            data_array.append(entry_val)
        return data_array

    @staticmethod
    def collate_dfs(
        low_df, high_df, interval=timedelta(minutes=1), symbol_list=[]
    ) -> pd.DataFrame:
        """
        Logic

        sep tables hold buy and sells

        need to understand the market at any given actionable interval

        since we open position when liquidity is present join on sells with last(highTime) < current_time in a window function
        """
        earliest = low_df["low_time"].min()
        latest = low_df["low_time"].max()
        pd_array = []

        for symbol in symbol_list:
            current_time = earliest
            symbol_array = []
            symbol_low_df = low_df[low_df["name"] == symbol].sort_values(
                ["low_time"], ascending=False
            )
            symbol_high_df = high_df[high_df["name"] == symbol].sort_values(
                ["high_time"], ascending=False
            )

            while current_time <= latest:
                # Get the sells and buys for the current time
                current_time = current_time + interval
                low_entry = symbol_low_df[
                    symbol_low_df["low_time"] < current_time
                ]
                if low_entry.empty:
                    continue
                low_entry = low_entry.iloc[0]
                high_entry = symbol_high_df[
                    symbol_high_df["high_time"] < current_time
                ]
                if high_entry.empty:
                    continue
                high_entry = high_entry.iloc[0]
                entry = {
                    "time": current_time,
                    "name": symbol,
                    "id": low_entry["id"],
                    "low_time": low_entry["low_time"],
                    "low": low_entry["low"],
                    "high_time": high_entry["high_time"],
                    "high": high_entry["high"],
                }
                symbol_array.append(entry)

            pd_array.append(pd.DataFrame(symbol_array))
        return pd.concat(pd_array)
