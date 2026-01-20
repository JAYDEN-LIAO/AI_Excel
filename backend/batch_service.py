import pandas as pd
import os
# 引入你原本的两个服务
from ai_service import get_formula_suggestion
from formula_service import apply_formula_to_file

def batch_process_files(file_path_list: list, user_requirement: str):
    """
    智能批处理入口：自动识别不同结构的文件，分组处理
    """
    # 1. 分组字典： { "列指纹字符串": [文件路径1, 文件路径2] }
    schema_groups = {}

    print(f"📦 收到 {len(file_path_list)} 个文件，正在进行结构分析...")

    # --- 第一步：按列结构分组 ---
    for f_path in file_path_list:
        try:
            # 优化：只读取前 0 行，极大提高速度，只为获取表头
            df_preview = pd.read_excel(f_path, nrows=0)

            # 生成指纹：将列名排序并拼接 (忽略顺序差异，只看列是否相同)
            # 如果需要严格区分列顺序，去掉 sorted() 即可
            cols = sorted(df_preview.columns.tolist())
            signature = "|".join(cols)

            if signature not in schema_groups:
                schema_groups[signature] = []
            schema_groups[signature].append(f_path)

        except Exception as e:
            print(f"⚠️ 跳过无法读取的文件 {f_path}: {e}")

    print(f"📊 分析完成，共识别出 {len(schema_groups)} 种不同的表格结构。")

    # --- 第二步：按组进行 AI 咨询与处理 ---
    batch_results = []

    for signature, files in schema_groups.items():
        print(f"\n======== 处理分组: 包含 {len(files)} 个文件 ========")
        print(f"列结构: {signature[:50]}...") # 打印一部分看看

        # 1. 选出代表文件 (Representative)
        rep_file = files[0]

        # 2. 调用 AI 获取处理逻辑 (该组只调一次 AI，节省 token)
        print(f"🤖 正在请求 AI 分析代表文件: {os.path.basename(rep_file)}")
        ai_result = get_formula_suggestion(rep_file, user_requirement)

        # 如果 AI 分析出错，这组所有文件都标记失败
        if ai_result.get('action_type') == 'error':
            for f in files:
                batch_results.append({
                    "original_file": f,
                    "status": "failed",
                    "error": ai_result.get('explanation')
                })
            continue

        # 3. 将同一套逻辑应用到该组所有文件
        for f in files:
            print(f"⚙️ 正在应用逻辑到: {os.path.basename(f)}")
            try:
                new_path, safe_name = apply_formula_to_file(f, ai_result)
                batch_results.append({
                    "original_file": f,
                    "processed_file": new_path,
                    "download_name": safe_name,
                    "status": "success",
                    "group_signature": signature
                })
            except Exception as e:
                batch_results.append({
                    "original_file": f,
                    "status": "failed",
                    "error": str(e)
                })

    return batch_results