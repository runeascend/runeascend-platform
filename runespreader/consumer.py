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


class hf_opp_message(faust.Record):
    symbol: str
    id: str
    profit_per_item: float
    limit: int
    m15_low: float
    m15_high: float
    m30_low: float
    m30_high: float
    h1_low: float
    h1_high: float
    last_sell: int
    last_sell_time: datetime.datetime
    last_buy: int
    last_buy_time: datetime.datetime
    time: datetime.datetime


class mf_opp_message(faust.Record):
    time: datetime.datetime
    name: str
    id: str
    low_time: datetime.datetime
    low: int
    high_time: datetime.datetime
    high: int
    mid_price: float
    macd_signal_crossover: bool
    macd_trigger: float
    macd_signal: float
    k_ewm: float
    d_ewm: float
    k_interval: int
    d_interval: int
    signal_interval: int
    time_window: int


class mkt_data_message(faust.Record):
    high: int
    low: int
    name: str
    time: datetime.datetime
    id: str
    avg_high_price: int
    avg_low_price: int
    high_price_volume: int
    low_price_volume: int
    high_time: datetime.datetime
    low_time: datetime.datetime


class sweep_message(faust.Record):
    time: datetime.datetime
    symbol: str
    id: str
    limit: int
    percent_sweep: int
    last_sell: int
    last_sell_time: datetime.datetime
    last_buy: int
    last_buy_time: datetime.datetime
    second_to_last_sell: int
    second_to_last_sell_time: datetime.datetime
    second_to_last_buy: int
    second_to_last_buy_time: datetime.datetime


class order_message(faust.Record):
    """
    Describes intent
    """

    symbol: str
    trader_id: int
    price: float
    quantity: int
    side: str
    entry_order_id: str | None  # If side == sell, provide the buy order id
    time: datetime.datetime
    order_id: str


class fill_message(faust.Record):
    """
    Describes fill(s) - many partial fills can be sent for a single order
    """

    symbol: str
    price: float
    quantity: int
    time: datetime.datetime
    order_id: str


class cancel_message(faust.Record):
    """
    Describes cancel
    """

    order_id: str
    time: datetime.datetime
    reason: str


class savant_order_table_entry(faust.Record):
    symbol: str
    req_price: float
    req_quantity: int
    trader_id: int
    side: str  # buy, sell
    entry_order_id: str | None  # If side == sell, provide the buy order id
    open_time: datetime.datetime
    order_id: str
    fill_price: float
    fill_quantity: int
    order_status: str  # open, filled, cancelled
    close_time: datetime.datetime | None
    cancel_reason: str | None


osrs_hf_opp = app.topic("osrs-hf-opp", value_type=hf_opp_message)
osrs_mf_opp = app.topic("osrs-mf-opp", value_type=mf_opp_message)
osrs_mkt_data = app.topic("osrs-mkt-data", value_type=mkt_data_message)
osrs_sweeps = app.topic("osrs-sweeps", value_type=sweep_message)
osrs_savant_orders = app.topic("osrs-savant-orders", value_type=order_message)
osrs_savant_fills = app.topic("osrs-savant-fills", value_type=fill_message)
osrs_savant_cancels = app.topic(
    "osrs-savant-cancels", value_type=cancel_message
)

savant_order_table = app.Table(
    "savant_orders", default=savant_order_table_entry
)


@app.agent(osrs_hf_opp)
async def hf_opp_handler(stream):
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
    async for record in stream:
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

        client.execute(
            "INSERT INTO osrs_hf_opp VALUES",
            [record.to_representation()],
            types_check=True,
        )


@app.agent(osrs_mf_opp)
async def mf_opp_handler(stream):
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
    async for record in stream:
        try:
            record.validate()
        except faust.errors.SchemaValidationError as e:
            print(f"Validation error: {e}")
            continue
        record.time = datetime.datetime.fromisoformat(record.time)
        record.low_time = datetime.datetime.fromisoformat(record.low_time)
        record.high_time = datetime.datetime.fromisoformat(record.high_time)
        client.execute(
            "INSERT INTO osrs_mf_opp VALUES",
            [record.to_representation()],
            types_check=True,
        )


@app.agent(osrs_mkt_data)
async def mkt_data_handler(stream):
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
    async for record in stream:
        try:
            record.validate()
        except faust.errors.SchemaValidationError as e:
            print(f"Validation error: {e}")
            continue
        record.time = datetime.datetime.fromisoformat(record.time)
        record.high_time = datetime.datetime.fromisoformat(record.high_time)
        record.low_time = datetime.datetime.fromisoformat(record.low_time)
        client.execute(
            "INSERT INTO osrs_mkt_data VALUES",
            [record.to_representation()],
            types_check=True,
        )


@app.agent(osrs_sweeps)
async def sweeps_handler(stream):
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
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


@app.agent(osrs_savant_orders)
async def order_handler(stream):
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
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
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
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
    client = Client(host="localhost", password=config.get("CH_PASSWORD"))
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

app.main()
