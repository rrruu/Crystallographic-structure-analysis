# -*- coding: utf-8 -*-
"""
本机路径配置示例。

使用方法：
  1. 复制本文件为 paths_user.py（同目录）
  2. 按你的电脑修改下面几个 Path
  3. paths_user.py 已在 .gitignore 中，勿提交到 Git

说明：
  - ATOMS_EXE：ATOMS 安装目录下的可执行文件（通常为 .exe）
  - PHASE1_OPEN_DIALOG_DIR：第一阶段「打开文件」对话框里要进入的文件夹
  - PHASE1_STR_FILENAME：该文件夹下的结构文件名（仅文件名）
  - PHASE2_STR_FILE：第二阶段要直接打开的结构文件；可为绝对路径，或相对项目根的路径，如：
        Path(r"D:\data\foo.str")
        Path("data/file/xyz/untitled.xyz")
"""
from pathlib import Path

ATOMS_EXE = Path(r"D:\ATOMS65\Eragon.exe")

PHASE1_OPEN_DIALOG_DIR = Path(r"D:\yan\agent\第一阶段\演示\演示8")

PHASE1_STR_FILENAME = "ICSD_CollCode103903.str"

PHASE2_STR_FILE = Path(r"D:\yan\agent\4\Pd2Ga-400-a-02.str")
