import asyncio
import re

import pytest

from runeascend.runeservant.bot import parse_intent
from tests.runespreader.runespreader_mock import Mockspreader

pytest_plugins = ("pytest_asyncio",)
m = Mockspreader()


@pytest.mark.asyncio
async def test_average_case_1():
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and show me the average prices for Logs",
        m,
    )
    assert intent == "No time unit provided, can't do much with this /shrug"


@pytest.mark.asyncio
async def test_average_case_2():
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and show me the average hour prices for Logs",
        m,
    )
    assert (
        intent
        == "Use the phrase `last` or provide an amount of hour(s) that you want"
    )


@pytest.mark.asyncio
async def test_average_case_3():
    intent_re = re.compile(
        r"Logs has a sell_avg of \d+\.\d+ and buy_avg of \d+\.\d+ over 1 hour"
    )
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and show me the average 1 hour prices for Logs",
        m,
    )
    assert re.match(intent_re, intent)


@pytest.mark.asyncio
async def test_average_case_4():
    intent_re = re.compile(
        r"Logs has a sell_avg of \d+\.\d+ and buy_avg of \d+\.\d+ over 1 hour"
    )
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and show me the average last hour prices for Logs",
        m,
    )
    assert re.match(intent_re, intent)


@pytest.mark.asyncio
async def test_average_case_5():
    intent_re = re.compile(
        r"Logs has a sell_avg of \d+\.\d+ and buy_avg of \d+\.\d+ over 20 hour"
    )
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and show me the average 20 hour prices for Logs",
        m,
    )
    assert re.match(intent_re, intent)


@pytest.mark.asyncio
async def test_average_case_6():
    intent_re = re.compile(
        r"Logs has a sell_avg of \d+\.\d+ and buy_avg of \d+\.\d+ over 20 minute"
    )
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and show me the average 20 minute prices for Logs",
        m,
    )
    assert re.match(intent_re, intent)


@pytest.mark.asyncio
async def test_average_case_7():
    intent_re = re.compile(
        r"Logs has a sell_avg of \d+\.\d+ and buy_avg of \d+\.\d+ over 20 day"
    )
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and show me the average 20 day prices for Logs",
        m,
    )
    assert re.match(intent_re, intent)


@pytest.mark.asyncio
async def test_average_case_8():
    intent_re = re.compile(
        r"Logs has a sell_avg of \d+\.\d+ and buy_avg of \d+\.\d+ over 20 week"
    )
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and show me the average 20 week prices for Logs",
        m,
    )
    assert re.match(intent_re, intent)


@pytest.mark.asyncio
async def test_average_case_9():
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and show me the average 20 year prices for Logs",
        m,
    )
    assert intent == "No time unit provided, can't do much with this /shrug"


@pytest.mark.asyncio
async def test_latest_case_1():
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and latest for Frogs", m
    )
    assert (
        intent
        == "Sorry, Im a bit slow. You do need to give me an item I can recognize"
    )


@pytest.mark.asyncio
async def test_latest_case_2():
    intent_re = re.compile(
        r"{'high': \d+, 'low': \d+, 'lowTime': \d+\.\d+, 'highTime': \d+.\d+, 'vol': \d+, 'vol_ts': \d+\.\d+}"
    )
    intent = await parse_intent(
        "Oh my dear would you be positively splendid and latest for Logs", m
    )
    assert re.match(intent_re, intent)
