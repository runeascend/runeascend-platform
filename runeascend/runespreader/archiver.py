import logging
import time

import pandas as pd
import structlog

from runeascend.common.clickhouse import get_clickhouse_client
from runeascend.common.config import get_config
from runeascend.runespreader.spreader import Runespreader

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO)
)
logger = structlog.get_logger()


def main():
    while True:
        logger.info("Starting data refresh loop")
        r = Runespreader()
        logger.info("Refreshing clickhouse client")
        client = get_clickhouse_client()
        logger.info("Getting Data for runesymbols")
        data = r.get_latest_data_for_all_symbols()
        logger.info("Converting data to dataframe")
        df = pd.DataFrame(
            data, columns=["high", "highTime", "low", "lowTime", "name", "id"]
        )
        logger.info("Updating clickhouse with new data")
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
        logger.info("Data updated")


if __name__ == "__main__":
    main()
