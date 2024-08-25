import time

import numpy as np
import pandas as pd


class Mockspreader:
    def __init__(self):
        self.id_to_name_mapping = {"1": "Logs"}
        self.name_to_id_mapping = {"Logs": "1"}
        self.id_to_limit = {"1": 1000}
        self.name_to_limit = {"Logs": 1000}

    def get_id_for_name(self, name: str) -> str:
        return self.name_to_id_mapping.get(name)

    def get_name_for_id(self, uuid: str | int) -> str:
        return self.id_to_name_mapping.get(str(uuid))

    def get_latest_data_for_id(self, uuid: str | int) -> dict:
        uuid = str(uuid)
        data_dict = (
            {
                "data": {
                    "1": {
                        "high": 25,
                        "low": 24,
                        "lowTime": time.time(),
                        "highTime": time.time(),
                    }
                }
            }
            .get("data")
            .get(uuid)
        )
        data_dict["vol"] = 10000
        data_dict["vol_ts"] = time.time()
        return data_dict

    def get_volumes(self) -> dict:
        """
        returns a dict with timestamp: <daily time>
        and a list in a key called data. The keys of
        said list are the ids.
        """
        return {"timestamp": time.time(), "data": {"1": 10000}}

    def get_item_data(self, name: str, interval: str) -> tuple:
        """
        queries clickhouse for an item on a specific time interval
        and returns the dataframes.

        returns a tuple with two df, first one is sells
        second one is buys
        """
        low_df = pd.DataFrame(
            np.random.randint(0, 100, size=(15, 2)), columns=["low", "low_time"]
        )
        low_df["name"] = name
        high_df = pd.DataFrame(
            np.random.randint(0, 100, size=(15, 2)),
            columns=["high", "high_time"],
        )
        high_df["name"] = name
        return low_df, high_df

    def get_latest_data_for_all_symbols(self) -> list:
        """
        returns a list of dicts containing entry values of highTime, high
        lowTime, low, name, and id
        """
        data_array = [
            {
                "1": {
                    "high": 25,
                    "low": 24,
                    "lowTime": time.time(),
                    "highTime": time.time(),
                }
            }
        ]
        return data_array
