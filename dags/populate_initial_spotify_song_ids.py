from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from neo4j import GraphDatabase
import re

# DAG Configuration
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 1,
}
dag = DAG(
    'populate_initial_spotify_song_ids',
    default_args=default_args,
    description='Create naked Song nodes based on Regex.',
    schedule_interval=None,
)

NEO4J_URI = "bolt://argus-neo4j:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "mycoolpassword"

def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def process_messages(**kwargs):
    driver = get_neo4j_driver()
    with driver.session() as session:
        messages = session.run("MATCH (u:User)-[:SENT]->(m:Message) -[:CONTAINED_IN]-> (c:Channel) WHERE c.channelId = '904725881589727252' RETURN m.content AS message_text, m.messageId as message_id, u.userId as user_id")

        spotify_url_regex = r"https://open\.spotify\.com/track/([0-9A-Za-z]+)"
        
        for record in messages:
            print(record)
            print("raw message")
            message_id = record["message_id"]
            message_body = record["message_text"]
            user_id = record["user_id"]
            print("message.id")
            if not message_body:
                message_body = ""
            # Search for Spotify song ID
            match = re.search(spotify_url_regex, message_body)
            if match:
                song_id = match.group(1)
                # Create NEW_SONG_NODE and LINKS_SONG relationship
                session.run(
                    "MERGE (song:Song {spotifyId: $song_id}) "
                    "MERGE (msg:Message {messageId: $message_id}) "
                    "MERGE (user:User {userId: $user_id})"
                    "MERGE (msg)-[:LINKS_SONG]->(song)"
                    "MERGE (user)-[:POSTED_SONG]->(song)",
                    song_id=song_id, message_id=message_id, user_id = user_id
                )

process_messages_task = PythonOperator(
    task_id='process_messages',
    python_callable=process_messages,
    dag=dag,
)

process_messages_task
