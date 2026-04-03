import tkinter as tk
import os
from vam_preset_manager.config import Config
from vam_preset_manager.ui_main import MainWindow

def main():
    root = tk.Tk()
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    config = Config(config_path)
    app = MainWindow(root, config)
    app.run()

if __name__ == "__main__":
    main()