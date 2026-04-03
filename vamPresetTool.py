import os
import json
import re
import zipfile
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import send2trash

class VamPresetManagerFinal:
    def __init__(self, root):
        self.root = root
        self.root.title("VaM 预设管理器 - 增强版")
        self.root.geometry("1100x700")

        # 配置文件
        self.config_file = os.path.join(os.path.dirname(__file__), "vam_preset_manager_config.json")
        self.load_config()

        # 数据
        self.person_path = tk.StringVar(value=self.config.get("person_path", ""))
        self.addon_path = tk.StringVar(value=self.config.get("addon_path", ""))
        self.presets = []          # (name, vap_path, fav_path, img_path, dependencies)
        self.card_frames = []
        self.check_vars = []

        self.setup_ui()

    def load_config(self):
        default = {"person_path": "", "addon_path": ""}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except:
                self.config = default
        else:
            self.config = default

    def save_config(self):
        self.config["person_path"] = self.person_path.get()
        self.config["addon_path"] = self.addon_path.get()
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    def setup_ui(self):
        # 顶部工具栏：两个路径选择
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # 预设目录行
        row1 = tk.Frame(top_frame)
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="预设目录 (Saves/Person):", width=20, anchor='e').pack(side=tk.LEFT)
        tk.Entry(row1, textvariable=self.person_path, width=60).pack(side=tk.LEFT, padx=5)
        tk.Button(row1, text="浏览", command=self.select_person_path).pack(side=tk.LEFT)
        tk.Button(row1, text="刷新", command=self.refresh_presets).pack(side=tk.LEFT, padx=5)

        # AddonPackages 目录行
        row2 = tk.Frame(top_frame)
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="AddonPackages 目录:", width=20, anchor='e').pack(side=tk.LEFT)
        tk.Entry(row2, textvariable=self.addon_path, width=60).pack(side=tk.LEFT, padx=5)
        tk.Button(row2, text="浏览", command=self.select_addon_path).pack(side=tk.LEFT)

        # 中间：可滚动网格
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
        tk.Label(bottom_frame, text="提示：单击卡片查看详情；双击依赖包可查看预览；删除文件直接进回收站", fg="gray").pack(side=tk.RIGHT)

    def select_person_path(self):
        path = filedialog.askdirectory(title="选择 VaM 的 Saves/Person 目录")
        if path:
            self.person_path.set(path)
            self.save_config()
            self.refresh_presets()

    def select_addon_path(self):
        path = filedialog.askdirectory(title="选择 VaM 的 AddonPackages 目录")
        if path:
            self.addon_path.set(path)
            self.save_config()

    # ---------- 预设文件名解析 ----------
    def parse_preset_name(self, name):
        """
        解析预设文件名（不含扩展名），尝试提取作者、名称、版本。
        支持格式：
          - Preset_作者.名称.版本
          - 作者.名称.版本
          - Preset_作者.名称
          - 作者.名称
          - 名称
        返回 (author, title, version) 可能为 None
        """
        # 去除可能的 Preset_ 前缀
        if name.startswith("Preset_"):
            name = name[7:]
        parts = name.split('.')
        if len(parts) >= 3:
            # 作者.名称.版本
            author = parts[0]
            title = '.'.join(parts[1:-1])  # 名称可能包含点
            version = parts[-1]
            return author, title, version
        elif len(parts) == 2:
            # 作者.名称
            author = parts[0]
            title = parts[1]
            return author, title, None
        else:
            # 只有名称
            return None, name, None

    # ---------- 依赖解析 ----------
    def extract_dependencies(self, vap_path):
        """解析 vap 文件，返回依赖的 VAR 包名列表（去重）"""
        deps = set()
        try:
            with open(vap_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"解析 {vap_path} 失败: {e}")
            return []

        pattern = re.compile(r'([a-zA-Z0-9_.]+\.\d+):/')
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

    # ---------- 增强的 VAR 包搜索 ----------
    def find_related_var_packages_enhanced(self, preset_name, dependencies):
        """
        根据预设文件名和依赖列表，在 AddonPackages 中查找相关 VAR 包。
        返回字典 {显示名称: 完整路径}
        搜索策略：
          1. 同名包：preset_name.var
          2. 依赖包：dependencies 中的每个包名 + '.var'
          3. 作者匹配：根据解析的作者名，匹配 AddonPackages 中以作者名开头的包
          4. 名称匹配：根据解析的名称，匹配包含该名称的包（模糊匹配）
        """
        if not self.addon_path.get() or not os.path.isdir(self.addon_path.get()):
            return {}

        addon_dir = self.addon_path.get()
        found = {}

        # 1. 同名包
        same_name = preset_name + ".var"
        same_path = os.path.join(addon_dir, same_name)
        if os.path.isfile(same_path):
            found[same_name] = same_path

        # 2. 依赖包
        for dep in dependencies:
            var_file = dep + ".var"
            dep_path = os.path.join(addon_dir, var_file)
            if os.path.isfile(dep_path):
                found[var_file] = dep_path

        # 3. 解析预设文件名获取作者和名称
        author, title, _ = self.parse_preset_name(preset_name)
        # 收集所有 VAR 文件名（不含扩展名）用于匹配
        all_vars = []
        for f in os.listdir(addon_dir):
            if f.endswith(".var"):
                all_vars.append(f[:-4])

        # 作者匹配：VAR 包名以 author. 开头
        if author:
            for var in all_vars:
                if var.startswith(author + '.'):
                    full_path = os.path.join(addon_dir, var + ".var")
                    if full_path not in found.values():
                        found[var + ".var"] = full_path

        # 名称匹配：VAR 包名包含 title（忽略大小写）
        if title:
            title_lower = title.lower()
            for var in all_vars:
                if title_lower in var.lower():
                    full_path = os.path.join(addon_dir, var + ".var")
                    if full_path not in found.values():
                        found[var + ".var"] = full_path

        return found

    # ---------- 删除到回收站 ----------
    def delete_to_recycle_bin(self, paths):
        for p in paths:
            if p and os.path.exists(p):
                try:
                    send2trash.send2trash(p)
                except Exception as e:
                    print(f"移入回收站失败 {p}: {e}")

    # ---------- 删除预设主逻辑 ----------
    def delete_selected(self):
        to_delete_idx = [i for i, var in enumerate(self.check_vars) if var.get() == 1]
        if not to_delete_idx:
            messagebox.showinfo("提示", "没有选中任何预设")
            return

        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {len(to_delete_idx)} 个预设吗？\n预设文件将被移入回收站。"):
            return

        # 收集预设信息
        presets_info = []
        for idx in to_delete_idx:
            card, name, vap_path, fav_path, img_path = self.card_frames[idx]
            presets_info.append((name, vap_path, fav_path, img_path))

        # 1. 删除预设文件
        preset_files = []
        for name, vap, fav, img in presets_info:
            preset_files.append(vap)
            if fav:
                preset_files.append(fav)
            if img:
                preset_files.append(img)
        self.delete_to_recycle_bin(preset_files)

        # 2. 收集关联的 VAR 包
        if self.addon_path.get() and os.path.isdir(self.addon_path.get()):
            all_var_packages = {}
            for name, vap, fav, img in presets_info:
                deps = self.extract_dependencies(vap)
                related = self.find_related_var_packages_enhanced(name, deps)
                all_var_packages.update(related)

            if all_var_packages:
                self.show_var_selection_dialog(all_var_packages)
            else:
                messagebox.showinfo("提示", "未在 AddonPackages 中找到与这些预设关联的 VAR 包。")
        else:
            messagebox.showwarning("警告", "未设置 AddonPackages 路径，无法扫描关联 VAR 包。")

        self.refresh_presets()
        messagebox.showinfo("完成", f"已删除 {len(to_delete_idx)} 个预设。")

    # ---------- VAR 包多选删除对话框 ----------
    def show_var_selection_dialog(self, var_packages):
        dialog = tk.Toplevel(self.root)
        dialog.title("选择要删除的 VAR 包")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="以下是与所选预设关联的 VAR 包，请勾选要删除的（默认全不选）：",
                 wraplength=580, justify=tk.LEFT).pack(pady=10, padx=10)

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

        var_vars = {}
        for name, path in var_packages.items():
            var = tk.IntVar()
            chk = tk.Checkbutton(scrollable, text=name, variable=var, anchor="w")
            chk.pack(fill=tk.X, padx=5, pady=2)
            var_vars[name] = (var, path)

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

        def confirm():
            to_delete = []
            for name, (var, path) in var_vars.items():
                if var.get() == 1:
                    to_delete.append(path)
            if to_delete:
                self.delete_to_recycle_bin(to_delete)
                messagebox.showinfo("完成", f"已将 {len(to_delete)} 个 VAR 包移入回收站。")
            dialog.destroy()

        tk.Button(dialog, text="确认删除选中的 VAR 包", command=confirm, bg="#ffaaaa").pack(pady=10)

    # ---------- VAR 包预览图提取 ----------
    def extract_preview_from_var(self, var_path):
        """
        从 VAR 包（ZIP）中查找 Saves/scene/ 目录下的第一张图片，返回临时文件路径（或 None）
        """
        if not var_path or not os.path.exists(var_path):
            return None
        try:
            with zipfile.ZipFile(var_path, 'r') as zf:
                # 查找 Saves/scene/ 下的图片文件
                image_exts = ('.png', '.jpg', '.jpeg')
                candidates = []
                for name in zf.namelist():
                    # 统一使用正斜杠比较
                    norm = name.replace('\\', '/')
                    if norm.startswith('Saves/scene/') and norm.lower().endswith(image_exts):
                        candidates.append(name)
                if candidates:
                    # 取第一个
                    img_data = zf.read(candidates[0])
                    # 写入临时文件
                    fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(candidates[0])[1])
                    with os.fdopen(fd, 'wb') as tmp:
                        tmp.write(img_data)
                    return temp_path
        except Exception as e:
            print(f"读取 VAR 包预览失败 {var_path}: {e}")
        return None

    def show_var_preview(self, var_name, var_path):
        """弹出窗口显示 VAR 包内的预览图"""
        preview_path = self.extract_preview_from_var(var_path)
        if not preview_path:
            messagebox.showinfo("提示", f"在 {var_name} 中未找到预览图 (Saves/scene/*.png/jpg/jpeg)")
            return

        win = tk.Toplevel(self.root)
        win.title(f"预览 - {var_name}")
        win.geometry("500x500")
        try:
            img = Image.open(preview_path)
            img.thumbnail((450, 450))
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(win, image=photo)
            label.image = photo
            label.pack(expand=True)
            tk.Button(win, text="关闭", command=win.destroy).pack(pady=5)
        except Exception as e:
            messagebox.showerror("错误", f"无法显示图片: {e}")
        finally:
            # 清理临时文件
            try:
                os.unlink(preview_path)
            except:
                pass

    # ---------- 详情窗口（支持双击依赖包查看预览）----------
    def show_detail(self, name, vap_path, fav_path, img_path, deps):
        detail_win = tk.Toplevel(self.root)
        detail_win.title(f"预设详情 - {name}")
        detail_win.geometry("750x550")
        detail_win.minsize(600, 450)

        main_frame = tk.Frame(detail_win)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧预览图
        left_frame = tk.Frame(main_frame)
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
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        tk.Label(right_frame, text="依赖的 VAR 包（双击可查看预览）:", font=("微软雅黑", 10, "bold")).pack(anchor=tk.W, pady=(0,5))

        list_frame = tk.Frame(right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Consolas", 9))
        for dep in deps:
            listbox.insert(tk.END, dep)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # 双击依赖项时，尝试在 AddonPackages 中查找并显示预览
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                dep_name = listbox.get(selection[0])
                # 构建可能的 VAR 包路径
                var_file = dep_name + ".var"
                addon_dir = self.addon_path.get()
                if addon_dir and os.path.isdir(addon_dir):
                    var_path = os.path.join(addon_dir, var_file)
                    if os.path.isfile(var_path):
                        self.show_var_preview(dep_name, var_path)
                    else:
                        messagebox.showinfo("提示", f"未找到 VAR 包: {var_file}\n请确认 AddonPackages 路径是否正确。")
                else:
                    messagebox.showwarning("警告", "未设置 AddonPackages 路径。")
        listbox.bind("<Double-Button-1>", on_double_click)

        # 底部关闭按钮和信息
        btn_frame = tk.Frame(detail_win)
        btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(btn_frame, text="关闭", command=detail_win.destroy, width=10).pack()
        path_label = tk.Label(btn_frame, text=f"文件: {os.path.basename(vap_path)}", fg="gray", font=("Arial", 8))
        path_label.pack(side=tk.LEFT, padx=10)

    # ---------- 网格加载 ----------
    def load_presets(self, path):
        presets = []
        if not os.path.isdir(path):
            return presets

        for f in os.listdir(path):
            if f.endswith(".vap"):
                base_name = f[:-4]
                vap_path = os.path.join(path, f)
                fav_path = os.path.join(path, base_name + ".vap.fav")
                if not os.path.exists(fav_path):
                    fav_path = None

                img_path = None
                for ext in [".png", ".jpg", ".jpeg"]:
                    test = os.path.join(path, base_name + ext)
                    if os.path.exists(test):
                        img_path = test
                        break

                deps = self.extract_dependencies(vap_path)
                presets.append((base_name, vap_path, fav_path, img_path, deps))
        return presets

    def refresh_presets(self):
        path = self.person_path.get()
        if not path or not os.path.isdir(path):
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            tk.Label(self.scrollable_frame, text="请先选择有效的预设目录", fg="gray").pack(pady=20)
            return

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.card_frames.clear()
        self.check_vars.clear()

        self.presets = self.load_presets(path)
        if not self.presets:
            tk.Label(self.scrollable_frame, text="该目录下没有找到 .vap 预设文件", fg="gray").pack(pady=20)
            return

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
        for idx, (name, vap_path, fav_path, img_path, deps) in enumerate(self.presets):
            card = tk.Frame(self.scrollable_frame, bd=2, relief=tk.RAISED, bg="white", padx=5, pady=5)
            card.grid(row=row, column=col, padx=padding, pady=padding, sticky="n")

            # 单击卡片显示详情
            card.bind("<Button-1>", lambda e, n=name, v=vap_path, f=fav_path, i=img_path, d=deps: self.show_detail(n, v, f, i, d))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, n=name, v=vap_path, f=fav_path, i=img_path, d=deps: self.show_detail(n, v, f, i, d))

            # 复选框
            var = tk.IntVar()
            chk = tk.Checkbutton(card, variable=var, bg="white")
            chk.place(x=5, y=5)
            self.check_vars.append(var)

            # 缩略图
            if img_path and os.path.exists(img_path):
                try:
                    pil_img = Image.open(img_path)
                    pil_img.thumbnail((150, 150))
                    photo = ImageTk.PhotoImage(pil_img)
                    img_label = tk.Label(card, image=photo, bg="white")
                    img_label.image = photo
                    img_label.pack(pady=(20, 5))
                    img_label.bind("<Button-1>", lambda e, n=name, v=vap_path, f=fav_path, i=img_path, d=deps: self.show_detail(n, v, f, i, d))
                except Exception:
                    tk.Label(card, text="[图片错误]", bg="white").pack(pady=(20, 5))
            else:
                tk.Label(card, text="无预览", bg="white", fg="gray").pack(pady=(20, 5))

            tk.Label(card, text=name, wraplength=160, bg="white", font=("微软雅黑", 9)).pack(pady=(0, 2))
            dep_count = len(deps)
            dep_text = f"依赖包: {dep_count}"
            tk.Label(card, text=dep_text, bg="white", fg="blue", font=("Arial", 8)).pack()

            if dep_count > 0:
                tooltip = "\n".join(deps[:5]) + ("\n..." if len(deps) > 5 else "")
                self.create_tooltip(card, tooltip)

            self.card_frames.append((card, name, vap_path, fav_path, img_path))

            col += 1
            if col >= columns:
                col = 0
                row += 1

    def create_tooltip(self, widget, text):
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

    def toggle_select_all(self):
        if not self.check_vars:
            return
        all_selected = all(v.get() == 1 for v in self.check_vars)
        new_state = 0 if all_selected else 1
        for var in self.check_vars:
            var.set(new_state)

if __name__ == "__main__":
    root = tk.Tk()
    app = VamPresetManagerFinal(root)
    root.mainloop()