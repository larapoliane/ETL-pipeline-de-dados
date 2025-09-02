from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup

import pandas as pd
import os
import hashlib
from datetime import datetime
from sqlalchemy import create_engine

# Configurações dos bancos
SOURCE_DB = {
    "host": "source_db",
    "port": 5432,
    "database": "banvic",
    "user": "data_engineer",
    "password": "v3rysecur&pas5w0rd"
}

DW_DB = {
    "host": "dw_postgres",
    "port": 5432,
    "database": "dw_db",
    "user": "dw_user",
    "password": "dw_pass"
}

DATA_PATH = "/opt/airflow/data"

# Função para extrair CSV
def extract_csv():
    df = pd.read_csv("/opt/airflow/source_data/transactions.csv")
    today = datetime.today().strftime("%Y-%m-%d")
    out_dir = os.path.join(DATA_PATH, today, "csv")
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, "transactions.csv"), index=False)

# Função para extrair tabelas SQL
def extract_sql_table(table_name):
    engine = create_engine(f"postgresql+psycopg2://{SOURCE_DB['user']}:{SOURCE_DB['password']}@{SOURCE_DB['host']}:{SOURCE_DB['port']}/{SOURCE_DB['database']}")
    df = pd.read_sql_table(table_name, engine)
    today = datetime.today().strftime("%Y-%m-%d")
    out_dir = os.path.join(DATA_PATH, today, "sql")
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, f"{table_name}.csv"), index=False)

# Função para carregar dados no Data Warehouse
def load_dw():
    today = datetime.today().strftime("%Y-%m-%d")
    dw_engine = create_engine(f"postgresql+psycopg2://{DW_DB['user']}:{DW_DB['password']}@{DW_DB['host']}:{DW_DB['port']}/{DW_DB['database']}")
    
    # Carregar CSV
    csv_path = os.path.join(DATA_PATH, today, "csv", "transactions.csv")
    df_csv = pd.read_csv(csv_path)
    df_csv["_md5hash"] = df_csv.apply(lambda row: hashlib.md5(str(row.values).encode()).hexdigest(), axis=1)
    df_csv.to_sql("transactions", dw_engine, if_exists="append", index=False, method='multi', chunksize=5000)
    
    # Carregar tabelas SQL
    sql_dir = os.path.join(DATA_PATH, today, "sql")
    for file in os.listdir(sql_dir):
        df_sql = pd.read_csv(os.path.join(sql_dir, file))
        df_sql["_md5hash"] = df_sql.apply(lambda row: hashlib.md5(str(row.values).encode()).hexdigest(), axis=1)
        table_name = file.replace(".csv", "")
        df_sql.to_sql(table_name, dw_engine, if_exists="append", index=False, method='multi', chunksize=5000)

# Definição da DAG
with DAG(
    dag_id="banvic_daily_etl",
    start_date=days_ago(1),
    schedule_interval="35 4 * * *",
    catchup=False,
    max_active_runs=1
) as dag:

    t1 = PythonOperator(
        task_id="extract_csv",
        python_callable=extract_csv
    )

    # Lista de tabelas SQL (substitua pelos nomes reais do banvic.sql)
    sql_tables = ["customers", "orders", "products"]
    t2_tasks = []
    with TaskGroup("extract_sql_tables") as t2_group:
        for table in sql_tables:
            t2_tasks.append(PythonOperator(
                task_id=f"extract_{table}",
                python_callable=extract_sql_table,
                op_args=[table]
            ))

    t3 = PythonOperator(
        task_id="load_dw",
        python_callable=load_dw
    )

    [t1, t2_group] >> t3
