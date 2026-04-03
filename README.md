# VaM Preset Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**VaM Preset Tool** 是一个专为 [Virt-A-Mate (VaM)](https://www.patreon.com/meshedvr) 设计的预设管理工具，帮助你高效整理、预览和删除角色预设（`.vap`）及其关联的 VAR 包。支持回收站安全删除、依赖解析、多目录扫描，让杂乱的内容库变得井井有条。

![界面预览](screenshot.png) <!-- 请替换为实际截图 -->

## ✨ 功能特性

- 📁 **预设网格展示** – 自动扫描 `Saves/Person` 目录，以卡片网格形式展示所有预设，包含缩略图、预设名、依赖数量。
- 🔍 **依赖解析** – 智能解析 `.vap` 文件中的服装、发型、变形等依赖，提取所需的 VAR 包名称（支持中文、特殊字符）。
- 🖼️ **一键详情** – 单击卡片放大预览图，右侧列出完整依赖列表；双击依赖项自动从 VAR 包中提取 `Saves/scene/` 下的预览图。
- 🗑️ **安全删除** – 删除预设时同时删除 `.vap`、`.fav` 和预览图片，**直接移入回收站**，可随时恢复。
- 📦 **关联 VAR 包管理** – 删除预设后自动扫描主目录（`AddonPackages`）和**用户自定义的额外目录**，列出同名包及依赖包，支持勾选后一并移入回收站。
- 🔌 **额外目录支持** – 对于使用符号链接（mklink）或分布在多个磁盘的 VAR 包，可通过“管理额外目录”添加任意文件夹，工具会递归扫描所有子目录。
- ⚙️ **配置持久化** – 预设目录、AddonPackages 路径、额外目录列表自动保存，下次启动无需重设。

## 🖥️ 系统要求

- Windows 7 / 8 / 10 / 11
- VaM 游戏本体（任意版本，预设文件位于 `Saves/Person`）
- 若从源码运行：Python 3.10 或更高版本

## 📦 安装与使用

1. 从 [Releases](/VaM-Preset-Tool/releases) 页面下载最新的 `VaMPresetTool.exe`。
2. 将 `VaMPresetTool.exe` 放置到任意文件夹（建议放在 VaM 根目录附近）。
3. 双击运行，按界面提示选择：
   - **预设目录**：VaM 游戏目录下的 `Saves/Person`
   - **AddonPackages 目录**：VaM 游戏目录下的 `AddonPackages`
   - （可选）额外 VAR 包目录：点击“管理”添加其他存放 `.var` 文件的文件夹。
4. 开始管理你的预设！


## 大爷！用的舒服的话赏口饭吃吧！
## 爱发电
https://www.ifdian.net/a/vamPresetTool

   
