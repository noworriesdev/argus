import datetime as dt
from datetime import datetime
import asyncio
import os
import psycopg2
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from neo4j import GraphDatabase
import discord
from discord.ext import commands
import dotenv
from dotenv import load_dotenv
load_dotenv()

DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': dt.timedelta(minutes=5),
}

NEO4J_URI = "bolt://argus-neo4j:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "mycoolpassword"

POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', None)
# if not POSTGRES_CONN:
#     raise ValueError("Unable to get AIRFLOW_POSTGRES_CONN from environment")

def fetch_last_message():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        query = """
        MATCH (m:Message)-[:CONTAINED_IN]->(c:Channel)
        WITH c, m ORDER BY m.timestamp DESC
        RETURN c.channelId AS channel_id, COLLECT(m.messageId)[0] AS message_id, COLLECT(m.timestamp)[0] AS timestamp
        """
        records = session.run(query)
        results = [(record['message_id'], record['timestamp'], record['channel_id']) for record in records]
    driver.close()
    return results

def store_in_postgres(**kwargs):
    ti = kwargs['ti']
    results = ti.xcom_pull(task_ids='fetch_last_message_task')
    current_time_utc = datetime.utcnow()
    formatted_time = current_time_utc.isoformat()
    try:
        with psycopg2.connect(f"postgres://postgres:{POSTGRES_PASSWORD}@argus-postgres-postgresql:5432/postgres") as conn:
            with conn.cursor() as cur:
                for message_id, timestamp, channel_id in results:
                    # Insert the data into the operational.graph_streaming_checkpoints table
                    cur.execute("""
                        INSERT INTO operational.graph_streaming_checkpoints (timestamp, channel, last_message_seen)
                        VALUES (%s, %s, %s)
                    """, (formatted_time, channel_id, message_id))
    except Exception as e:
        print(f"Error: {str(e)}")

def prepare_json_for_insert(**kwargs):
    async def get_last_seen_message(channel_id):
        with psycopg2.connect(f"postgres://postgres:{POSTGRES_PASSWORD}@argus-postgres-postgresql:5432/postgres") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT last_message_seen FROM operational.graph_streaming_checkpoints WHERE channel = %s ORDER BY last_message_seen DESC LIMIT 1", (channel_id,))
                result = cur.fetchone()
                return result[0] if result else None

    async def fetch_channel_messages(bot, channel):
        last_seen_message = await get_last_seen_message(channel.id)
        print(last_seen_message)
        new_messages = []
        
        async for message in channel.history(limit=100):
            if message.id == last_seen_message:
                break
            new_messages.append({
                "id": message.id,
                "author_id": message.author.id,
                "author_name": str(message.author),
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                "channel_name": message.channel.name
            })
        
        if new_messages:
            with psycopg2.connect(f"postgres://postgres:{POSTGRES_PASSWORD}@argus-postgres-postgresql:5432/postgres") as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO operational.graph_streaming_checkpoints (channel, last_message_seen) VALUES (%s, %s)", (channel.id, new_messages[0]['id']))
                    conn.commit()

        return new_messages

    async def fetch_all_messages():
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        bot = commands.Bot(command_prefix="!", intents=intents)

        all_messages = {}

        @bot.event
        async def on_ready():
            guild = bot.get_guild(904432320025595904)
            print(guild.text_channels)
            for channel in guild.text_channels:
                messages = await fetch_channel_messages(bot, channel)
                all_messages[channel.id] = messages
            
            await bot.close()

        await bot.start("MTE2MzY2NTQxNDA1MjY0Mjg5Nw.GPq26R.mRQJ-j7gukBsOs8upmw9rT7BBKvn9ZSTaVR3DQ")
        return all_messages
        # Execute the main function
    ret =  asyncio.run(fetch_all_messages())
    print(ret)
    return ret

def load_into_neo4j(**kwargs):

    def load_messages(tx, messages_list):
        query = """
        CALL apoc.periodic.iterate(
            'UNWIND $messages AS message RETURN message',
            '
            MERGE (u:User {userId: message.author_id}) ON CREATE SET u.name = message.author_name
            MERGE (m:Message {messageId: message.id, content: message.content, timestamp: message.timestamp})
            MERGE (c:Channel {channelId: message.channel_id, name: message.channel_name})
            MERGE (u)-[:SENT]->(m)
            MERGE (m)-[:CONTAINED_IN]->(c)
            ', 
            {batchSize:100, parallel:true, params:{messages: $messages_list}})
        """
        print(messages_list)
        tx.run(query, messages_list=messages_list)

    ti = kwargs['ti']
    fetched_messages = ti.xcom_pull(task_ids='prepare_json_for_insert_task')

    messages_list = []
    for channel_id, messages in fetched_messages.items():
        for message in messages:
            message_data = {
                "author_id": message["author_id"],
                "author_name": message["author_name"],
                "id": message["id"],
                "content": message["content"],
                "timestamp": message["timestamp"],
                "channel_id": channel_id,
                "channel_name": message["channel_name"]
            }
            messages_list.append(message_data)

    uri = "bolt://argus-neo4j:7687"
    username = "neo4j"
    password = "mycoolpassword"

    driver = GraphDatabase.driver(uri, auth=(username, password))

    with driver.session() as session:
        session.write_transaction(load_messages, messages_list)

    driver.close()


with DAG('neo4j_to_postgres_dag',
         default_args=DEFAULT_ARGS,
         description='Transfer latest message from Neo4j to Postgres for each channel',
         schedule_interval=dt.timedelta(minutes=60),
         start_date=dt.datetime(2023, 10, 25),
         catchup=False) as dag:

    fetch_last_message_task = PythonOperator(
        task_id='fetch_last_message_task',
        python_callable=fetch_last_message,
        dag=dag,
    )

    store_in_postgres_task = PythonOperator(
        task_id='store_in_postgres_task',
        provide_context=True,
        python_callable=store_in_postgres,
        dag=dag,
    )

    prepare_json_for_insert_task = PythonOperator(
        task_id='prepare_json_for_insert_task',
        provide_context=True,
        python_callable=prepare_json_for_insert,
        dag=dag,
    )
    load_into_neo4j_task = PythonOperator(
        task_id='load_into_neo4j_task',
        provide_context=True,
        python_callable=load_into_neo4j,
        dag=dag,
    )
    fetch_last_message_task >> store_in_postgres_task >> prepare_json_for_insert_task >> load_into_neo4j_task
