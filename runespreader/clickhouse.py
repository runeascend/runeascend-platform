import os
import time

import pandas as pd
import yaml
from clickhouse_driver import Client

from runespreader.main import Runespreader

config = yaml.load(open("/home/charles/.config/runespreader"), Loader=yaml.Loader)

while True:
    r = Runespreader()
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
    data = r.get_latest_data_for_all_symbols()
    df = pd.DataFrame(
        data, columns=["high", "highTime", "low", "lowTime", "name", "id"]
    )
    client.execute(
        "INSERT INTO rs_live_prices VALUES",
        df[["name", "id", "high", "highTime", "low", "lowTime"]].to_dict("records"),
        types_check=True,
    )
    client.execute(
        "INSERT INTO rs_buys VALUES",
        df[["name", "id", "high", "highTime"]].to_dict("records"),
        types_check=True,
    )
    client.execute(
        "INSERT INTO rs_sells VALUES",
        df[["name", "id", "low", "lowTime"]].to_dict("records"),
        types_check=True,
    )
    time.sleep(1)
