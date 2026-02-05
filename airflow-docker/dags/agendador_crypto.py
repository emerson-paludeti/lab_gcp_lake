from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Configurações básicas
default_args = {
    'owner': 'voce',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Definição do Agendamento
with DAG(
    'pipeline_crypto_completo',             # O nome que aparece no site
    default_args=default_args,
    description='Roda o ETL de Criptomoedas',
    schedule_interval='0 9 * * *',          # Cron: Todo dia às 09:00
    start_date=datetime(2024, 1, 1),
    catchup=False,                          # Não tentar rodar o passado
    tags=['crypto', 'producao'],
) as dag:

    # A Tarefa: Rodar o script Python
    rodar_etl = BashOperator(
        task_id='rodar_script_python',
        # O comando exato que o Airflow vai digitar no terminal dele
        bash_command='python /opt/airflow/dags/pipeline_oficial.py'
    )