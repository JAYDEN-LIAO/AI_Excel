# backend/excel_ops.py
import math
import re
from datetime import datetime

# ================= 工具函数 =================
def _to_float(val):
    """尝试将任何东西转为 float，失败返回 0"""
    try:
        return float(val)
    except:
        return 0.0

def _to_str(val):
    """转为字符串，None转为空"""
    return "" if val is None else str(val)

# ================= 数学运算 =================

def EXCEL_SUM(*args):
    """
    模拟 SUM。
    支持传入单个列表/Series (如 df['列']) 或 多个参数。
    """
    # 如果第一个参数是列表或 Series，直接求和该列表
    if len(args) == 1 and hasattr(args[0], '__iter__'):
        return sum(_to_float(x) for x in args[0])

    # 否则求和所有参数
    return sum(_to_float(x) for x in args)

def EXCEL_AVERAGE(*args):
    """模拟 AVERAGE"""
    values = []
    # 处理列表/Series输入
    if len(args) == 1 and hasattr(args[0], '__iter__'):
        values = [_to_float(x) for x in args[0]]
    else:
        values = [_to_float(x) for x in args]

    if not values:
        return 0
    return sum(values) / len(values)

def EXCEL_MULTIPLY(a, b):
    """安全乘法"""
    return _to_float(a) * _to_float(b)

def EXCEL_DIVIDE(a, b):
    """安全除法，防除零"""
    val_b = _to_float(b)
    if val_b == 0:
        return 0
    return _to_float(a) / val_b

def EXCEL_ROUND(number, digits):
    """四舍五入"""
    try:
        return round(_to_float(number), int(digits))
    except:
        return 0

# ================= 逻辑运算 =================

def EXCEL_IF(condition, true_val, false_val):
    """模拟 IF"""
    return true_val if condition else false_val

def EXCEL_AND(*args):
    """模拟 AND"""
    return all(args)

def EXCEL_OR(*args):
    """模拟 OR"""
    return any(args)

# ================= 文本处理 (最常用) =================

def EXCEL_LEFT(text, num_chars):
    """模拟 LEFT"""
    s = _to_str(text)
    n = int(_to_float(num_chars))
    return s[:n]

def EXCEL_RIGHT(text, num_chars):
    """模拟 RIGHT"""
    s = _to_str(text)
    n = int(_to_float(num_chars))
    return s[-n:] if n > 0 else ""

def EXCEL_MID(text, start_num, num_chars):
    """模拟 MID (注意 Excel 索引从1开始，Python从0开始)"""
    s = _to_str(text)
    start = int(_to_float(start_num)) - 1
    length = int(_to_float(num_chars))
    if start < 0: start = 0
    return s[start : start + length]

def EXCEL_LEN(text):
    """模拟 LEN"""
    return len(_to_str(text))

def EXCEL_CONCAT(*args):
    """模拟 CONCAT"""
    return "".join([_to_str(x) for x in args])

def EXCEL_FIND(find_text, within_text):
    """模拟 FIND (没找到返回 -1，而不是报错)"""
    try:
        return _to_str(within_text).find(_to_str(find_text)) + 1
    except:
        return -1

# ================= 高级模拟 =================

def EXCEL_VLOOKUP_DICT(lookup_value, lookup_dict, default=""):
    """
    Python 版 VLOOKUP 的简化。
    lookup_dict 应该是一个 {'张三': '经理', '李四': '专员'} 的字典。
    """
    return lookup_dict.get(lookup_value, default)