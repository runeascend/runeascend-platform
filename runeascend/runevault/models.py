import datetime

import faust


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
    """
    Describes a record in the savant order table
    """

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
