import difflib

import requests


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
            self.id_to_name_mapping[item.get("id")] = item.get("name")
            self.name_to_id_mapping[item.get("name")] = item.get("id")
            self.id_to_limit[item.get("id")] = item.get("limit")
            self.name_to_limit[item.get("name")] = item.get("limit")

    def get_id_for_name(self, name):
        return self.name_to_id_mapping.get(name)

    def get_name_for_id(self, uuid):
        return self.id_to_name_mapping.get(int(uuid))

    def get_latest_data_for_id(self, uuid):
        data_dict = (
            requests.get(
                f"https://prices.runescape.wiki/api/v1/osrs/latest/?id={uuid}",
                headers=self.custom_headers,
            )
            .json()
            .get("data")
            .get(str(uuid))
        )
        resp_json = requests.get(
            "https://prices.runescape.wiki/api/v1/osrs/volumes",
            headers=self.custom_headers,
        ).json()
        data_dict["vol"] = resp_json.get("data").get(str(uuid))
        data_dict["vol_ts"] = resp_json.get("timestamp")
        return data_dict

    def get_volumes(self):
        resp_json = requests.get(
            "https://prices.runescape.wiki/api/v1/osrs/volumes",
            headers=self.custom_headers,
        ).json()
        return resp_json

    def get_latest_data_for_all_symbols(self):
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
