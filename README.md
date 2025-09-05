# BanVic ETL Pipeline

Este projeto implementa um pipeline de **ETL (Extract, Transform, Load)** utilizando **Apache Airflow** e **PostgreSQL**.  
O objetivo é centralizar dados de diferentes fontes.

---

# Estrutura do Projeto

```bash
.
├── dags/                → onde está sua DAG (`banvic_dag.py`)
│   └── banvic_dag.py
│
├── docker-compose.yml   → para subir os containers
│
├── requirements.txt     → para instalar dependências
│
├── README.md            → com instruções
│
├── source_data/         → dados de entrada em CSV necessários para reproduzir o pipeline
│   └── transacoes.csv
│
└── source_db/           → dados de entrada em SQL necessários para reproduzir o pipeline
    └── banvic.sql


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



📌 Pré-requisitos Para Rodar o Projeto

Antes de rodar o pipeline, certifique-se de ter instalado:

 * Docker (>= 20.x)

 * Docker Compose (>= 1.29)

 * Git (para clonar o repositório)

## Passo a Passo de Execução

1 Clonar o projeto

  git clone <url-do-repositorio>
  cd <nome-do-projeto>

2 Subir os containers
  docker compose up -d --build

  Irá subir:
  * airflow_webserver → Interface do Airflow
  * airflow_scheduler → Scheduler do Airflow
  * airflow_db → Banco interno do Airflow
  * source_db → Banco de origem (com dados do banvic.sql)
  * dw_postgres → Data Warehouse

3 Acessar o Airflow

Abra no navegador:
👉 http://localhost:8080
Usuário e senha padrão:
  Usuário: admin
  Senha: admin

4 Executar a DAG

Na UI do Airflow, ative a DAG banvic_dag.
Clique em Trigger DAG para rodar manualmente.
Acompanhe os logs de cada task.

Para Conferir as Tabelas no DW (dw_postgres):

docker exec -it dw_postgres psql -U airflow -d airflow

E consultar por exemplo:

SELECT COUNT(*) FROM clientes;
SELECT COUNT(*) FROM transacoes;


📌 Observações

* O pipeline roda diariamente às 04:35 da manhã.
* As extrações são idempotentes (recriam os arquivos a cada execução).
* A DAG só carrega dados no DW se todas as extrações forem concluídas com sucesso.









