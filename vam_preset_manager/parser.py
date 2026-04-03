import json
import re

def extract_dependencies(vap_path: str) -> list:
    """
    从 vap 文件（JSON）中提取所有依赖的 VAR 包名（格式：作者.名称.版本）
    返回去重排序后的列表
    """
    deps = set()
    try:
        with open(vap_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"解析 {vap_path} 失败: {e}")
        return []

    # 匹配模式：任意非冒号字符序列，以 .数字 结尾，紧跟着冒号
    # 例如 "101.小恶魔.1:" 或 "Chaos.幼沅（学生&公主-双外观）.1:"
    pattern = re.compile(r'([^:]+\.\d+):/')

    def traverse(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                traverse(value)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)
        elif isinstance(obj, str):
            matches = pattern.findall(obj)
            for m in matches:
                deps.add(m)

    traverse(data)
    return sorted(list(deps))