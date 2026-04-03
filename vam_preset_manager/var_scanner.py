import os
import zipfile
import tempfile
from typing import Dict, List, Optional

def scan_var_packages(directories: List[str]) -> Dict[str, str]:
    """
    扫描一个或多个目录（包括子目录）中的所有 .var 文件
    返回 {包名(不含.var): 完整路径}
    """
    result = {}
    for base_dir in directories:
        if not base_dir or not os.path.isdir(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir, followlinks=False):
            for f in files:
                if f.endswith(".var"):
                    name = f[:-4]
                    full_path = os.path.join(root, f)
                    if name not in result:  # 同名包保留第一个
                        result[name] = full_path
    return result

def find_related_var_packages(preset_name: str, dependencies: List[str], addon_dir: str, extra_dirs: List[str]) -> Dict[str, str]:
    """
    根据依赖列表和预设同名包查找 VAR 包（精确匹配）
    扫描主目录 addon_dir 和额外目录 extra_dirs
    返回字典 {显示名称: 完整路径}
    """
    all_dirs = []
    if addon_dir:
        all_dirs.append(addon_dir)
    all_dirs.extend(extra_dirs)
    all_vars = scan_var_packages(all_dirs)
    if not all_vars:
        return {}

    found = {}
    if preset_name in all_vars:
        found[preset_name + ".var"] = all_vars[preset_name]
    for dep in dependencies:
        if dep in all_vars:
            found[dep + ".var"] = all_vars[dep]
    return found

def extract_preview_from_var(var_path: str) -> Optional[str]:
    """从 VAR 包中提取预览图，返回临时文件路径"""
    if not var_path or not os.path.exists(var_path):
        return None
    image_exts = ('.png', '.jpg', '.jpeg')
    try:
        with zipfile.ZipFile(var_path, 'r') as zf:
            candidates = []
            for name in zf.namelist():
                norm = name.replace('\\', '/')
                if norm.startswith('Saves/scene/') and norm.lower().endswith(image_exts):
                    candidates.append(name)
            if not candidates:
                return None
            img_name = candidates[0]
            img_data = zf.read(img_name)
            ext = os.path.splitext(img_name)[1]
            if not ext:
                ext = '.png'
            fd, temp_path = tempfile.mkstemp(suffix=ext)
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(img_data)
            return temp_path
    except Exception as e:
        print(f"提取预览图失败 {var_path}: {e}")
        return None