# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from database import Base

class FileRecord(Base):
    __tablename__ = "file_records"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    stored_path = Column(String)
    file_size = Column(Float)
    status = Column(String, default="uploaded")
    upload_time = Column(DateTime(timezone=True), server_default=func.now())

    # 🟢 新增：父文件ID，用于关联“原件”和“修改后的文件”
    parent_id = Column(Integer, ForeignKey("file_records.id"), nullable=True)

class FormulaTemplate(Base):
    __tablename__ = "formula_templates"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)
    title = Column(String)
    description = Column(String)  # 🟢 补回 description
    prompt_text = Column(String)