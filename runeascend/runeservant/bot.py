import re

import discord

from runeascend.common.config import get_config
from runeascend.runespreader.spreader import Runespreader


async def parse_intent(message: str, r) -> str:
    time_expression = re.compile(r"((?:hour)|(?:minute)|(?:day)|(?:week))")
    number_expression = re.compile(r"(\d+)")

    def find_item(message):
        item = ""
        for value in r.name_to_id_mapping.keys():
            if value.lower() in message.lower():
                item = value
        return item

    intents = ["average", "latest"]
    if "average" in message:
        # find time unit
        unit = re.findall(time_expression, message.lower())
        if not unit:
            return "No time unit provided, can't do much with this /shrug"
        unit = unit[0]
        number = re.findall(number_expression, message)
        if number:
            number = number[0]
            interval = f"{number} {unit}"
        elif "last" in message:
            # Assume someone wants -1 of time unit
            interval = f"1 {unit}"
        else:
            return f"Use the phrase `last` or provide an amount of {unit}(s) that you want"
        # Find item
        item = find_item(message)
        if not item:
            return "Sorry, Im a bit slow. You do need to give me an item I can recognize"
        low_df, high_df = r.get_item_data(item, interval)
        sell_avg = low_df["low"].mean()
        buy_avg = high_df["high"].mean()
        return f"{item} has a sell_avg of {sell_avg} and buy_avg of {buy_avg} over {interval}"

    elif "latest" in message:
        item = find_item(message)
        if not item:
            return "Sorry, Im a bit slow. You do need to give me an item I can recognize"
        data = r.get_latest_data_for_id(r.get_id_for_name(item))
        return str(data)
    else:
        return f"Unable to understand your intent, I can do any of the following: {intents}"


def main():
    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print("Ready to scape? @runespreader")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        if f"<@{client.application_id}>" in message.content:
            r = Runespreader()
            response = await parse_intent(
                message.content.replace(f"<@{client.application_id}>", ""), r
            )
            await message.channel.send(response)
            return
        return

    config = get_config()
    bot_token = config.get("BOT_TOKEN")

    client.run(bot_token)


if __name__ == "__main__":
    main()
