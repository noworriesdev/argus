def fetch_discord_messages():
    import discord
    from discord.ext import commands
    import asyncio
    import json
    import os
    import time

    async def fetch_channel_messages(channel, channel_messages, semaphore):
        async with semaphore:  
            channel_info = {
                "id": channel.id,
                "name": channel.name,
                "topic": channel.topic,
            }
            channel_messages[channel.id] = {
                "info": channel_info,
                "messages": [],
            }

            batch_size = 100
            last_message_id = None
            printFirstTime = True
            while True:
                if printFirstTime is True:
                    print("we are retrieving " + channel.name)
                    printFirstTime = False
                messages_list = []
                async for message in channel.history(
                    limit=batch_size,
                    before=discord.Object(id=last_message_id)
                    if last_message_id
                    else None,
                ):
                    messages_list.append(
                        {
                            "id": message.id,
                            "author_id": message.author.id,
                            "author_name": str(message.author),
                            "content": message.content,
                            "timestamp": message.created_at.isoformat(),
                        }
                    )
                    print(channel.name + " " + str(message.created_at.isoformat()))
                channel_messages[channel.id]["messages"].extend(messages_list)
                if not messages_list:
                    break
                last_message_id = messages_list[-1]["id"]

    async def fetch_messages():
        TOKEN = (
            "MTE1OTI2NjE1NDM3MjY3NzY4Mg.GGpVCJ.z7o54bxjczdmJzaarr3TN26reP0_G69n5eUyZo"
        )
        GUILD_ID = 904432320025595904  # use your actual guild ID

        intents = discord.Intents.default()
        intents.messages = True
        bot = commands.Bot(command_prefix="!", intents=intents)

        channel_messages = {}

        @bot.event
        async def on_ready():
            print(f"We have logged in as {bot.user}")

            guild = bot.get_guild(GUILD_ID)
            if not guild:
                print(f"No guild with ID {GUILD_ID} found.")
                await bot.close()
                return

            semaphore = asyncio.Semaphore(10)  # Limit the parallel operations to 8
            fetch_tasks = []

            for channel in guild.channels:
                print(channel)
                print(channel.permissions_for(guild.me).view_channel)
                if (
                    isinstance(channel, discord.TextChannel)
                    and channel.permissions_for(guild.me).view_channel
                ):
                    fetch_tasks.append(
                        fetch_channel_messages(channel, channel_messages, semaphore)
                    )

            # wait for all the tasks to complete
            await asyncio.gather(*fetch_tasks)

            with open("/mnt/c/development/argus/discord_messages.json", "w+") as f:
                print("dumping messages")
                print(channel_messages)
                json.dump(channel_messages, f)
                f.close()
            await bot.close()

        print("starting bot")
        try:
            await bot.start(TOKEN)
        except Exception as e:
            raise e

    asyncio.run(fetch_messages())


def load_messages_to_neo4j():
    from neo4j import GraphDatabase
    import json
    import os

    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_USERNAME")
    neo4j_host = os.getenv("NEO4J_HOST")
    neo4j_port = os.getenv("NEO4J_PORT")

    uri = f"bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=(neo4j_username, neo4j_password))

    with open("./discord_messages.json", "r") as f:
        channel_messages = json.load(f)

    for channel_id, channel_data in channel_messages.items():
        with driver.session() as session:
            session.run(
                ("MERGE (c:Channel {id: $id, name: $name})"),
                id=channel_data["info"]["id"],
                name=channel_data["info"]["name"],
            )
            batch = []
            total = len(channel_data["messages"])
            batch_size = 100  # Set your preferred batch size

            for i, message in enumerate(channel_data["messages"]):
                print(f"loading message {i + 1} of {total}")
                batch.append(
                    {
                        "author_id": message["author_id"],
                        "author_name": message["author_name"],
                        "message_id": message["id"],
                        "content": message["content"],
                        "timestamp": message["timestamp"],
                        "channel_id": channel_id,
                    }
                )

                # If batch is of the desired size or if it is the last message, run the transaction
                if len(batch) == batch_size or i == total - 1:
                    session.run(
                        (
                            "UNWIND $batch AS msg "
                            "MERGE (u:User {id: msg.author_id, name: msg.author_name}) "
                            "MERGE (m:Message {id: msg.message_id, content: msg.content, timestamp: msg.timestamp}) "
                            "MERGE (c:Channel {id: msg.channel_id}) "
                            "MERGE (u)-[:SENT]->(m) "
                            "MERGE (m)-[:CONTAINED_IN]->(c)"
                        ),
                        {"batch": batch},
                    )
                    batch.clear()  # Clear the batch
        driver.close()


if __name__ == "__main__":
    # fetch_discord_messages()
    load_messages_to_neo4j()

    """
    k means
    db scan

    """
