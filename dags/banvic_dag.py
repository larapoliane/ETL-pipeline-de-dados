from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime
import pandas as pd
import os

# Caminho base para salvar os CSVs
BASE_PATH = "/opt/airflow/data"

def extract_postgres(**context):
    """Extrai dados do banco de origem (source_db) e salva em CSV."""
    hook = PostgresHook(postgres_conn_id="source_postgres")
    tables = ["clientes", "produtos", "transacoes"]  # ajuste conforme seu banvic.sql
    
    run_date = context["ds"]  # Data de execução no formato YYYY-MM-DD
    output_dir = os.path.join(BASE_PATH, run_date, "source_db")
    os.makedirs(output_dir, exist_ok=True)

    for table in tables:
        print(f"🔍 Conectando no source_db e extraindo tabela: {table}")
        df = hook.get_pandas_df(f"SELECT * FROM {table};")
        output_file = os.path.join(output_dir, f"{table}.csv")
        df.to_csv(output_file, index=False)
        print(f"✅ Tabela {table} salva em {output_file} com {len(df)} registros")

def extract_csv(**context):
    run_date = context["ds"]
    output_dir = os.path.join(BASE_PATH, run_date, "csv")
    os.makedirs(output_dir, exist_ok=True)

    source_file = "/opt/airflow/source_data/transacoes.csv"  # ajuste aqui!
    target_file = os.path.join(output_dir, "transacoes.csv")

    print(f"📂 Copiando {source_file} para {target_file}")
    if not os.path.exists(source_file):
        raise FileNotFoundError(f"❌ Arquivo CSV de origem não encontrado: {source_file}")

    df = pd.read_csv(source_file)
    df.to_csv(target_file, index=False)
    print(f"✅ Arquivo CSV copiado com {len(df)} registros")

def load_to_dw(**context):
    """Carrega os arquivos CSV no Data Warehouse (dw_postgres)."""
    hook = PostgresHook(postgres_conn_id="dw_postgres")
    engine = hook.get_sqlalchemy_engine()

    run_date = context["ds"]
    input_dir = os.path.join(BASE_PATH, run_date)

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".csv"):
                table_name = file.replace(".csv", "")
                file_path = os.path.join(root, file)
                print(f"📥 Carregando {file_path} para tabela {table_name} no DW")
                df = pd.read_csv(file_path)
                df.to_sql(table_name, engine, if_exists="replace", index=False)
                print(f"✅ Tabela {table_name} carregada com {len(df)} registros")

default_args = {
    "owner": "airflow",
    "retries": 1,
}

with DAG(
    dag_id="banvic_etl_dag",
    default_args=default_args,
    description="Pipeline ETL Banvic com logs detalhados",
    schedule_interval="35 4 * * *",  # 04:35 AM todo dia
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["banvic", "etl"],
) as dag:

    extract_postgres_task = PythonOperator(
        task_id="extract_postgres",
        python_callable=extract_postgres,
        provide_context=True,
    )

    extract_csv_task = PythonOperator(
        task_id="extract_csv",
        python_callable=extract_csv,
        provide_context=True,
    )

    load_to_dw_task = PythonOperator(
        task_id="load_to_dw",
        python_callable=load_to_dw,
        provide_context=True,
    )

    # Execuções paralelas, mas carregamento só após sucesso de ambas
    [extract_postgres_task, extract_csv_task] >> load_to_dw_task
