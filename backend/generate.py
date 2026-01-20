import pandas as pd
import numpy as np
import os
import random

# ================= 配置路径 =================
base_path = r"C:\Users\廖志东\Desktop\test_data"

if not os.path.exists(base_path):
    os.makedirs(base_path)
    print(f"✅ 文件夹已创建: {base_path}")
else:
    print(f"📂 文件夹已存在: {base_path}")

# ================= 1. 准备基础数据 =================
# 生成 50 个工号 (E001 - E050)
emp_ids = [f"E{str(i).zfill(3)}" for i in range(1, 51)]

# 员工姓名与岗位库
surnames = ["赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈"]
names_last = ["伟", "芳", "娜", "敏", "静", "强", "磊", "军", "洋", "杰"]
departments = ["研发部", "市场部", "产品部", "运营部"]
levels = ["P4", "P5", "P6", "P7"]

emp_names = [random.choice(surnames) + random.choice(names_last) for _ in range(50)]
emp_depts = [random.choice(departments) for _ in range(50)]
emp_levels = [random.choice(levels) for _ in range(50)]

# ================= 2. 生成 DataFrame =================

# --- 表1: 一季度考核表 (包含Q1项目完成数) ---
df_q1 = pd.DataFrame({
    "工号": emp_ids,
    "Q1完成项目数": np.random.randint(5, 30, 50), # 每个人完成5-30个项目
    "直属主管": [random.choice(["主管A", "主管B", "主管C"]) for _ in range(50)]
})

# --- 表2: 二季度考核表 (包含Q2项目数 和 质量扣分项) ---
# 对应之前的“下半年数据”，包含“退货”(这里是Bug数)
df_q2 = pd.DataFrame({
    "工号": emp_ids,
    "Q2完成项目数": np.random.randint(5, 35, 50),
    "Bug或投诉量": np.random.randint(0, 5, 50) # 扣分项，大部分人比较少
})

# --- 表3: 薪酬职级表 (包含单价信息) ---
# 对应之前的“产品价格表”
df_salary = pd.DataFrame({
    "工号": emp_ids,
    "姓名": emp_names,
    "部门": emp_depts,
    "职级": emp_levels,
    "项目提成单价": [round(random.uniform(200.0, 1000.0), 0) for _ in range(50)], # 每个项目的奖金
    "基本工资": [random.randint(8000, 25000) for _ in range(50)]
})

# --- 表4: 考勤记录表 (异构数据，用于复杂逻辑测试) ---
# 对应之前的“库存预警表”
df_attendance = pd.DataFrame({
    "工号": emp_ids,
    "办公地点": [random.choice(["总部大楼", "科技园", "居家办公"]) for _ in range(50)],
    "迟到次数": np.random.randint(0, 10, 50),
    "年假剩余": np.random.randint(0, 15, 50)
})

# ================= 3. 保存文件 =================

files = {
    "一季度考核表.xlsx": df_q1,
    "二季度考核表.xlsx": df_q2,
    "薪酬职级表.xlsx": df_salary,
    "考勤记录表.xlsx": df_attendance
}

print("\n🚀 开始生成绩效考核数据...")
for filename, df in files.items():
    file_path = os.path.join(base_path, filename)
    try:
        df.to_excel(file_path, index=False)
        print(f"✅ 成功生成: {filename}")
    except Exception as e:
        print(f"❌ 生成失败 {filename}: {e}")

print(f"\n✨ 所有文件已生成至: {base_path}")