# backend/update_schema.py
from database import engine
from sqlalchemy import text
from models import Base

def update_schema():
    print("🛠️ 正在更新数据库结构...")

    # 获取数据库连接
    with engine.connect() as conn:
        # 1. 安全起见，我们只删除 file_records 表
        #这会清空“已上传文件”的记录，但绝对不会影响 formula_templates (公式模板)
        print("🗑️ 正在重建 file_records 表 (以添加 parent_id 字段)...")

        # 使用 CASCADE 以防有其他依赖（虽然目前没有）
        conn.execute(text("DROP TABLE IF EXISTS file_records CASCADE;"))
        conn.commit()

    # 2. 调用 SQLAlchemy 重新创建缺失的表
    # 因为 formula_templates 还在，它会被跳过
    # 因为 file_records 刚被删了，它会被按最新模型重新创建（包含 parent_id）
    Base.metadata.create_all(bind=engine)

    print("✅ 数据库结构更新完成！")
    print("   - file_records 表已重建 (包含 parent_id)")
    print("   - formula_templates 表保持原样 (数据未丢失)")

if __name__ == "__main__":
    update_schema()