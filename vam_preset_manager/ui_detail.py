import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from .var_scanner import extract_preview_from_var, scan_var_packages
from .file_ops import cleanup_temp_file

def show_detail(parent, preset, addon_dir, extra_dirs=None):
    if extra_dirs is None:
        extra_dirs = []

    name = preset.name
    vap_path = preset.vap_path
    img_path = preset.img_path
    dependencies = preset.dependencies

    win = tk.Toplevel(parent)
    win.title(f"预设详情 - {name}")
    win.geometry("750x550")
    win.minsize(600, 450)

    # 预先扫描所有 VAR 包目录，构建包名->路径的映射
    all_dirs = []
    if addon_dir:
        all_dirs.append(addon_dir)
    all_dirs.extend(extra_dirs)
    var_map = scan_var_packages(all_dirs)  # {包名(无.var): 完整路径}

    # 左侧预览图
    left_frame = tk.Frame(win)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
    if img_path and os.path.exists(img_path):
        try:
            pil_img = Image.open(img_path)
            pil_img.thumbnail((400, 400), Image.LANCZOS)
            photo = ImageTk.PhotoImage(pil_img)
            img_label = tk.Label(left_frame, image=photo)
            img_label.image = photo
            img_label.pack(expand=True)
        except Exception:
            tk.Label(left_frame, text="图片加载失败", fg="red").pack(expand=True)
    else:
        tk.Label(left_frame, text="无预览图", fg="gray").pack(expand=True)

    # 右侧依赖列表
    right_frame = tk.Frame(win)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
    tk.Label(right_frame, text="依赖的 VAR 包（双击可查看预览）:",
             font=("微软雅黑", 10, "bold")).pack(anchor=tk.W, pady=(0,5))

    list_frame = tk.Frame(right_frame)
    list_frame.pack(fill=tk.BOTH, expand=True)
    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                         font=("Consolas", 9), exportselection=False)
    for dep in dependencies:
        listbox.insert(tk.END, dep)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    def on_double_click(event):
        selection = listbox.curselection()
        if not selection:
            return
        dep_name = listbox.get(selection[0])
        # 直接从预扫描的映射中获取路径
        if dep_name in var_map:
            var_path = var_map[dep_name]
        else:
            messagebox.showinfo("提示", f"未找到 VAR 包: {dep_name}.var")
            return

        preview_path = extract_preview_from_var(var_path)
        if not preview_path:
            messagebox.showinfo("提示", f"在 {dep_name} 中未找到预览图 (Saves/scene/*.png/jpg/jpeg)")
            return

        preview_win = tk.Toplevel(win)
        preview_win.title(f"预览 - {dep_name}")
        preview_win.geometry("500x500")
        try:
            img = Image.open(preview_path)
            img.thumbnail((450, 450))
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(preview_win, image=photo)
            label.image = photo
            label.pack(expand=True)
            tk.Button(preview_win, text="关闭", command=preview_win.destroy).pack(pady=5)
            def cleanup():
                cleanup_temp_file(preview_path)
                preview_win.destroy()
            preview_win.protocol("WM_DELETE_WINDOW", cleanup)
        except Exception as e:
            messagebox.showerror("错误", f"无法显示图片: {e}")
            cleanup_temp_file(preview_path)

    listbox.bind("<Double-Button-1>", on_double_click)

    bottom_frame = tk.Frame(win)
    bottom_frame.pack(fill=tk.X, pady=10)
    tk.Button(bottom_frame, text="关闭", command=win.destroy, width=10).pack()
    info_label = tk.Label(bottom_frame, text=f"文件: {os.path.basename(vap_path)}",
                          fg="gray", font=("Arial", 8))
    info_label.pack(side=tk.LEFT, padx=10)