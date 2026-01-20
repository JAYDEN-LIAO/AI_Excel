import pandas as pd
import json
import requests
import string
import re

# ================= 配置区 =================
# 请确保 API_KEY 正确且有余额
API_KEY = "sk-09469bb302c44f8a9b386790ac149f0a"
API_URL = "https://api.deepseek.com/chat/completions"
# =========================================

def get_col_letter(n):
    """
    将数字索引转化为 Excel 列名
    0 -> A, 1 -> B, ... 26 -> AA
    """
    s = ""
    while n >= 0:
        s = chr(n % 26 + 65) + s
        n = n // 26 - 1
    return s

def call_deepseek_raw(system_prompt, user_content):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "stream": False,
        "temperature": 0.1 # 低温度保证逻辑严谨
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            proxies={"http": None, "https": None}
        )
        response.encoding = 'utf-8'

        if response.status_code != 200:
            raise Exception(f"API Error ({response.status_code}): {response.text}")

        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Request Error: {repr(str(e))}")
        raise e

def get_ai_analysis(file_path: str, user_query: str):
    """
    Dashboard 智能咨询 (Chat) - Code Interpreter 模式
    """
    try:
        # 1. 读取全量数据 (但不要把数据喂给 AI，只喂结构)
        df = pd.read_excel(file_path)

        # 2. 准备元数据 (让 AI 知道有哪些列，数据长什么样，但只给看 3 行)
        columns = ", ".join(df.columns.tolist())
        dtypes = str(df.dtypes)
        preview_data = df.head(3).to_markdown(index=False)

        # 3. 构造 Prompt：要求 AI 不直接回答，而是写 Python 代码
        # 关键点：告诉 AI 它有一个现成的 dataframe 叫 'df'
        system_prompt = """
        你是一个 Python Pandas 数据分析专家。
        你不需要直接回答问题，而是需要编写 Python 代码来计算答案。
        
        【环境说明】
        1. 内存中已经加载了一个 pandas DataFrame，变量名为 `df`。
        2. 请根据用户问题，利用 `df` 编写代码。
        3. **必须**将最终计算结果赋值给变量 `result`。
        4. 代码中不要包含 print()，只进行计算和赋值。
        5. 输出格式：仅输出代码块，用 ```python 包裹，不要有其他废话。
        """

        user_message = f"""
        【数据结构信息】
        列名: {columns}
        数据类型:
        {dtypes}
        
        数据样例 (前3行):
        {preview_data}

        【用户问题】: {user_query}
        
        请写出计算用的 Python 代码：
        """

        # 4. 第一步：调用 AI 获取分析代码
        generated_content = call_deepseek_raw(system_prompt, user_message)

        # 5. 清洗 AI 返回的代码 (去掉 markdown 符号)
        code_match = re.search(r'```python(.*?)```', generated_content, re.DOTALL)
        if code_match:
            code_to_run = code_match.group(1).strip()
        else:
            # 如果 AI 没写 markdown，尝试直接用返回内容（容错）
            code_to_run = generated_content.strip().replace('```', '')

        print(f"🤖 AI 生成的代码:\n{code_to_run}") # 调试用，方便看后台

        # 6. 第二步：在本地 Python 环境中执行代码 (使用 exec)
        # 这是一个沙箱环境，传入 df，并准备捕获 result 变量
        local_vars = {"df": df, "pd": pd}

        try:
            exec(code_to_run, {}, local_vars)

            # 获取计算结果
            calculation_result = local_vars.get('result', "代码执行完毕，但未找到 result 变量")

        except Exception as e:
            return {"answer": f"分析执行出错: {str(e)}。AI 生成的代码可能不适配当前数据。"}

        # 7. (可选) 第三步：让 AI 把冰冷的数字转换成自然语言
        # 如果你只想要数字，可以直接返回 calculation_result
        # 这里我们再调一次 AI，让它组织语言
        summary_prompt = "你是一个贴心的数据助手。请根据用户的问题和计算出的结果，给出一个简洁、友好的回答。"
        summary_message = f"用户问题：{user_query}\n计算结果：{calculation_result}\n请回复用户："

        final_answer = call_deepseek_raw(summary_prompt, summary_message)

        return {"answer": final_answer}

    except Exception as e:
        return {"answer": f"系统内部错误: {str(e)}"}

def get_multi_file_agent(file_map: dict, user_query: str):
    """
    多文件关联分析 Agent (已升级：增强 Excel 公式鲁棒性约束)
    """
    # 1. 构建多表元数据 (保持不变)
    schema_info = []
    preview_info = []
    available_keys = list(file_map.keys())

    for fname, fpath in file_map.items():
        try:
            df_temp = pd.read_excel(fpath, nrows=3)
            cols = ", ".join(df_temp.columns.tolist())
            schema_info.append(f"- 文件名 Key: '{fname}' | 列: {cols}")
            preview_info.append(f"--- '{fname}' 预览 ---\n{df_temp.to_markdown(index=False)}")
        except Exception as e:
            schema_info.append(f"- 文件名: {fname} | 读取失败: {e}")

    schema_str = "\n".join(schema_info)
    preview_str = "\n".join(preview_info)

    # 2. 构造 Prompt
    # 🟢 核心修改：加入"Excel 公式强制规范" 模块，解决 #NAME? 和 #N/A 问题
    system_prompt = f"""
    你是一个 Python Pandas 高级数据工程师，同时也是 Excel 公式专家。
    
    【任务目标】
    1. 编写 Python 代码处理 `dfs` 字典中的数据。
    2. 编写 Excel 公式来解释你的操作。
    
    【💻 Python 执行环境】
    1. 只有一个变量：`dfs` (字典, Key=文件名, Value=DataFrame)。
    2. 必须通过文件名 Key 获取数据: `df = dfs['文件名']`。
    3. 最终结果赋值给 `result_df`。
    
    【🛡️ Excel 公式强制规范 (必须严格遵守)】
    为了确保公式在不同版本 Excel 中稳定运行，请遵守以下铁律：
    1. 📂 **外部文件引用规范 (关键修改)**：
       - 必须将数据源视为**独立的外部 Excel 文件**进行引用。
       - 引用格式必须严格遵循：`'[完整文件名]SheetName'!范围`。
       - 文件名必须包含后缀 (如 .xlsx)。
       - 默认假设 Sheet 名称为 "Sheet1" (除非你有明确理由使用其他名称)。
       - ✅ 正确示例: `'[上半年数据.xlsx]Sheet1'!$A:$A`
       - ❌ 错误示例: `'上半年数据'!$A:$A` (这是内部引用，禁止使用)
    
    2. 🚫 **禁止使用极新函数**：严禁使用 `CHOOSECOLS`, `CHOOSEROWS`。
       - ✅ **替代方案**：必须使用 `INDEX(array, , col_num)` 来提取列。
    
    3. 🧹 **必须清洗空值**：
       - 使用 `UNIQUE(VSTACK(...))` 合并数据时，必须嵌套 `FILTER` 去除 0 值。
       - 错误写法: `UNIQUE(VSTACK(A, B))`
       - 正确写法: `FILTER(unique_ids, unique_ids<>0)` 或 `unique_ids<>""`。
    
    4. 🛡️ **必须容错**：
       - 所有的 `XLOOKUP`, `VLOOKUP`, `MATCH` 必须包裹在 `IFERROR(..., 0)` 或 `IFERROR(..., "")` 中。
       - 防止单个 ID 缺失导致整个数组公式崩溃。
    
    5. 🚫 **禁止整列引用 (性能铁律)**：
    - 在 LET 动态数组公式中，严禁引用整列 (如 `A:A` 或 `A:C`)。
    - 原因：VSTACK 整列会导致数百万行空白数据进入内存，引发 #NUM! 错误。
    - ✅ **正确做法**：使用固定的大范围，例如 `$A$2:$C$5000` (假设数据不超过5000行)。
    - 或者使用 Excel 表格对象引用 (如果适用)。但对于外部文件，请默认使用 `$A$2:$DataEndRow` 的形式。
    
    【可用文件列表 (dfs keys)】
    {available_keys}
    
    【输出格式 (JSON)】
    请返回且仅返回一个 JSON 对象，不要包含 markdown 格式，包含三个字段：
    
    1. "python_code": string 
       - 可执行的 Python 代码。
       
    2. "excel_formula": string 
       - 【一步到位版】一个完整的 LET 动态数组公式。
       - 逻辑模板：定义源数据(外部引用) -> 获取唯一ID (去重+去空) -> IFERROR(XLOOKUP)获取属性 -> 计算 -> HSTACK输出。
       - 确保可以直接粘贴到 A1 单元格并溢出生成整张表。
       - ⚠️ **注意**：动态数组中不要引用整列 (如 A:A)，请使用 `$A$2:$C$5000` 形式。
    
    3. "column_formulas": dict 
       - 【分列填充版】Key是结果表的列名，Value是该列在 **第二行 (Row 2)** 的单格公式。
       - ⚠️ **Excel 最佳实践强制要求**：
         1. **假设布局**：默认 A 列为 ID。请根据任务逻辑，合理安排后续列的顺序（如 B, C, D...）。
         2. **链式引用 (关键)**：如果“金额”列依赖于“数量”列，**必须引用“数量”列的单元格 (如 D2)**，严禁把“数量”的计算逻辑（加减乘除/XLOOKUP）再写一遍。
         3. **外部数据源**：查找源数据时，必须使用外部文件格式 `'[文件名.xlsx]Sheet1'!范围`。
         4. **单行引用**：所有引用基于第 2 行（如 `$A2`），以便用户向下拖拽填充。
       
       - ✅ **正确示例** (假设 B列=姓名, C列=数量, D列=单价, E列=总价):
         {{
        "姓名": "=IFERROR(XLOOKUP($A2, '[花名册.xlsx]Sheet1'!$A:$A, '[花名册.xlsx]Sheet1'!$B:$B, \"\"), \"\")",
            "数量": "=IFERROR(XLOOKUP($A2, '[Q1.xlsx]Sheet1'!$A:$A, '[Q1.xlsx]Sheet1'!$B:$B, 0), 0) + IFERROR(XLOOKUP($A2, '[Q2.xlsx]Sheet1'!$A:$A, '[Q2.xlsx]Sheet1'!$B:$B, 0), 0)",
            "单价": "=IFERROR(XLOOKUP($A2, '[价格表.xlsx]Sheet1'!$A:$A, '[价格表.xlsx]Sheet1'!$C:$C, 0), 0)",
            "总价": "=C2 * D2"  // <--- 这里的 C2 和 D2 就是最佳实践，禁止重新计算 XLOOKUP
         }}
    """

    user_message = f"""
    【数据结构详情】
    {schema_str}
    
    【数据内容预览】
    {preview_str}

    【用户需求】
    {user_query}
    
    请严格按 JSON 格式输出：
    """
    # 3. 调用 AI
    content = call_deepseek_raw(system_prompt, user_message)

    # 🟢 解析 JSON
    try:
        # 清洗可能存在的 markdown 符号
        clean_content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_content)
        return result
        # 期望返回字典：
        # {
        #   'python_code': '...',
        #   'excel_formula': '...',
        #   'column_formulas': {'列A': '=...', '列B': '=...'}
        # }
    except json.JSONDecodeError:
        # 容错：如果 AI 还是死板地回了纯代码
        print("AI 返回了非 JSON 格式，尝试作为纯代码处理")
        code_match = re.search(r'```python(.*?)```', content, re.DOTALL)
        code = code_match.group(1).strip() if code_match else content.strip()
        return {
            "python_code": code,
            "excel_formula": "AI未能生成公式，请查看Python逻辑",
            "column_formulas": {} # 容错空字典
        }

def get_formula_suggestion(file_path: str, user_requirement: str):
    """
    智能生成：Python 负责执行，Excel 公式负责展示 (优化版：移除 row 占位符)
    """
    try:
        # 1. 读取 Excel 获取上下文
        df = pd.read_excel(file_path)

        # 获取真实数据维度
        real_row_count = len(df)
        data_end_row = real_row_count + 1 # 假设第一行是表头

        preview = df.head(5).to_markdown(index=False)

        # 2. 生成列映射
        col_mapping_list = []
        for i, col in enumerate(df.columns):
            letter = get_col_letter(i)
            col_mapping_list.append(f"【{letter}列】: {col}")

        column_mapping_str = " | ".join(col_mapping_list)

        # 3. 构建 Prompt (核心升级：要求生成标准 Excel 相对引用)
        system_prompt = f"""
        你是一个 Python Excel 自动化专家。
        
        【🎯 核心任务】
        你需要根据用户需求，判断是修改**表格结构**还是计算**单元格数值**，并生成对应的 JSON。
        
        【💻 1. Python 执行逻辑 (核心规则)】
        环境中有变量：`df` (Pandas DataFrame), `rows` (List[Dict]), `row` (当前行, 仅在 Formula 模式有效)。
        
        🔴 **模式 A: structure (结构修改 - 排序/筛选/删除)**
        - **定义**: 改变行数、顺序或删除列的操作。
        - **执行方式**: 后端使用 `exec()`，**必须使用赋值语句**更新 `df`。
        - **操作对象**: 直接操作 `df`。
        - **必遵规则**: 代码必须改变 `df` 的状态。
          - ✅ 正确: `df = df.sort_values(by='年龄', ascending=False)`
          - ✅ 正确: `df.drop(columns=['无用列'], inplace=True)`
          - ✅ 正确: `df = df[df['性别'] == '女']`
        
        🔵 **模式 B: formula (数值计算 - 新增列/覆盖列/指定列)**
        - **定义**: 对每一行进行数学计算、文本处理或逻辑判断。
        - **执行方式**: 后端使用 `eval()`，**仅支持 Python 表达式 (Expression)**。
        - **操作对象**: 使用 `row` (当前行字典) 或 `rows` (所有行列表)。
        - **🛑 致命错误避坑 (严禁使用赋值号)**:
          - 后端会自动处理写入操作，你只需要算出**值**。
          - ❌ **严重错误**: `row['年龄'] = row['年龄'] + 1` (这会导致 SyntaxError)
          - ✅ **完美正确**: `row['年龄'] + 1` (只返回计算结果)
        - **单元格汇总 (mode="cell")**:
          - ✅ 正确: `excel_ops.EXCEL_SUM([r['金额'] for r in rows])`
        
        【👀 2. Excel 展示公式 (用户体验优化)】
        - 无论哪种模式，都请生成一个 **标准 Excel 公式** 用于前端展示。
        - **核心原则**：假设你正在在一个**全新的空白辅助列**编写此公式。
        - **关于覆盖操作**：即使是对原列进行覆盖（如“年龄加1”），公式依然要引用原列（如 `=C2+1`）。这是为了展示计算逻辑，不用担心循环引用。
        - **必须**使用具体相对引用 (如 `A2`) 或 完整区域 (如 `A2:A{data_end_row}`)。
        
        【📝 3. Explanation (解释字段 - 必须包含位置信息)】
        - **explanation** 字段必须包含两部分信息：
          1. **逻辑**: 做了什么计算 (e.g. "性别为男则年龄+5")
          2. **去向**: 结果写到了哪里 (必须明确区分 "覆盖原列 [列名]" / "新建列 [列名]" / "写入指定列 [列号]")
        - **示例**:
          - "计算年龄+5，并**覆盖原‘年龄’列**。"
          - "计算总价，结果**写入新列‘F’**。"
        
        【📍 4. Target Position (智能定位规则)】
        - **情况 1：新建列** (例如 "计算总价")
          - `target_position`: `"总价"` (输出新列名)
        - **情况 2：覆盖原列** (例如 "把**年龄**加1", "结果写入**原列**")
          - `target_position`: `"年龄"` (❌ 严禁输出 "原列"，必须填入具体的**被覆盖列名**)
        - **情况 3：指定列号** (例如 "写入 **G** 列", "写入第 7 列")
          - `target_position`: `"G"` (直接输出列号字母)
        - **情况 4：结构修改 / 单元格汇总**
          - `target_position`: `"全表"` 或 具体单元格如 `"E13"`
        
        【JSON 输出模板】
        {{
            "action_type": "structure" | "formula",
            "python_expression": "string (注意: formula模式下严禁写 '=', 只能写表达式)", 
            "excel_formula": "string (用于前端展示的标准Excel公式)",
            "mode": "column" | "cell" | "structure", 
            "target_position": "string (写入的目标列名 或 列字母)",
            "explanation": "简短说明"
        }}
        """

        user_prompt = f"""
        【数据统计】
        - 数据结束行: {data_end_row} (引用整列数据时请用到此行号)
        
        【列结构映射 (请根据此确定 A/B/C 列)】:
        {column_mapping_str}

        【数据预览】:
        {preview}

        【用户需求】: 
        {user_requirement}
        """

        print(f"--- AI Request: {user_requirement} ---")
        content = call_deepseek_raw(system_prompt, user_prompt)

        # 清洗结果
        clean_content = content.replace("```json", "").replace("```", "").strip()
        print(f"--- AI Response: {clean_content} ---")

        try:
            result = json.loads(clean_content)
        except:
            # 简单的 JSON 容错处理
            start = clean_content.find('{')
            end = clean_content.rfind('}') + 1
            result = json.loads(clean_content[start:end])

        # 🟢 关键步骤：拼接公式到解释中
        formula_display = result.get('excel_formula', '')
        if formula_display and formula_display not in result.get('explanation', ''):
            # 优化显示的文本格式
            result['explanation'] = f"{result['explanation']} (参考公式: `{formula_display}`)"

        return result

    except Exception as e:
        print(f"AI Service Error: {repr(str(e))}")
        return {
            "action_type": "error",
            "explanation": f"AI分析失败: {str(e)}"
        }