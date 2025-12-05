import os
import time

from fastapi import FastAPI
from pymongo import MongoClient
from sqlalchemy import create_engine, text

app = FastAPI()

# --- 資料庫連線設定 (從環境變數讀取) ---
# 注意：在 Docker 內部要用 service name (postgres, mongodb) 而不是 localhost
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
PG_DB = os.getenv("POSTGRES_DB", "postgres")
PG_HOST = "postgres"  # docker-compose service name

MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
MONGO_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "password")
MONGO_HOST = "mongodb"  # docker-compose service name


# --- 連線測試函式 ---
def get_pg_connection():
    # 使用 SQLAlchemy 建立連線
    DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:5432/{PG_DB}"
    engine = create_engine(DATABASE_URL)
    return engine


def get_mongo_connection():
    # 連線字串
    MONGO_URL = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:27017/"
    client = MongoClient(MONGO_URL)
    return client


@app.get("/")
def read_root():
    return {"message": "Hello from NEW Fridge Backend!"}


@app.get("/health/postgres")
def health_pg():
    try:
        engine = get_pg_connection()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/health/mongo")
def health_mongo():
    try:
        client = get_mongo_connection()
        # 嘗試 ping admin 資料庫
        client.admin.command("ping")
        return {"status": "success", "message": "MongoDB connected!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
