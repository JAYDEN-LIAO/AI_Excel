# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 数据库连接配置
# 格式: postgresql://用户名:密码@地址:端口/数据库名
# 对应 docker-compose.yml 里的配置
SQLALCHEMY_DATABASE_URL = "postgresql://admin:password123@localhost:5432/excel_automation"

# 创建数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建模型基类
Base = declarative_base()

# 依赖注入工具：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()