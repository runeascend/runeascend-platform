import os
import typing

import pandas as pd
import requests
import yaml
from clickhouse_driver import Client


class Runespreader:
    def __init__(self):
        self.custom_headers = {
            "User-Agent": "Runespreader Python-3.11, Discord @avg_white_male"
        }
        raw_list = requests.get(
            "https://prices.runescape.wiki/api/v1/osrs/mapping",
            headers=self.custom_headers,
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
        data_dict = (
            requests.get(
                f"https://prices.runescape.wiki/api/v1/osrs/latest/?id={uuid}",
                headers=self.custom_headers,
            )
            .json()
            .get("data")
            .get(uuid)
        )
        resp_json = requests.get(
            "https://prices.runescape.wiki/api/v1/osrs/volumes",
            headers=self.custom_headers,
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
        resp_json = requests.get(
            "https://prices.runescape.wiki/api/v1/osrs/volumes",
            headers=self.custom_headers,
        ).json()
        return resp_json

    def get_item_data(self, name: str, interval: str) -> tuple:
        """
        queries clickhouse for an item on a specific time interval
        and returns the dataframes.

        returns a tuple with two df, first one is sells
        second one is buys
        """
        config = yaml.load(
            open(f"{os.path.expanduser('~')}/.config/runespreader"),
            Loader=yaml.Loader,
        )
        client = Client(host="localhost", password=config.get("CH_PASSWORD"))
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
        data_dict = (
            requests.get(
                f"https://prices.runescape.wiki/api/v1/osrs/latest/",
                headers=self.custom_headers,
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
