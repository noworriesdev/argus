from airflow import DAG
from airflow.operators.python_operator import PythonVirtualenvOperator
from datetime import datetime
import os

def fetch_discord_messages():
    import discord
    from discord.ext import commands
    import asyncio
    import json
    import os

    async def fetch_messages():
        TOKEN = os.getenv('DISCORD_TOKEN')
        GUILD_ID = os.getenv('DISCORD_GUILD')
        
        intents = discord.Intents.default()
        intents.messages = True
        bot = commands.Bot(command_prefix='!', intents=intents)

        channel_messages = {}

        @bot.event
        async def on_ready():
            print(f'We have logged in as {bot.user}')
            
            guild = bot.get_guild(GUILD_ID)
            if not guild:
                print(f"No guild with ID {GUILD_ID} found.")
                await bot.close()
                return
            
            for channel in guild.channels:
                print(channel)
                print(channel.permissions_for(guild.me).view_channel)
                if isinstance(channel, discord.TextChannel) and channel.permissions_for(guild.me).view_channel:
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

                    while True:
                        messages_list = []
                        async for message in channel.history(limit=batch_size, 
                                                            before=discord.Object(id=last_message_id) if last_message_id else None):
                            messages_list.append({
                                "id": message.id,
                                "author_id": message.author.id,
                                "author_name": str(message.author),
                                "content": message.content,
                                "timestamp": message.created_at.isoformat()
                            })
                        
                        channel_messages[channel.id]["messages"].extend(messages_list)
                        if not messages_list:
                            break
                        last_message_id = messages_list[-1]["id"]
                        await asyncio.sleep(1)
            
            await bot.close()
        
        await bot.start(TOKEN)
        
        with open("/tmp/discord_messages.json", "w") as f:
            json.dump(channel_messages, f)

    asyncio.run(fetch_messages())

def load_messages_to_neo4j():
    from neo4j import GraphDatabase
    import json
    import os
    neo4j_username = os.getenv('NEO4J_USERNAME')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    neo4j_host = os.getenv('NEO4J_HOST')
    neo4j_port = os.getenv('NEO4J_PORT')

    uri = f"bolt://{neo4j_host}:{neo4j_port}"
    driver = GraphDatabase.driver(uri, auth=(neo4j_username, neo4j_password))

    with open("/tmp/discord_messages.json", "r") as f:
        channel_messages = json.load(f)

    with driver.session() as session:
        for channel_id, channel_data in channel_messages.items():
            session.run(("MERGE (c:Channel {id: $id, name: $name})"),
                        id=channel_data["info"]["id"], name=channel_data["info"]["name"])
            
            for message in channel_data["messages"]:
                session.run(("MERGE (u:User {id: $author_id, name: $author_name}) "
                             "MERGE (m:Message {id: $message_id, content: $content, timestamp: $timestamp}) "
                             "MERGE (c:Channel {id: $channel_id}) "
                             "MERGE (u)-[:SENT]->(m) "
                             "MERGE (m)-[:CONTAINED_IN]->(c)"),
                            author_id=message["author_id"], author_name=message["author_name"],
                            message_id=message["id"], content=message["content"], timestamp=message["timestamp"],
                            channel_id=channel_id)

    driver.close()

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
}

dag = DAG(
    'fetch_and_load_discord_messages',
    default_args=default_args,
    description='A DAG to fetch Discord messages and load them into a Neo4j database',
    schedule_interval='@once',
)

task1 = PythonVirtualenvOperator(
    task_id='fetch_discord_messages',
    python_callable=fetch_discord_messages,
    dag=dag,
    requirements=["discord.py"],
)

task2 = PythonVirtualenvOperator(
    task_id='load_messages_to_neo4j',
    python_callable=load_messages_to_neo4j,
    dag=dag,
    requirements=["neo4j"],
)

task1 >> task2
