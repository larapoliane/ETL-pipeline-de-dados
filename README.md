# BanVic ETL Pipeline

Este projeto implementa um pipeline de **ETL (Extract, Transform, Load)** utilizando **Apache Airflow** e **PostgreSQL**.  
O objetivo é centralizar dados de diferentes fontes (ERP, CRM, Marketing) em um **Data Warehouse** para possibilitar análises e integração com ferramentas de BI (Metabase, PowerBI, Looker, etc.).

---

## 🚀 Visão Geral do Pipeline

Fluxo de dados:

1. **Extração**  
   - Tabelas do banco de origem (`source_db`, inicializado a partir de `banvic.sql`)  
   - Arquivo CSV de transações (`transacoes.csv`)  

2. **Armazenamento Temporário (Data Lake Local)**  
   - Os dados extraídos são salvos em CSV no diretório `data/`  
   - Estrutura de diretórios:  
     ```
     data/<ano>-<mes>-<dia>/
        ├── sql/
        │    ├── clientes.csv
        │    ├── contas.csv
        │    ├── propostas_credito.csv
        │    └── agencias.csv
        └── csv/
             └── transacoes.csv
     ```

3. **Carga no Data Warehouse (DW)**  
   - Os CSVs são carregados em um banco PostgreSQL separado (`dw_postgres`)  
   - As tabelas são recriadas a cada execução (idempotência)  

4. **Verificação**  
   - O pipeline executa queries de contagem (`SELECT COUNT(*)`) no DW para garantir que os dados foram carregados corretamente.  

---

## 🛠️ Tecnologias Utilizadas

- [Apache Airflow 2.7.2](https://airflow.apache.org/) → Orquestração das tarefas  
- [PostgreSQL 16](https://www.postgresql.org/) → Banco de origem e Data Warehouse  
- [Docker Compose](https://docs.docker.com/compose/) → Gerenciamento dos serviços  

---
## 📂 Estrutura do Projeto
ETL-pipeline-de-dados/
├── dags/
│ └── banvic_dag.py # DAG do Airflow (pipeline principal)
├── source_db/
│ └── banvic.sql # Dump SQL do banco de origem
├── source_data/
│ └── transacoes.csv # Arquivo CSV de transações
├── data/ # Data Lake (gerado automaticamente)
├── dbdata/ # Volume do banco de origem (Postgres)
├── dwdata/ # Volume do Data Warehouse
├── airflow_db/ # Volume do metadatabase do Airflow
└── docker-compose.yml # Configuração dos serviços






<img width="740" height="332" alt="image" src="https://github.com/user-attachments/assets/b7d67ea4-9ca4-4cff-83ca-d56176ef0f37" />



