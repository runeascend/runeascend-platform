import datetime
import os

import faust
import yaml
from clickhouse_driver import Client

app = faust.App(
    "runewriter", broker="kafka://localhost:9092", topic_partitions=4
)

config = yaml.load(
    open(f"{os.path.expanduser('~')}/.config/runespreader"), Loader=yaml.Loader
)

osrs_hf_opp = app.topic("osrs-hf-opp")
osrs_mf_opp = app.topic("osrs-mf-opp")
osrs_mkt_data = app.topic("osrs-mkt-data")
osrs_sweeps = app.topic("osrs-sweeps")


@app.agent(osrs_hf_opp)
async def hf_opp_handler(stream):
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
    async for record in stream:
        record["_time"] = datetime.datetime.now()
        record["last_sell_time"] = datetime.datetime.fromisoformat(
            record["last_sell_time"]
        )
        record["last_buy_time"] = datetime.datetime.fromisoformat(
            record["last_buy_time"]
        )

        client.execute(
            "INSERT INTO osrs_hf_opp VALUES",
            [record],
            types_check=True,
        )


@app.agent(osrs_sweeps)
async def sweeps_handler(stream):
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
    async for record in stream:
        record["_time"] = datetime.datetime.now()
        record["second_to_last_sell_time"] = datetime.datetime.fromisoformat(
            record["second_to_last_sell_time"]
        )
        record["second_to_last_buy_time"] = datetime.datetime.fromisoformat(
            record["second_to_last_buy_time"]
        )
        record["last_sell_time"] = datetime.datetime.fromisoformat(
            record["last_sell_time"]
        )
        record["last_buy_time"] = datetime.datetime.fromisoformat(
            record["last_buy_time"]
        )

        client.execute(
            "INSERT INTO osrs_sweeps VALUES",
            [record],
            types_check=True,
        )


app.main()
