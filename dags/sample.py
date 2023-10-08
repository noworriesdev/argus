# Importing necessary libraries
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from datetime import datetime, timedelta

# Default argument setting for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Instantiating a DAG
dag = DAG(
    'example_dag',
    default_args=default_args,
    description='A simple example DAG',
    schedule_interval=timedelta(days=1),
)

# Task definitions
start = DummyOperator(
    task_id='start',
    dag=dag,
)

extract_data = DummyOperator(
    task_id='extract_data',
    dag=dag,
)

end = DummyOperator(
    task_id='end',
    dag=dag,
)

# Defining task dependencies
start >> extract_data >> end
