# 1. Comece com a imagem oficial do Airflow (versão estável)
FROM apache/airflow:2.10.2

# 2. Copie nossa lista de compras para dentro do container
COPY requirements.txt /requirements.txt

# 3. Instale tudo o que está na lista
RUN pip install --no-cache-dir -r /requirements.txt