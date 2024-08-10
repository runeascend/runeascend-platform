import datetime
import os

import faust

from runeascend.common.clickhouse import get_clickhouse_client
from runeascend.runevault.models import (
    hf_opp_message,
    mf_opp_message,
    mkt_data_message,
    sweep_message,
)

app = faust.App(
    "runewriter",
    broker=f"kafka://{os.getenv('KAFKA_BROKER','localhost:9092')}",
    topic_partitions=4,
)

osrs_hf_opp = app.topic("osrs-hf-opp", value_type=hf_opp_message)
osrs_mf_opp = app.topic("osrs-mf-opp", value_type=mf_opp_message)
osrs_mkt_data = app.topic("osrs-mkt-data", value_type=mkt_data_message)
osrs_sweeps = app.topic("osrs-sweeps", value_type=sweep_message)


@app.agent(osrs_hf_opp)
async def hf_opp_handler(stream):
    client = get_clickhouse_client()
    async for records in stream.take(100, within=1):
        formatted_records = []
        for record in records:
            try:
                record.validate()
            except faust.errors.SchemaValidationError as e:
                print(f"Validation error: {e}")
                continue
            record.time = datetime.datetime.fromisoformat(record.time)

            record.last_sell_time = datetime.datetime.fromisoformat(
                record.last_sell_time
            )
            record.last_buy_time = datetime.datetime.fromisoformat(
                record.last_buy_time
            )
            formatted_records.append(record.to_representation())

        client.execute(
            "INSERT INTO osrs_hf_opp VALUES",
            formatted_records,
            types_check=True,
        )


@app.agent(osrs_mf_opp)
async def mf_opp_handler(stream):
    client = get_clickhouse_client()
    async for records in stream.take(1000, within=1):
        formatted_records = []
        for record in records:
            try:
                record.validate()
            except faust.errors.SchemaValidationError as e:
                print(f"Validation error: {e}")
                continue
            record.time = datetime.datetime.fromisoformat(record.time)
            record.low_time = datetime.datetime.fromisoformat(record.low_time)
            record.high_time = datetime.datetime.fromisoformat(record.high_time)
            formatted_records.append(record.to_representation())
        client.execute(
            "INSERT INTO osrs_mf_opp VALUES",
            formatted_records,
            types_check=True,
        )


@app.agent(osrs_mkt_data)
async def mkt_data_handler(stream):
    client = get_clickhouse_client()
    async for records in stream.take(1000, within=1):
        formatted_records = []
        for record in records:
            try:
                record.validate()
            except faust.errors.SchemaValidationError as e:
                print(f"Validation error: {e}")
                continue
            record.time = datetime.datetime.fromisoformat(record.time)
            record.high_time = datetime.datetime.fromisoformat(record.high_time)
            record.low_time = datetime.datetime.fromisoformat(record.low_time)
            formatted_records.append(record.to_representation())
        client.execute(
            "INSERT INTO osrs_mkt_data VALUES",
            formatted_records,
            types_check=True,
        )


@app.agent(osrs_sweeps)
async def sweeps_handler(stream):
    client = get_clickhouse_client()
    async for record in stream:
        try:
            record.validate()
        except faust.errors.SchemaValidationError as e:
            print(f"Validation error: {e}")
            continue
        record.time = datetime.datetime.fromisoformat(record.time)
        record.second_to_last_sell_time = datetime.datetime.fromisoformat(
            record.second_to_last_sell_time
        )
        record.second_to_last_buy_time = datetime.datetime.fromisoformat(
            record.second_to_last_buy_time
        )
        record.last_sell_time = datetime.datetime.fromisoformat(
            record.last_sell_time
        )
        record.last_buy_time = datetime.datetime.fromisoformat(
            record.last_buy_time
        )

        client.execute(
            "INSERT INTO osrs_sweeps VALUES",
            [record.to_representation()],
            types_check=True,
        )


def main():
    app.main()


if __name__ == "__main__":
    main()
