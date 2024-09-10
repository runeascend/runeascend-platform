import datetime
import os

import faust

from runeascend.common.clickhouse import get_clickhouse_client
from runeascend.runevault.models import (
    cancel_message,
    fill_message,
    order_message,
    savant_order_table_entry,
)

app = faust.App(
    "runevault",
    broker=f"kafka://{os.getenv('KAFKA_BROKER','localhost:9092')}",
    topic_partitions=4,
)


osrs_savant_orders = app.topic("osrs-savant-orders", value_type=order_message)
osrs_savant_fills = app.topic("osrs-savant-fills", value_type=fill_message)
osrs_savant_cancels = app.topic(
    "osrs-savant-cancels", value_type=cancel_message
)

savant_order_table = app.Table(
    "savant_orders", default=savant_order_table_entry
)


@app.agent(osrs_savant_orders)
async def order_handler(stream):
    client = get_clickhouse_client()
    async for record in stream:
        try:
            record.validate()
        except faust.errors.SchemaValidationError as e:
            print(f"Validation error: {e}")
            continue
        record.time = datetime.datetime.fromisoformat(record.time)
        # Create a record in faust table
        savant_order_table[record.order_id] = savant_order_table_entry(
            symbol=record.symbol,
            req_price=record.price,
            trader_id=record.trader_id,
            req_quantity=record.quantity,
            side=record.side,
            open_time=record.time,
            order_id=record.order_id,
            entry_order_id=record.entry_order_id,
            fill_price=None,
            fill_quantity=None,
            order_status="open",
            close_time=None,
            cancel_reason=None,
        )

        # Insert into clickhouse
        client.execute(
            "INSERT INTO osrs_savant_order_events VALUES",
            [record.to_representation()],
            types_check=True,
        )


@app.agent(osrs_savant_fills)
async def fill_handler(stream):
    client = get_clickhouse_client()
    async for record in stream:
        try:
            record.validate()
        except faust.errors.SchemaValidationError as e:
            print(f"Validation error: {e}")
            continue
        record.time = datetime.datetime.fromisoformat(record.time)
        # Update record in faust table
        order = savant_order_table[record.order_id]
        if order.fill_quantity is None:
            order.fill_price = record.price
            order.fill_quantity = record.quantity
        else:
            # Average the fill price
            order.fill_price = (
                order.fill_price * order.fill_quantity
                + record.price * record.quantity
            ) / (order.fill_quantity + record.quantity)
            order.fill_quantity += record.quantity

        # Update order status
        if order.fill_quantity == order.req_quantity:
            order.order_status = "filled"
            order.close_time = record.time
            # Order Resolved, write to clickhouse
            client.execute(
                "INSERT INTO osrs_savant_orders VALUES",
                [order.to_representation()],
                types_check=True,
            )
            # TODO: Add table for pnl calculation, and write to it here if on the sell side.

        savant_order_table[record.order_id] = order

        client.execute(
            "INSERT INTO osrs_savant_fill_events VALUES",
            [record.to_representation()],
            types_check=True,
        )


@app.agent(osrs_savant_cancels)
async def cancel_handler(stream):
    client = get_clickhouse_client()
    async for record in stream:
        try:
            record.validate()
        except faust.errors.SchemaValidationError as e:
            print(f"Validation error: {e}")
            continue
        record.time = datetime.datetime.fromisoformat(record.time)
        # Update record in faust table
        order = savant_order_table[record.order_id]
        order.order_status = "cancelled"
        order.close_time = record.time
        order.cancel_reason = record.reason
        savant_order_table[record.order_id] = order

        # TODO: In PnL calculation, we need to consider the case where a partial fill has been cancelled on the sell side an inventory is held

        # Order Resolved, write to clickhouse
        client.execute(
            "INSERT INTO osrs_savant_orders VALUES",
            [order.to_representation()],
            types_check=True,
        )
        client.execute(
            "INSERT INTO osrs_savant_cancel_events VALUES",
            [record.to_representation()],
            types_check=True,
        )


# TODO: Implement app views for querying the data


def main():
    app.main()


if __name__ == "__main__":
    main()
