import os
import send2trash

def delete_to_recycle_bin(paths):
    """
    将文件列表移入回收站，自动跳过不存在的文件，
    并在失败时打印错误信息（不抛出异常）
    """
    for p in paths:
        if not p:
            continue
        # 规范化路径：统一分隔符，去除末尾斜杠
        norm_path = os.path.normpath(p)
        if not os.path.exists(norm_path):
            print(f"[跳过] 文件不存在: {norm_path}")
            continue
        try:
            send2trash.send2trash(norm_path)
        except Exception as e:
            # 如果还是失败，尝试直接删除（永久删除，不进回收站）
            print(f"[错误] 移入回收站失败 ({norm_path}): {e}")
            try:
                os.remove(norm_path)
                print(f"[回退] 已永久删除: {norm_path}")
            except Exception as rm_e:
                print(f"[严重] 无法删除文件: {rm_e}")

def create_temp_file(suffix=".png"):
    import tempfile
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path

def cleanup_temp_file(path):
    if path and os.path.exists(path):
        os.unlink(path)