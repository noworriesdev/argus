import discord
from discord.ext import commands
import asyncio
import ipdb
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_discord_messages(token, guild, channel):
    
    async def fetch_channel_messages(channel_obj, channel_messages):
        channel_info = {
            "id": channel_obj.id,
            "name": channel_obj.name,
            "topic": channel_obj.topic,
        }
        channel_messages[channel_obj.id] = {
            "info": channel_info,
            "messages": [],
        }

        messages_list = []
        async for message in channel_obj.history(limit=4):
            ipdb.set_trace()

    async def fetch_messages():
        intents = discord.Intents.default()
        intents.messages = True
        bot = commands.Bot(command_prefix="!", intents=intents)
        channel_messages = {}

        @bot.event
        async def on_ready():
            print(f"We have logged in as {bot.user}")

            guild_obj = bot.get_guild(int(guild))  # Convert the guild ID to int and fetch the guild
            if not guild_obj:
                print(f"No guild with ID {guild} found.")
                await bot.close()
                return

            # Fetch the channel object using the channel ID
            channel_obj = guild_obj.get_channel(int(channel))  # Convert the channel ID to int
            if not channel_obj:
                print(f"No channel with ID {channel} found.")
                await bot.close()
                return

            await fetch_channel_messages(channel_obj, channel_messages)

        try:
            await bot.start(token)
        except Exception as e:
            raise e

    asyncio.run(fetch_messages())

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN_V")
    GUILD = os.getenv("DISCORD_GUILD")
    CHANNEL = 1159142635672449094
    fetch_discord_messages(TOKEN, GUILD, CHANNEL)
