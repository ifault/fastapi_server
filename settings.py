import os

from dotenv import load_dotenv

load_dotenv()

TORTOISE_ORM = {
    'connections': {
        "default": {
            "engine": "tortoise.backends.asyncpg",  # 使用 asyncpg 引擎连接 PostgreSQL
            "credentials": {
                "host": os.getenv("POSTGRES_HOST"),  # PostgreSQL 服务器主机地址
                "port": os.getenv("DATABASE_PORT"),  # PostgreSQL 服务器端口
                "user": os.getenv("DATABASE_USER"),  # PostgreSQL 用户名
                "password": os.getenv("DATABASE_PASSWORD"),  # PostgreSQL 密码
                "database": os.getenv("DATABASE_NAME"),  # PostgreSQL 数据库名称
            },
        }
    },
    'apps': {
        'models': {
            'models': ['models.db'],
            'default_connection': 'default'
        }
    },
    'use_tz': False,
    'timezone': 'Asia/Shanghai'
}
