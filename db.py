import os
import json
import pymysql
from dotenv import load_dotenv

load_dotenv()

_DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "multi_agent_rag"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_conn():
    return pymysql.connect(**_DB_CONFIG)


def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    phone VARCHAR(20) PRIMARY KEY,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    phone VARCHAR(20) NOT NULL,
                    messages JSON NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_phone (phone),
                    FOREIGN KEY (phone) REFERENCES users(phone) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_documents (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    phone VARCHAR(20) NOT NULL,
                    index_id VARCHAR(50) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (phone) REFERENCES users(phone) ON DELETE CASCADE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    phone VARCHAR(20) PRIMARY KEY,
                    settings JSON NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (phone) REFERENCES users(phone) ON DELETE CASCADE
                )
            """)
        conn.commit()
    finally:
        conn.close()
