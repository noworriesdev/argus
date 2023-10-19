import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from neo4j import GraphDatabase
import os

def calculate_sentiment():
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_USERNAME")
    neo4j_host = os.getenv("NEO4J_HOST")
    neo4j_port = os.getenv("NEO4J_PORT")

    uri = f"bolt://{neo4j_host}:{neo4j_port}"
    driver = GraphDatabase.driver(uri, auth=(neo4j_username, neo4j_password))
    analyzer = SentimentIntensityAnalyzer()

    with driver.session() as session:
        # Assume you have a model in Neo4j where each Message node has a 'content' property.
        messages = session.run(
            "MATCH (m:Message) RETURN m.id AS id, m.content AS content"
        )

        for message in messages:
            message_id = message["id"]
            content = message["content"]
            sentiment_score = analyzer.polarity_scores(content)

            # Add the sentiment score to the Message node.
            session.run(
                (
                    "MATCH (m:Message {id: $message_id}) "
                    "SET m.sentiment_score = $sentiment_score"
                ),
                {
                    "message_id": message_id,
                    "sentiment_score": sentiment_score["compound"],
                },
            )

    driver.close()


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "calculate_sentiment_scores",
    default_args=default_args,
    description="A DAG to calculate sentiment scores of messages using VADER",
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 10, 11),
    catchup=False,
)

calculate_sentiment_task = PythonOperator(
    task_id="calculate_sentiment",
    python_callable=calculate_sentiment,
    dag=dag,
)

calculate_sentiment_task
