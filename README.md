# BanVic ETL Pipeline

## Estrutura
- source_db/banvic.sql → banco fonte Postgres 16
- source_data/transactions.csv → CSV fornecido
- dags/banvic_dag.py → DAG Airflow para extração + carga DW
- data/ → arquivos extraídos
- DW Postgres: localhost:5433
- Airflow Web: http://localhost:8080


<img width="740" height="332" alt="image" src="https://github.com/user-attachments/assets/b7d67ea4-9ca4-4cff-83ca-d56176ef0f37" />



