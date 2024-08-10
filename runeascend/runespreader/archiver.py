import time

import pandas as pd

from runeascend.common.clickhouse import get_clickhouse_client
from runeascend.common.config import get_config
from runeascend.runespreader.spreader import Runespreader


def main():
    config = get_config()
    while True:
        r = Runespreader()
        client = get_clickhouse_client()
        data = r.get_latest_data_for_all_symbols()
        df = pd.DataFrame(
            data, columns=["high", "highTime", "low", "lowTime", "name", "id"]
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


if __name__ == "__main__":
    main()
