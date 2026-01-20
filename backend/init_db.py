# backend/init_db.py
from database import engine, SessionLocal
import models  # 必须导入 models，否则 Base 找不到表定义
from models import FormulaTemplate

def init_db():
    print("⏳ 正在初始化数据库...")

    # 1. 自动创建表结构 (如果表不存在则创建，存在则忽略)
    models.Base.metadata.create_all(bind=engine)
    print("✅ 表结构 (file_records, formula_templates) 创建成功！")

    # 2. 插入预设的公式模板数据
    db = SessionLocal()
    try:
        # 先检查是否已经有数据，防止重复插入
        if db.query(FormulaTemplate).count() == 0:
            print("🌱 正在插入预设公式模板...")

            templates = [
                FormulaTemplate(
                    title="计算销售总额",
                    description="计算“金额”列的总和并写入最后一行",
                    category="计算",
                    prompt_text="请计算表格中“金额”这一列的所有数值之和，并将结果写入该列的最后一行。请确保使用 SUM 函数。"
                ),
                FormulaTemplate(
                    title="提取出生年份",
                    description="从身份证号中提取出生年到新列",
                    category="清洗",
                    prompt_text="假设表格中有一列包含身份证号，请在旁边新增一列“出生年份”，利用公式从身份证号中提取前4位年份信息（通常在第7-10位）。"
                ),
                FormulaTemplate(
                    title="删除空数据行",
                    description="删除所有没有任何内容的空行",
                    category="清洗",
                    prompt_text="请检查表格，删除所有内容完全为空的行。请使用 pandas 操作，不要保留索引。"
                ),
                FormulaTemplate(
                    title="Top 5 排名",
                    description="按数值从大到小排序并保留前5名",
                    category="统计",
                    prompt_text="请根据表格中的数值列（如果有多个数值列，选择最靠右的一列）进行降序排序，并只保留数值最大的前 5 行数据，删除其余行。"
                )
            ]

            db.add_all(templates)
            db.commit()
            print(f"✅ 已成功插入 {len(templates)} 条预设模板！")
        else:
            print("ℹ️ 模板表已有数据，跳过插入步骤。")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()