from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 9),
    'retries': 1,
}

with DAG(
    dag_id='app_script_dag',
    default_args=default_args,
    schedule_interval='0 * * * *',  # ou par ex. "0 8 * * *" pour exécution quotidienne
    catchup=False,
    max_active_runs=1,
    tags=['bluesky']
) as dag:

    run_app_script = BashOperator(
        task_id='run_app_script',
        bash_command='python3 /opt/airflow/src/app.py'
    )

    run_app_script
