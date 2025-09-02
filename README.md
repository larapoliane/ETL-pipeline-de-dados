# BanVic ETL Pipeline

## Estrutura
- source_db/banvic.sql → banco fonte Postgres 16
- source_data/transactions.csv → CSV fornecido
- dags/banvic_dag.py → DAG Airflow para extração + carga DW
- data/ → arquivos extraídos
- DW Postgres: localhost:5433
- Airflow Web: http://localhost:8080

## Rodando o projeto
1. Coloque o SQL e CSV nas pastas corretas
2. Suba os containers:
```bash
docker compose up -d --build
```
3. Inicialize Airflow e crie usuário admin
4. Ative a DAG `banvic_daily_etl` e execute
