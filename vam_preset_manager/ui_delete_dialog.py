import tkinter as tk
from tkinter import messagebox
from .file_ops import delete_to_recycle_bin

def show_var_selection_dialog(parent, var_packages: dict):
    """
    弹出对话框，显示所有关联的 VAR 包，让用户勾选要删除的（默认全不选）
    :param parent: 父窗口
    :param var_packages: 字典 {显示名称: 完整路径}
    :return: 用户确认删除的路径列表（如果取消则返回空列表）
    """
    if not var_packages:
        return []

    dialog = tk.Toplevel(parent)
    dialog.title("选择要删除的 VAR 包")
    dialog.geometry("600x500")
    dialog.transient(parent)
    dialog.grab_set()

    # 提示标签
    tk.Label(dialog, text="以下是与所选预设关联的 VAR 包，请勾选要删除的（默认全不选）：",
             wraplength=580, justify=tk.LEFT).pack(pady=10, padx=10)

    # 带滚动条的列表框框架
    frame = tk.Frame(dialog)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    canvas = tk.Canvas(frame, highlightthickness=0)
    scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollable = tk.Frame(canvas)
    scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas.create_window((0, 0), window=scrollable, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # 存储每个包的勾选状态 (IntVar)
    var_vars = {}  # {显示名称: (IntVar, 完整路径)}
    for name, path in var_packages.items():
        var = tk.IntVar()
        chk = tk.Checkbutton(scrollable, text=name, variable=var, anchor="w")
        chk.pack(fill=tk.X, padx=5, pady=2)
        var_vars[name] = (var, path)

    # 底部按钮框架
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(fill=tk.X, pady=10)

    def select_all():
        for var, _ in var_vars.values():
            var.set(1)

    def select_none():
        for var, _ in var_vars.values():
            var.set(0)

    tk.Button(btn_frame, text="全选", command=select_all, width=8).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="全不选", command=select_none, width=8).pack(side=tk.LEFT, padx=10)

    # 返回值存储
    selected_paths = []

    def confirm():
        nonlocal selected_paths
        selected_paths = [path for (var, path) in var_vars.values() if var.get() == 1]
        dialog.destroy()

    def cancel():
        nonlocal selected_paths
        selected_paths = []
        dialog.destroy()

    tk.Button(btn_frame, text="确认删除选中的 VAR 包", command=confirm, bg="#ffaaaa").pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="取消", command=cancel, width=8).pack(side=tk.LEFT, padx=10)

    # 等待对话框关闭
    dialog.wait_window()

    return selected_paths