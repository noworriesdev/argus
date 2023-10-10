# dags/test_neo4j_connection.py

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from neo4j import GraphDatabase
import os

def test_neo4j_connection():
    # Retrieve environment variables
    neo4j_username = "neo4j"
    neo4j_password = "cNtG5b5blejc4y"
    neo4j_host = os.getenv('NEO4J_HOST')
    neo4j_port = os.getenv('NEO4J_PORT')
    print("Port: " + neo4j_port)

    uri = f"neo4j://{neo4j_host}:{neo4j_port}"
    
    # Establish connection to Neo4j
    driver = GraphDatabase.driver(uri, auth=(neo4j_username, neo4j_password))
    
    # Execute a simple query to fetch and log node count
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN COUNT(n) AS count")
        for record in result:
            print(f"Node count: {record['count']}")
    
    driver.close()


# DAG definition
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
}

dag = DAG(
    'test_neo4j_connection',
    default_args=default_args,
    description='A simple example DAG to test connection with Neo4j',
    schedule_interval='@once',
)

task1 = PythonOperator(
    task_id='test_neo4j_connection',
    python_callable=test_neo4j_connection,
    dag=dag,
)

task1
