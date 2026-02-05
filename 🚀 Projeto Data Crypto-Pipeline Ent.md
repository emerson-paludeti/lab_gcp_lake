# 🚀 Projeto: Data Crypto-Pipeline Enterprise

**Objetivo:** Capturar dados de mercado (API), garantir sua persistência (Data Lake) e realizar o processamento analítico (Data Warehouse).

----------

## 🏗️ 1. Arquitetura do Ecossistema

1.  **Docker:** Cria o ambiente onde tudo funciona, isolado do seu computador.
    
2.  **Airflow:** Decide que horas o processo começa a ser executado e o que fazer se algo quebrar.
    
3.  **Python:** Busca o dado e na API e faz a ingestão.
    
4.  **Google Cloud Storage:** Data Lake.
    
5.  **BigQuery:** Transforma o dado bruto em informação (Data Warehouse).
    

----------

## ☁️ 2. Configuração Detalhada: Google Cloud Platform (GCP)

### 2.1. O Projeto e Faturamento

-   **Nome do Projeto:** `lab-dados-gcp` (É o identificador único de todos os recursos).
    
-   **Conta de Faturamento (Billing):** No GCP, nada funciona sem estar vinculado a uma conta de faturamento (mesmo no nível gratuito). O projeto foi associado à sua conta de faturamento padrão para liberar o uso do BigQuery e Storage.
    

### 2.2. Google Cloud Storage (O Data Lake)

-   **Nome do Bucket:** `lab-dados-gcp-raw`
    
-   **Função:** Funciona como um HD na nuvem. Aqui salvamos os arquivos `.json` puros, exatamente como vieram da API.
    
-   **Configuração de Classe:** _Standard_ (Para acesso frequente) e Região _US_ (Mais barata e próxima dos servidores do BigQuery).
    

### 2.3. Google BigQuery (O Data Warehouse)

-   **Dataset:** `crypto_analytics` (É a "pasta" que contém as tabelas).
    
-   **Tabelas:**
    
    1.  **`BRZ_assets` (Bronze):** Dados crus. Se a API mandou 100 moedas, as 100 estão aqui com todos os erros e formatos estranhos.
        
    2.  **`SLV_assets` (Silver):** Dados limpos. Aqui o que era texto vira número decimal e o que era bagunçado é organizado.
        
    3.  **`GLD_market_summary` (Gold):** O produto final. Contém apenas o resumo (médias e categorias), pronto para a criação das visões (relatórios).
        ----------

## 📂 3. Guia de Arquivos: O que cada um faz?

Sua pasta `airflow-docker` é o coração do projeto. Aqui está o papel de cada integrante:

**Arquivo**

**Função Explicada**

**`docker-compose.yaml`**

É o manual de instruções do Docker. Ele diz: "Crie um servidor para o Airflow, um banco de dados para ele e conecte tudo".

**`Dockerfile`**

É a receita de bolo da imagem. Ele pega o Airflow padrão e "instala" as ferramentas do Google dentro dele.

**`requirements.txt`**

Uma lista de compras. Contém o nome das bibliotecas Python (como `google-cloud-bigquery`) que o script precisa para funcionar.

**`credentials.json`**

É o seu crachá de acesso. Sem esse arquivo, o Google barra a entrada do seu código na nuvem.

**`pipeline_oficial.py`**

O código principal. Ele faz a extração da API, o upload para o Storage e as consultas SQL no BigQuery.

**`agendador_crypto.py`**

O "despertador". Ele diz ao Airflow: "Todo dia, às 09:00, execute o arquivo `pipeline_oficial.py`".

**`.airflowignore`**

Um aviso de "não entre". Diz ao Airflow para não tentar agendar o script de execução, apenas o despertador.

----------

## 🛠️ 4. O Passo a Passo da Execução (O que aconteceu por trás?)

1.  **O Comando `docker compose build`:** O Docker leu o `Dockerfile` e criou uma máquina virtual com Python e todas as ferramentas do Google instaladas.
    
2.  **O Comando `docker compose up -d`:** Ligou os servidores. O Airflow lê a pasta `dags`.
    
3.  **A Autenticação:** O script Python lê o `credentials.json`. Ele usou esse arquivo para dizer ao Google: "Eu sou o administrador do projeto `lab-dados-gcp`, deixe-me entrar".
    
4.  **O Fluxo de Dados:**
    
    -   O Python buscou os dados na API CoinCap.
        
    -   Salvou um arquivo no Storage (Bucket).
        
    -   Mandou um comando para o BigQuery: "Pegue aquele arquivo que acabei de salvar no Storage e coloque na tabela Bronze".
        
    -   Mandou outro comando: "Agora limpe a Bronze e salve na Silver, e depois resuma na Gold".
        

----------

## 📊 5. Estrutura de Dados nas Tabelas

### Tabela Silver (`SLV_assets`)

-   `id`: Nome da moeda (ex: bitcoin).
    
-   `symbol`: Sigla (ex: BTC).
    
-   `priceUsd`: Preço convertido para número (FLOAT64) para permitir cálculos.
    
-   `data_carga`: Horário em que o dado entrou no sistema.
    

### Tabela Gold (`GLD_market_summary`)

-   `categoria_mercado`: Classificação automática ("Alto Valor" para moedas caras).
    
-   `qtd_ativos`: Quantas moedas caíram naquela categoria.
    
-   `preco_medio_usd`: A média de preço daquele grupo.
    

----------

## 💡 6. Decisões de Projeto:

-   **Por que não salvar direto no banco?** Se o banco de dados falhar, perdemos o dado. Salvando no Storage primeiro (Data Lake), temos um backup eterno do dado bruto.
    
-   **Por que o Airflow?** Se a API cair às 3 da manhã, o Airflow vai tentar de novo sozinho. Você não precisa acordar para consertar.
    
-   **Por que Docker?** Se você trocarmos a infra local, basta instalar o Docker e rodar um comando. Tudo funcionará igual, sem precisar configurar o Windows novamente.