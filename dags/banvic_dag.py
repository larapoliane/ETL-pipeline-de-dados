# Importações 
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import pandas as pd
import psycopg2

# ------------------------------------------------------
# Configurações de conexão
# ------------------------------------------------------

# Banco de origem (source_db = Postgres inicializado com banvic.sql)
SOURCE_CONFIG = {
    "dbname": "banvic",
    "user": "data_engineer",
    "password": "v3rysecur&pas5w0rd",
    "host": "source_db",   # nome do serviço no docker-compose
    "port": 5432,
}

# Data Warehouse (dw_postgres = Postgres destino)
DW_CONFIG = {
    "dbname": "airflow",
    "user": "airflow",
    "password": "airflow",
    "host": "dw_postgres", # nome do serviço no docker-compose
    "port": 5432,
}

# Tabelas que serão extraídas do banco de origem
TABLES_TO_EXTRACT = ["clientes", "contas", "propostas_credito", "agencias"]

# Caminhos dos dados
CSV_SOURCE  = "/opt/airflow/source_data/transacoes.csv"   # CSV fornecido
OUTPUT_BASE = "/opt/airflow/data"                         # Data Lake local (montado no docker-compose)


# ------------------------------------------------------
# Funções de extração
# ------------------------------------------------------

def extract_table(table, output_dir):
    """Extrai uma tabela do banco de origem e salva como CSV."""
    conn = psycopg2.connect(**SOURCE_CONFIG)
    query = f"SELECT * FROM {table};"
    df = pd.read_sql(query, conn)
    conn.close()

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{table}.csv")
    df.to_csv(output_file, index=False)
    print(f"📂 Tabela {table} exportada para {output_file} ({len(df)} registros)")


def extract_all_sql(**kwargs):
    """Extrai todas as tabelas do banco de origem e salva como CSV."""
    date_str = kwargs["ds"]
    output_dir = f"{OUTPUT_BASE}/{date_str}/sql"
    for table in TABLES_TO_EXTRACT:
        extract_table(table, output_dir)


def extract_csv(**kwargs):
    """Copia o CSV de transações para o Data Lake."""
    date_str = kwargs["ds"]
    output_dir = f"{OUTPUT_BASE}/{date_str}/csv"
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(CSV_SOURCE)
    output_file = os.path.join(output_dir, "transacoes.csv")
    df.to_csv(output_file, index=False)
    print(f"📂 CSV de transações exportado para {output_file} ({len(df)} registros)")


# ------------------------------------------------------
# Função de carga no Data Warehouse
# ------------------------------------------------------

def load_to_dw(**kwargs):
    """Carrega os CSVs no Data Warehouse."""
    date_str = kwargs["ds"]
    base_dir = f"{OUTPUT_BASE}/{date_str}"

    conn = psycopg2.connect(**DW_CONFIG)
    cur = conn.cursor()

    # --- Carregar tabelas SQL ---
    sql_dir = os.path.join(base_dir, "sql")
    for table in TABLES_TO_EXTRACT:
        file_path = os.path.join(sql_dir, f"{table}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            cur.execute(f"DROP TABLE IF EXISTS {table};")
            cur.execute(
                f"CREATE TABLE {table} ({', '.join([col + ' TEXT' for col in df.columns])});"
            )
            for _, row in df.iterrows():
                cur.execute(
                    f"INSERT INTO {table} ({', '.join(df.columns)}) VALUES ({', '.join(['%s']*len(df.columns))})",
                    tuple(row),
                )
            print(f"✅ Tabela {table} carregada no DW ({len(df)} registros)")

    # --- Carregar transações (CSV externo) ---
    csv_file = os.path.join(base_dir, "csv", "transacoes.csv")
    if os.path.exists(csv_file):
        df_csv = pd.read_csv(csv_file)

        # recria a tabela com colunas corretas
        cur.execute("DROP TABLE IF EXISTS transacoes;")
        cur.execute("""
            CREATE TABLE transacoes (
                data_transacao DATE,
                valor_transacao NUMERIC,
                num_conta INT
            );
        """)

        for _, row in df_csv.iterrows():
            cur.execute(
                "INSERT INTO transacoes (data_transacao, valor_transacao, num_conta) VALUES (%s, %s, %s)",
                (row["data_transacao"], row["valor_transacao"], row["num_conta"]),
            )

        print(f"✅ Tabela transacoes carregada no DW ({len(df_csv)} registros)")

    conn.commit()
    cur.close()
    conn.close()


# ------------------------------------------------------
# Função de verificação
# ------------------------------------------------------

def verify_dw(**kwargs):
    """Faz SELECT COUNT(*) em cada tabela no DW."""
    conn = psycopg2.connect(**DW_CONFIG)
    cur = conn.cursor()

    print("🔍 Verificando tabelas no Data Warehouse...")
    for table in TABLES_TO_EXTRACT + ["transacoes"]:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"✅ Tabela {table} contém {count} registros.")

    cur.close()
    conn.close()


# ------------------------------------------------------
# Definição da DAG
# ------------------------------------------------------

with DAG(
    dag_id="banvic_dag",
    start_date=datetime(2023, 1, 1),
    schedule_interval="35 4 * * *",
    catchup=False,
    tags=["banvic", "etl"],
) as dag:

    extract_sql_task = PythonOperator(
        task_id="extract_sql_tables",
        python_callable=extract_all_sql,
        provide_context=True,
    )

    extract_csv_task = PythonOperator(
        task_id="extract_csv_file",
        python_callable=extract_csv,
        provide_context=True,
    )

    load_task = PythonOperator(
        task_id="load_to_dw",
        python_callable=load_to_dw,
        provide_context=True,
    )

    verify_task = PythonOperator(
        task_id="verify_dw",
        python_callable=verify_dw,
        provide_context=True,
    )

    [extract_sql_task, extract_csv_task] >> load_task >> verify_task
