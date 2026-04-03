import json
import os
import tkinter as tk

DEFAULT_CONFIG = {"person_path": "", "addon_path": "", "extra_addon_dirs": []}

class Config:
    def __init__(self, config_path):
        self.config_path = config_path
        self.data = self.load()
        self.vars = {}

    def load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保 extra_addon_dirs 字段存在
                if "extra_addon_dirs" not in data:
                    data["extra_addon_dirs"] = []
                return data
        return DEFAULT_CONFIG.copy()

    def save(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
        if key in self.vars:
            self.vars[key].set(value)

    def get_var(self, key):
        if key not in self.vars:
            var = tk.StringVar(value=self.get(key, ""))
            var.trace_add("write", lambda *args: self.set(key, var.get()))
            self.vars[key] = var
        return self.vars[key]

    def get_extra_dirs(self):
        return self.data.get("extra_addon_dirs", [])

    def add_extra_dir(self, dir_path):
        extra = self.data.get("extra_addon_dirs", [])
        if dir_path not in extra:
            extra.append(dir_path)
            self.data["extra_addon_dirs"] = extra
            self.save()

    def remove_extra_dir(self, dir_path):
        extra = self.data.get("extra_addon_dirs", [])
        if dir_path in extra:
            extra.remove(dir_path)
            self.data["extra_addon_dirs"] = extra
            self.save()