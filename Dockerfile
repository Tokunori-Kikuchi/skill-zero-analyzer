FROM python:3.11-slim

WORKDIR /app

# Chromeをインストール（ARM64対応）
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y chromium \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . /app

# データディレクトリを作成
RUN mkdir -p /app/data

# 環境変数を設定
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/chromium

# デフォルトコマンド
CMD ["python", "data_processor.py"]