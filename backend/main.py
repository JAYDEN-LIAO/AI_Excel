# backend/main.py
import os
import shutil
import uuid
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc  # 🟢 必须添加这一行！
from pydantic import BaseModel
from typing import Union
from fastapi.responses import FileResponse
from urllib.parse import quote
from typing import List
from ai_service import get_multi_file_agent
#from formula_service import apply_multi_file_operation

# --- 本地模块引入 ---
from database import engine, Base, get_db
# 🟢 变更1：引入 FormulaTemplate 模型
from models import FileRecord, FormulaTemplate
from formula_service import apply_formula_to_file
# 确保 ai_service 中这两个函数都存在
from ai_service import get_formula_suggestion, get_ai_analysis

# 1. 自动创建数据库表
# (这会同时检查 file_records 和 formula_templates 表是否存在)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Excel自动化处理系统")

# 2. 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置上传文件夹
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class MultiFileRequest(BaseModel):
    file_ids: List[int]  # 用户选中的多个文件 ID
    query: str           # 用户需求 (例如: "把表A和表B按工号合并...")
# --- 定义请求模型 ---
class ChatRequest(BaseModel):
    file_id: Union[str, int]
    query: str

class TemplateCreate(BaseModel):
    title: str
    description: str
    prompt_text: str
    category: str  # 🟢 新增字段

class TemplateUpdate(BaseModel):
    title: str
    description: str
    prompt_text: str
    category: str  # 🟢 新增字段，允许编辑时修改分类

# --- 接口定义 ---

@app.post("/api/process_multi_files")
def process_multi_files(request: MultiFileRequest, db: Session = Depends(get_db)):
    # A. 查出所有文件记录
    files = db.query(FileRecord).filter(FileRecord.id.in_(request.file_ids)).all()

    if len(files) < 1:
        raise HTTPException(status_code=400, detail="至少选择一个文件")

    # B. 准备上下文：读取所有文件到内存字典 'dfs'
    loaded_dfs = {}
    file_map_for_ai = {} # 仅用于给 AI 提供预览路径

    print(f"🔄 开始加载 {len(files)} 个文件...")

    for f in files:
        if not os.path.exists(f.stored_path):
            continue
        try:
            # 读取数据
            df_temp = pd.read_excel(f.stored_path)
            # 存入字典
            loaded_dfs[f.filename] = df_temp
            # 记录路径供 AI 预览函数使用
            file_map_for_ai[f.filename] = f.stored_path
        except Exception as e:
            print(f"❌ 读取文件 {f.filename} 失败: {e}")

    if not loaded_dfs:
        raise HTTPException(status_code=400, detail="没有成功加载任何文件，请检查文件是否存在")

    try:
        # C. 第一步：找 AI 写代码
        print(f"🤖 请求 AI 进行多表分析: {list(loaded_dfs.keys())}")

        # 调用 AI (这里 ai_service.py 已经修改为返回字典)
        ai_result = get_multi_file_agent(file_map_for_ai, request.query)

        # 🟢【关键修改】解析 AI 返回的字典
        column_formulas_data = {} # 初始化为空字典

        if isinstance(ai_result, dict):
            py_code = ai_result.get("python_code", "")
            excel_formula_display = ai_result.get("excel_formula", "AI 未提供公式逻辑")
            # 提取分列公式
            column_formulas_data = ai_result.get("column_formulas", {})
        else:
            # 容错：如果 ai_service 没更新或者出错返回了字符串
            py_code = str(ai_result)
            excel_formula_display = "多表复杂计算"

        print(f"🐍 AI生成的代码:\n{py_code}")
        print(f"➗ AI生成的公式逻辑: {excel_formula_display}")

        # D. 第二步：执行代码
        # 建立沙箱环境
        exec_globals = {
            'pd': pd,        # 注入 pandas
            'dfs': loaded_dfs, # 🟢 注入所有表数据
            'result_df': None  # 结果占位符
        }

        # 执行 AI 代码
        exec(py_code, exec_globals)

        # 获取结果
        final_df = exec_globals.get('result_df')

        if final_df is None or not isinstance(final_df, pd.DataFrame):
            raise Exception("代码执行完毕，但 `result_df` 为空。请确保 AI 代码将结果赋值给了 `result_df`。")

        # E. 第三步：结果存库
        new_filename = f"多表计算结果_{uuid.uuid4().hex[:6]}.xlsx"
        new_path = os.path.join(UPLOAD_DIR, new_filename)

        # 保存 Excel
        final_df.to_excel(new_path, index=False)
        new_file_size = os.path.getsize(new_path)

        # 写入数据库
        db_file = FileRecord(
            filename="多表合并分析结果.xlsx",
            stored_path=new_path,
            file_size=new_file_size,
            status="processed",
            parent_id=files[0].id
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # 🟢【关键修改】返回结构增加 raw_result，适配前端展示
        return {
            "success": True,
            "msg": "多表处理成功",
            "file_id": db_file.id,
            "download_url": f"/api/download/{new_filename}",
            "ai_code_used": py_code,
            # 构造一个前端能看懂的 result 对象，用于显示在黄色框框里
            "raw_result": {
                "action_type": "structure",
                "excel_formula": excel_formula_display, # 这里就是那串长公式
                "column_formulas": column_formulas_data, # 👈 新增：把分列公式字典传回给前端
                "explanation": f"已根据指令合并 {len(files)} 个文件并计算结果。",
                "target_position": "新文件",
                "mode": "structure"
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "msg": f"处理失败: {str(e)}"}
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend is running!"}

# ==========================================
# 🟢 新增接口：获取对应历史记录 (FilesPage用)
# ==========================================
@app.get("/api/history")
def get_history_list(q: str = None, db: Session = Depends(get_db)):
    """
    返回成对的文件结构：[{ original: {...}, result: {...} }]
    """
    # 1. 查询所有原始文件 (parent_id 为 NULL)
    query = db.query(FileRecord).filter(FileRecord.parent_id == None)

    if q:
        query = query.filter(FileRecord.filename.contains(q))

    # 按时间倒序
    originals = query.order_by(desc(FileRecord.upload_time)).all()

    history_list = []

    for org in originals:
        # 2. 查找该文件的最新生成的子文件
        # 这里假设一个原文件可能对应多个结果，我们只取最新的一个，或者你也可以改为返回列表
        child = db.query(FileRecord) \
            .filter(FileRecord.parent_id == org.id) \
            .order_by(desc(FileRecord.upload_time)) \
            .first()

        item = {
            "id": org.id, # 唯一标识
            "original": {
                "file_id": org.id,
                "filename": org.filename,
                "upload_time": org.upload_time.strftime("%Y-%m-%d %H:%M") if org.upload_time else ""
            },
            "result": None
        }

        if child:
            item["result"] = {
                "file_id": child.id,
                "filename": child.filename,
                "generated_time": child.upload_time.strftime("%Y-%m-%d %H:%M") if child.upload_time else "",
                # 构造下载链接
                "download_url": f"http://127.0.0.1:8000/api/download/{child.stored_path.split(os.sep)[-1]}"
            }

        history_list.append(item)

    return {
        "success": True,
        "data": history_list
    }

# ==========================================
# 🟢 新增接口：获取公式模板库 (Section 0)
# ==========================================
@app.get("/api/templates")
def get_templates(db: Session = Depends(get_db)):
    """
    获取所有预设的 AI 公式模板
    """
    try:
        templates = db.query(FormulaTemplate).all()
        return {
            "success": True,
            "data": templates
        }
    except Exception as e:
        print(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail="获取模板失败")

# ==========================================
# 🟢 新增接口：更新公式模板 (已修复 NameError)
# ==========================================
# 修复 update_template 结尾被截断的问题
@app.put("/api/templates/{template_id}")
def update_template(template_id: int, template_update: TemplateUpdate, db: Session = Depends(get_db)):
    # 查找模板
    db_template = db.query(FormulaTemplate).filter(FormulaTemplate.id == template_id).first()

    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")

    # 更新字段
    db_template.title = template_update.title
    db_template.description = template_update.description
    db_template.prompt_text = template_update.prompt_text
    db_template.category = template_update.category # 记得加上这个

    # 提交保存
    db.commit()
    db.refresh(db_template)
    return {"success": True, "data": db_template}
# ==========================================
# 🟢 新增接口：创建新模板
# ==========================================
@app.post("/api/templates")
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    try:
        new_tpl = FormulaTemplate(
            title=template.title,
            description=template.description,
            prompt_text=template.prompt_text,
            category=template.category
        )
        db.add(new_tpl)
        db.commit()
        db.refresh(new_tpl)
        return {"success": True, "data": new_tpl}
    except Exception as e:
        print(f"Create Error: {e}")
        raise HTTPException(status_code=500, detail="创建模板失败")

# ==========================================
# 🟢 新增接口：删除模板
# ==========================================
@app.delete("/api/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    tpl = db.query(FormulaTemplate).filter(FormulaTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="未找到该模板")

    try:
        db.delete(tpl)
        db.commit()
        return {"success": True, "msg": "删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除失败")
    # 提交保存
    db.commit()
    db.refresh(db_template)
    return {"success": True, "data": db_template}

# ==========================================
# 1. 文件上传接口
# ==========================================
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="只支持 Excel 文件")

    # 生成安全文件名
    file_ext = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_location = os.path.join(UPLOAD_DIR, safe_filename)

    # 保存文件
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(file_location)

    # 存入数据库
    db_file = FileRecord(
        filename=file.filename,    # 原始文件名 (显示用)
        stored_path=file_location, # 物理路径 (读取用)
        file_size=file_size,
        status="uploaded"
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return {"msg": "上传成功", "file_id": db_file.id, "filename": db_file.filename}

# ==========================================
# 🟢 新增接口：获取指定文件的预览数据
# ==========================================
# ==========================================
# 🟢 修复后的接口：获取指定文件的预览数据
# ==========================================
@app.get("/api/files/{file_id}/data")
def get_file_data(file_id: int, db: Session = Depends(get_db)):
    # 1. 数据库查询文件记录
    file_record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 2. 获取文件路径 (🟢 核心修复：使用 stored_path)
    # models.py 中定义的是 stored_path，不是 file_path
    file_path = file_record.stored_path

    # 兼容性/容错处理：检查物理文件
    if not os.path.exists(file_path):
        # 尝试在 uploads 目录下找
        potential_path = os.path.join(UPLOAD_DIR, os.path.basename(file_path))
        if os.path.exists(potential_path):
            file_path = potential_path
        else:
            print(f"DEBUG: 数据库路径: {file_record.stored_path}，实际查找路径: {file_path}")
            raise HTTPException(status_code=404, detail="磁盘上未找到该文件，可能已被删除")

    try:
        # 3. 读取 Excel (只读取前 50 行以提高速度)
        # keep_default_na=False 可以防止 pandas 把空单元格读成 NaN
        df = pd.read_excel(file_path, nrows=50)

        # 4. 再次确保处理空值 (JSON 标准不支持 NaN)
        df = df.fillna("")

        # 针对包含 "Timestamp" (日期) 类型的列进行字符串转换，防止 JSON 序列化报错
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)

        # 5. 构造 Ant Design Vue Table 需要的 columns 格式
        columns = [
            {"title": col, "dataIndex": col, "key": col, "width": 150}
            for col in df.columns
        ]

        # 6. 构造数据列表
        data = df.to_dict(orient="records")

        return {
            "success": True,
            "filename": file_record.filename,
            "columns": columns,
            "data": data,
            "total_rows": 50 # 只是预览，或者你可以再读一次获取 len(df)
        }

    except Exception as e:
        print(f"Read Excel Error: {e}")
        # 打印详细堆栈以便调试
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")
# ==========================================
# 2. 读取 Excel 数据接口 (用于初始加载)
# ==========================================
# @app.get("/api/files/{file_id}/data")
# def get_file_data(file_id: str, db: Session = Depends(get_db)):
#     record = db.query(FileRecord).filter(FileRecord.id == file_id).first()
#     if not record:
#         raise HTTPException(status_code=404, detail="文件不存在")
#
#     try:
#         df = pd.read_excel(record.stored_path)
#         # 替换 NaN 为空字符串，防止 JSON 序列化报错
#         df = df.fillna("")
#
#         columns = [{"title": col, "dataIndex": col, "key": col, "width": 150} for col in df.columns]
#         data = df.head(20).to_dict(orient="records") # 限制返回前20行
#
#         return {
#             "filename": record.filename,
#             "columns": columns,
#             "data": data,
#             "total_rows": len(df)
#         }
#     except Exception as e:
#         print(f"Error reading excel: {e}")
#         raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")

# ==========================================
# 3. 纯 AI 对话接口 (咨询用)
# ==========================================
@app.post("/api/chat")
def chat_with_data(request: ChatRequest, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == request.file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 调用 ai_service
    ai_result = get_ai_analysis(record.stored_path, request.query)

    # 🟢 修复：ai_service 已经返回了 {"answer": "..."}，这里直接返回 ai_result 即可
    # 如果 ai_service 返回的是纯字符串，则封装一下
    if isinstance(ai_result, dict):
        return ai_result
    else:
        return {"answer": ai_result}
# ==========================================
# 4. 核心：智能操作接口 (生成公式/修改结构)
# ==========================================
@app.post("/api/generate_formula")
def generate_excel_formula(request: ChatRequest, db: Session = Depends(get_db)):
    record = db.query(FileRecord).filter(FileRecord.id == request.file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="文件不存在")

    ai_result = get_formula_suggestion(record.stored_path, request.query)

    if ai_result.get("action_type") == "error":
        return {"success": False, "msg": f"AI 分析失败: {ai_result.get('explanation')}"}

    try:
        # 执行物理操作
        new_path, new_filename = apply_formula_to_file(record.stored_path, ai_result)

        # 🟢 关键修改：将生成的文件存入数据库，并关联父ID
        new_file_size = os.path.getsize(new_path)
        db_child_file = FileRecord(
            filename=f"处理结果_{record.filename}", # 或者使用 new_filename
            stored_path=new_path,
            file_size=new_file_size,
            status="processed",
            parent_id=record.id  # 🟢 建立关联！
        )
        db.add(db_child_file)
        db.commit()
        db.refresh(db_child_file)

        # 预览逻辑 (保持不变)
        df_new = pd.read_excel(new_path)
        preview_df = df_new.head(50).fillna("")
        preview_columns = [{"title": col, "dataIndex": col, "key": col, "width": 100} for col in preview_df.columns]
        preview_rows = preview_df.to_dict(orient='records')

        return {
            "success": True,
            "msg": "处理成功",
            "download_url": f"/api/download/{os.path.basename(new_path)}", # 简化路径
            "file_id": db_child_file.id, # 返回新的 ID
            "raw_result": ai_result,
            "preview_data": {
                "columns": preview_columns,
                "dataSource": preview_rows
            }
        }

    except Exception as e:
        print(f"Process Error: {str(e)}")
        return {"success": False, "msg": f"执行失败: {str(e)}"}

# ==========================================
# 5. 文件下载接口
# ==========================================
@app.get("/api/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=filename # 建议此处结合数据库查真实文件名，这里暂且用物理文件名
        )
    return {"error": "File not found"}

# ==========================================
# 🟢 新增接口：智能批量上传 (支持 合并模式/独立模式)
# ==========================================
@app.post("/api/upload/batch")
async def batch_upload_files(
        files: List[UploadFile] = File(...),
        auto_merge: bool = Form(False),  # 🟢 开关：True=合并为一个, False=保持独立
        db: Session = Depends(get_db)
):
    """
    批量上传接口：
    - auto_merge=True: 强校验列名，合并为一个新文件，返回 1 个 file_id。
    - auto_merge=False: 弱校验，保存所有文件，返回 N 个 file_id 列表。
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="未上传任何文件")

    uploaded_records = [] # 只有独立模式会用到
    dfs_to_merge = []     # 只有合并模式会用到
    base_columns = None   # 用于合并模式的列名校验

    # --- 1. 循环处理所有文件 ---
    for file in files:
        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=400, detail=f"文件 {file.filename} 格式错误，仅支持 Excel")

        try:
            # 读取文件内容
            content = await file.read()
            df = pd.read_excel(content)

            # [通用验证]：空表检查
            if df.empty:
                raise HTTPException(status_code=400, detail=f"文件 {file.filename} 是空的，无法处理")

            # --- 分支逻辑 ---
            if auto_merge:
                # [合并模式]：严格校验列名一致性
                current_columns = list(df.columns)
                if base_columns is None:
                    base_columns = current_columns
                else:
                    if set(base_columns) != set(current_columns):
                        raise HTTPException(
                            status_code=400,
                            detail=f"【合并失败】文件 '{file.filename}' 的列名与其他文件不一致。\n预期: {base_columns}\n实际: {current_columns}"
                        )

                # 记录来源，准备合并
                df['_来源文件'] = file.filename
                dfs_to_merge.append(df)

            else:
                # [独立模式]：直接保存每个文件
                # 1. 保存物理文件
                file_ext = os.path.splitext(file.filename)[1]
                safe_filename = f"{uuid.uuid4().hex}{file_ext}"
                save_path = os.path.join(UPLOAD_DIR, safe_filename)

                # 由于 content 已经被 read() 读到内存，我们需要用 pandas 再写出，或者重置指针
                # 简单起见，直接用 pandas 写出（顺便还能标准化格式）
                df.to_excel(save_path, index=False)
                file_size = os.path.getsize(save_path)

                # 2. 存入数据库
                db_file = FileRecord(
                    filename=file.filename,
                    stored_path=save_path,
                    file_size=file_size,
                    status="uploaded"
                )
                db.add(db_file)
                db.commit()
                db.refresh(db_file)

                # 添加到返回列表
                uploaded_records.append({
                    "file_id": db_file.id,
                    "filename": db_file.filename
                })

        except HTTPException as he:
            raise he
        except Exception as e:
            print(f"Error processing {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"处理文件 {file.filename} 失败: {str(e)}")

    # --- 2. 后续处理 (针对合并模式) ---
    if auto_merge:
        try:
            # 执行合并
            final_df = pd.concat(dfs_to_merge, ignore_index=True)

            # 保存合并后的文件
            merged_filename = f"merged_{uuid.uuid4().hex[:8]}.xlsx"
            save_path = os.path.join(UPLOAD_DIR, merged_filename)
            final_df.to_excel(save_path, index=False)

            # 存库
            display_name = f"批量合并_{len(files)}个文件.xlsx"
            db_file = FileRecord(
                filename=display_name,
                stored_path=save_path,
                file_size=os.path.getsize(save_path),
                status="uploaded"
            )
            db.add(db_file)
            db.commit()
            db.refresh(db_file)

            return {
                "mode": "merge",
                "success": True,
                "msg": f"成功合并 {len(files)} 个文件",
                "file_info": {
                    "file_id": db_file.id,
                    "filename": db_file.filename,
                    "total_rows": len(final_df)
                }
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"合并过程出错: {str(e)}")

    # --- 3. 后续处理 (针对独立模式) ---
    else:
        return {
            "mode": "independent",
            "success": True,
            "msg": f"成功上传 {len(uploaded_records)} 个文件",
            "files": uploaded_records # 返回一个列表，包含所有ID
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)