import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

from .config import Config
from .models import Preset
from .parser import extract_dependencies
from .var_scanner import find_related_var_packages
from .file_ops import delete_to_recycle_bin
from .ui_detail import show_detail
from .ui_delete_dialog import show_var_selection_dialog


class MainWindow:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.presets = []          # 存储 Preset 对象列表
        self.card_frames = []      # 存储 (frame, preset)
        self.check_vars = []       # 存储每个预设的 IntVar
        self.setup_ui()
        self.refresh_presets()
        self.update_extra_dirs_label()

    def setup_ui(self):
        self.root.title("VaM 预设管理器")
        self.root.geometry("1100x700")

        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # 预设目录行
        row1 = tk.Frame(top_frame)
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="预设目录 (Saves/Person):", width=20, anchor='e').pack(side=tk.LEFT)
        self.person_entry = tk.Entry(row1, textvariable=self.config.get_var("person_path"), width=60)
        self.person_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(row1, text="浏览", command=self.select_person_path).pack(side=tk.LEFT)
        tk.Button(row1, text="刷新", command=self.refresh_presets).pack(side=tk.LEFT, padx=5)

        # AddonPackages 目录行
        row2 = tk.Frame(top_frame)
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="AddonPackages 目录:", width=20, anchor='e').pack(side=tk.LEFT)
        self.addon_entry = tk.Entry(row2, textvariable=self.config.get_var("addon_path"), width=60)
        self.addon_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(row2, text="浏览", command=self.select_addon_path).pack(side=tk.LEFT)

        # 额外 VAR 包目录行
        row3 = tk.Frame(top_frame)
        row3.pack(fill=tk.X, pady=2)
        tk.Label(row3, text="额外 VAR 包目录:", width=20, anchor='e').pack(side=tk.LEFT)
        self.extra_dirs_label = tk.Label(row3, text="", fg="blue", anchor='w')
        self.extra_dirs_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(row3, text="管理", command=self.manage_extra_dirs).pack(side=tk.LEFT)

        # 中间滚动区域
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 底部按钮
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(bottom_frame, text="删除选中预设", command=self.delete_selected, bg="#ffaaaa").pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="全选 / 反选", command=self.toggle_select_all).pack(side=tk.LEFT)
        tk.Label(bottom_frame, text="提示：单击卡片查看详情；双击依赖包可查看预览", fg="gray").pack(side=tk.RIGHT)

    def select_person_path(self):
        path = filedialog.askdirectory(title="选择 VaM 的 Saves/Person 目录")
        if path:
            self.config.set("person_path", path)
            self.refresh_presets()

    def select_addon_path(self):
        path = filedialog.askdirectory(title="选择 VaM 的 AddonPackages 目录")
        if path:
            self.config.set("addon_path", path)

    def refresh_presets(self):
        person_dir = self.config.get("person_path")
        if not person_dir or not os.path.isdir(person_dir):
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.card_frames.clear()
            self.check_vars.clear()
            tk.Label(self.scrollable_frame, text="请先选择有效的预设目录", fg="gray").pack(pady=20)
            return

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.card_frames.clear()
        self.check_vars.clear()
        self.presets.clear()

        # 扫描 .vap 文件
        preset_list = []
        for f in os.listdir(person_dir):
            if f.endswith(".vap"):
                base_name = f[:-4]
                vap_path = os.path.join(person_dir, f)
                fav_path = os.path.join(person_dir, base_name + ".vap.fav")
                if not os.path.exists(fav_path):
                    fav_path = None

                img_path = None
                for ext in [".png", ".jpg", ".jpeg"]:
                    test = os.path.join(person_dir, base_name + ext)
                    if os.path.exists(test):
                        img_path = test
                        break

                deps = extract_dependencies(vap_path)
                preset = Preset(base_name, vap_path, fav_path, img_path, deps)
                preset_list.append(preset)

        self.presets = preset_list

        if not self.presets:
            tk.Label(self.scrollable_frame, text="该目录下没有找到 .vap 预设文件", fg="gray").pack(pady=20)
            return

        # 网格参数
        card_width = 180
        padding = 10
        canvas_width = self.canvas.winfo_width()
        columns = max(1, (canvas_width // (card_width + padding)) if canvas_width > 0 else 4)

        def on_canvas_resize(event):
            nonlocal columns
            new_cols = max(1, event.width // (card_width + padding))
            if new_cols != columns:
                columns = new_cols
                self.refresh_presets()

        self.canvas.bind("<Configure>", on_canvas_resize)

        row = 0
        col = 0
        addon_dir = self.config.get("addon_path")
        extra_dirs = self.config.get_extra_dirs()

        for preset in self.presets:
            card = tk.Frame(self.scrollable_frame, bd=2, relief=tk.RAISED, bg="white", padx=5, pady=5)
            card.grid(row=row, column=col, padx=padding, pady=padding, sticky="n")

            # 单击卡片显示详情
            card.bind("<Button-1>", lambda e, p=preset: show_detail(self.root, p, addon_dir, extra_dirs))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, p=preset: show_detail(self.root, p, addon_dir, extra_dirs))

            # 复选框
            var = tk.IntVar()
            chk = tk.Checkbutton(card, variable=var, bg="white")
            chk.place(x=5, y=5)
            self.check_vars.append(var)

            # 缩略图
            if preset.img_path and os.path.exists(preset.img_path):
                try:
                    pil_img = Image.open(preset.img_path)
                    pil_img.thumbnail((150, 150))
                    photo = ImageTk.PhotoImage(pil_img)
                    img_label = tk.Label(card, image=photo, bg="white")
                    img_label.image = photo
                    img_label.pack(pady=(20, 5))
                    img_label.bind("<Button-1>", lambda e, p=preset: show_detail(self.root, p, addon_dir, extra_dirs))
                except Exception:
                    tk.Label(card, text="[图片错误]", bg="white").pack(pady=(20, 5))
            else:
                tk.Label(card, text="无预览", bg="white", fg="gray").pack(pady=(20, 5))

            # 预设名和依赖数量
            tk.Label(card, text=preset.name, wraplength=160, bg="white", font=("微软雅黑", 9)).pack(pady=(0, 2))
            dep_count = len(preset.dependencies)
            dep_text = f"依赖包: {dep_count}"
            tk.Label(card, text=dep_text, bg="white", fg="blue", font=("Arial", 8)).pack()

            if dep_count > 0:
                tooltip = "\n".join(preset.dependencies[:5]) + ("\n..." if dep_count > 5 else "")
                self._create_tooltip(card, tooltip)

            self.card_frames.append((card, preset))

            col += 1
            if col >= columns:
                col = 0
                row += 1

    def _create_tooltip(self, widget, text):
        def enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#ffffcc", relief=tk.SOLID, borderwidth=1)
            label.pack()
            widget.tooltip = tooltip

        def leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()

        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)

    def delete_selected(self):
        to_delete_idx = [i for i, var in enumerate(self.check_vars) if var.get() == 1]
        if not to_delete_idx:
            messagebox.showinfo("提示", "没有选中任何预设")
            return

        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {len(to_delete_idx)} 个预设吗？\n预设文件将被移入回收站。"):
            return

        # 收集预设文件路径
        preset_files = []
        selected_presets = []
        for idx in to_delete_idx:
            card, preset = self.card_frames[idx]
            if os.path.exists(preset.vap_path):
                preset_files.append(preset.vap_path)
            if preset.fav_path and os.path.exists(preset.fav_path):
                preset_files.append(preset.fav_path)
            if preset.img_path and os.path.exists(preset.img_path):
                preset_files.append(preset.img_path)
            selected_presets.append(preset)

        # 删除预设文件
        if preset_files:
            delete_to_recycle_bin(preset_files)

        # 询问并删除关联的 VAR 包
        addon_dir = self.config.get("addon_path")
        extra_dirs = self.config.get_extra_dirs()

        # 收集所有相关 VAR 包（去重）
        all_var_packages = {}
        for preset in selected_presets:
            related = find_related_var_packages(preset.name, preset.dependencies, addon_dir, extra_dirs)
            all_var_packages.update(related)

        if all_var_packages:
            to_delete_var_paths = show_var_selection_dialog(self.root, all_var_packages)
            if to_delete_var_paths:
                delete_to_recycle_bin(to_delete_var_paths)
                messagebox.showinfo("完成", f"已将 {len(to_delete_var_paths)} 个 VAR 包移入回收站。")
        else:
            if addon_dir or extra_dirs:
                messagebox.showinfo("提示", "未在 AddonPackages 或额外目录中找到与这些预设关联的 VAR 包。")
            else:
                messagebox.showwarning("警告", "未设置 AddonPackages 路径或额外目录，无法扫描关联 VAR 包。")

        # 刷新界面
        self.refresh_presets()
        messagebox.showinfo("完成", f"已删除 {len(to_delete_idx)} 个预设。")

    def toggle_select_all(self):
        if not self.check_vars:
            return
        all_selected = all(v.get() == 1 for v in self.check_vars)
        new_state = 0 if all_selected else 1
        for var in self.check_vars:
            var.set(new_state)

    def run(self):
        self.root.mainloop()

    def update_extra_dirs_label(self):
        dirs = self.config.get_extra_dirs()
        if dirs:
            self.extra_dirs_label.config(text="; ".join(dirs))
        else:
            self.extra_dirs_label.config(text="无")

    def manage_extra_dirs(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("管理额外 VAR 包目录")
        dialog.geometry("500x400")
        listbox = tk.Listbox(dialog)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for d in self.config.get_extra_dirs():
            listbox.insert(tk.END, d)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=5)

        def add():
            path = filedialog.askdirectory()
            if path:
                self.config.add_extra_dir(path)
                listbox.insert(tk.END, path)
                self.update_extra_dirs_label()

        def remove():
            sel = listbox.curselection()
            if sel:
                d = listbox.get(sel[0])
                self.config.remove_extra_dir(d)
                listbox.delete(sel[0])
                self.update_extra_dirs_label()

        tk.Button(btn_frame, text="添加目录", command=add).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="删除选中", command=remove).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="关闭", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)