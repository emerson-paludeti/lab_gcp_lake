import time
import json
import requests
from google.cloud import storage
from google.cloud import bigquery
from google.oauth2 import service_account

# --- CONFIGURAÇÕES ---
KEY_PATH = 'credentials.json'
PROJECT_ID = 'lab-dados-gcp'            # ID do projeto (minúsculo)
BUCKET_NAME = 'lab-dados-gcp-raw'       # O nome EXATO do seu bucket
DATASET_ID = 'crypto_analytics'

# --- AUTENTICAÇÃO ---
print(f"[INIT] Autenticando no projeto '{PROJECT_ID}'...")
credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
storage_client = storage.Client(credentials=credentials, project=PROJECT_ID)
bq_client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

def setup_inicial():
    """Garante que o Dataset existe"""
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"
    try:
        bq_client.create_dataset(dataset, exists_ok=True)
        print(f"[SETUP] Dataset '{DATASET_ID}' verificado.")
    except Exception as e:
        print(f"[ERRO SETUP] {e}")

# 1. INGESTÃO (AGORA GERANDO NDJSON)
def ingestao_ndjson():
    print(">>> 1. Baixando API e convertendo para NDJSON...")
    url = "https://api.coincap.io/v2/assets?limit=20"
    
    lista_dados = []
    
    # Tentativa de pegar dados reais
    try:
        response = requests.get(url, timeout=10)
        dados_brutos = response.json()
        # A CoinCap retorna {"data": [...]}. Pegamos só a lista.
        lista_dados = dados_brutos.get('data', [])
        print("[API] Sucesso! Dados reais baixados.")
    except Exception as e:
        print(f"[AVISO] Falha na API ({e}). Usando dados simulados.")
        lista_dados = [
            {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin", "priceUsd": "65000.50", "marketCapUsd": "1200000000000", "changePercent24Hr": "2.5"},
            {"id": "ethereum", "symbol": "ETH", "name": "Ethereum", "priceUsd": "3500.20", "marketCapUsd": "400000000000", "changePercent24Hr": "-1.2"},
            {"id": "solana", "symbol": "SOL", "name": "Solana", "priceUsd": "140.00", "marketCapUsd": "60000000000", "changePercent24Hr": "5.0"}
        ]

    # --- O PULO DO GATO: CONVERSÃO PARA NDJSON ---
    # Transforma a lista em várias strings, uma por linha
    ndjson_data = '\n'.join([json.dumps(record) for record in lista_dados])
    
    try:
        timestamp = int(time.time())
        file_name = f"raw/coins_{timestamp}.json"
        
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(file_name)
        # Salvamos o NDJSON (texto puro) e não o JSON (application/json)
        blob.upload_from_string(ndjson_data, content_type='text/plain')
        
        print(f"[STORAGE] Arquivo NDJSON salvo: gs://{BUCKET_NAME}/{file_name}")
        return f"gs://{BUCKET_NAME}/{file_name}"
    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha no Upload: {e}")
        return None

# 2. BRONZE (LÊ NDJSON)
def camada_bronze(gcs_uri):
    if not gcs_uri: return
    print(">>> 2. Carga Bronze...")
    
    table_id = f"{PROJECT_ID}.{DATASET_ID}.BRZ_assets"
    
    # Configuração explícita para NDJSON
    job_config = bigquery.LoadJobConfig(
        source_format="NEWLINE_DELIMITED_JSON",  # O formato correto
        autodetect=True,
        write_disposition="WRITE_APPEND",
        ignore_unknown_values=True  # Ajuda a não quebrar se vier campo novo
    )
    
    try:
        job = bq_client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
        job.result()  # Espera terminar
        print(f"[BIGQUERY] Tabela Bronze carregada com sucesso.")
    except Exception as e:
        print(f"[ERRO BRONZE] {e}")

# 3. SILVER
def camada_silver():
    print(">>> 3. Transformação Silver...")
    # Como o NDJSON já é plano, não precisamos mais do UNNEST(data)
    # A query fica até mais simples!
    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.SLV_assets` AS
    SELECT
        id as asset_id,
        symbol,
        name,
        CAST(priceUsd AS FLOAT64) as price_usd,
        CAST(marketCapUsd AS FLOAT64) as market_cap,
        CAST(changePercent24Hr AS FLOAT64) as change_24h,
        CURRENT_TIMESTAMP() as data_carga
    FROM `{PROJECT_ID}.{DATASET_ID}.BRZ_assets`
    """
    try:
        bq_client.query(sql).result()
        print("[BIGQUERY] Tabela Silver atualizada.")
    except Exception as e:
        print(f"[ERRO SILVER] {e}")

# 4. GOLD
def camada_gold():
    print(">>> 4. Transformação Gold...")
    sql = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET_ID}.GLD_market_summary` AS
    SELECT
        CASE 
            WHEN price_usd > 1000 THEN 'Alto Valor'
            ELSE 'Baixo Valor'
        END as categoria,
        COUNT(asset_id) as qtd_moedas,
        ROUND(AVG(price_usd), 2) as preco_medio_usd
    FROM `{PROJECT_ID}.{DATASET_ID}.SLV_assets`
    GROUP BY 1
    ORDER BY 3 DESC
    """
    try:
        bq_client.query(sql).result()
        print("[BIGQUERY] Tabela Gold finalizada.")
    except Exception as e:
        print(f"[ERRO GOLD] {e}")

if __name__ == "__main__":
    setup_inicial()
    uri = ingestao_ndjson()
    if uri:
        camada_bronze(uri)
        camada_silver()
        camada_gold()
        print("\n--- SUCESSO! ---")