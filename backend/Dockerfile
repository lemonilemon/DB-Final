# 使用輕量級 Python 映像 (升級至 3.13)
FROM python:3.13-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴 (如果需要編譯某些套件)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# 複製 requirements 並安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 暴露 Port 8000
EXPOSE 8000

# 啟動 FastAPI 伺服器
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
