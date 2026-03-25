# -*- coding: utf-8 -*-
"""
项目路径与「给 Agent 看的」路径文案统一入口。

- 凡依赖本机安装位置的路径（ATOMS 可执行文件、数据目录等）：在 paths_user.py 中配置
  （从 paths_user.example.py 复制一份并重命名）。
- 凡位于仓库内的目录（utils/bmp、data/file 等）：默认相对 PROJECT_ROOT，克隆到任意盘符即可用。
"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# data 子目录（相对项目根，一般不必改）
DATA_FILE_ROOT = PROJECT_ROOT / "data" / "file"
UTILS_BMP_DIR = PROJECT_ROOT / "utils" / "bmp"
DATA_XYZ_DIR = DATA_FILE_ROOT / "xyz"
DATA_XLSX_DIR = DATA_FILE_ROOT / "xlsx"
DATA_CSV_DIR = DATA_FILE_ROOT / "csv"
DATA_TXT_DIR = DATA_FILE_ROOT / "txt"

# 第二阶段里用到的文件名（与 data 脚本、Agent 文案一致）
DATA_TRANSACTION_XLSX = "Data transation.xlsx"
DATA_TRANSACTION_TXT = "Data transation.txt"
PROCESSED_CSV = "processed_data.csv"

# 第二阶段旋转角度（写进 Agent 任务文案）
PHASE2_ROTATION_ANGLE = 90

try:
    from paths_user import (
        ATOMS_EXE,
        PHASE1_OPEN_DIALOG_DIR,
        PHASE1_STR_FILENAME,
        PHASE2_STR_FILE,
    )
except ImportError:
    # 未创建 paths_user.py 时的占位：请复制 paths_user.example.py 为 paths_user.py 并修改
    ATOMS_EXE = PROJECT_ROOT / "tools" / "ATOMS.exe"
    PHASE1_OPEN_DIALOG_DIR = PROJECT_ROOT / "data" / "phase1_input"
    PHASE1_STR_FILENAME = "example.str"
    PHASE2_STR_FILE = PROJECT_ROOT / "data" / "file" / "xyz" / "untitled.xyz"


def resolve_user_path(p: Path) -> Path:
    """若 p 为相对路径，则相对 PROJECT_ROOT 解析。"""
    if p.is_absolute():
        return p.resolve()
    return (PROJECT_ROOT / p).resolve()


def path_for_agent(p: Path) -> str:
    """Windows 文件对话框 / 资源管理器里常见的反斜杠路径字符串。"""
    return str(resolve_user_path(p)).replace("/", "\\")


def build_phase1_subtasks_stage_1():
    """第一阶段：SUB_TASKS_STAGE_1（除角度相关外）"""
    exe = path_for_agent(ATOMS_EXE)
    folder = path_for_agent(PHASE1_OPEN_DIALOG_DIR)
    bmp_dir = path_for_agent(UTILS_BMP_DIR)
    return [
        {
            "goal": f"启动位于 '{exe}' 的 ATOMS 软件，并确保主窗口处于最大化状态。",
            "desc": "环境初始化",
        },
        {
            "goal": f"在 ATOMS 软件中点击 'Open'。在弹出的对话框地址栏输入 '{folder}' 并回车。确认正确进入该路径后，加载文件 '{PHASE1_STR_FILENAME}'，直到结构图显示在主窗口中。",
            "desc": "数据加载",
        },
        {
            "goal": "配置物理边界：在 'Input1' 菜单下打开 'Boundary' 选项，将模式更改为 'Sphere'，并将 'Radius' 数值修改为 45。完成后确认并返回主界面。",
            "desc": "边界配置",
        },
        {
            "goal": "空间取向调整：打开顶部 'Rotation' 菜单，选择 'Align Face or Vector'。重点：确保选中左侧的 'Vector' 单选按钮，并在 'Indices of vector (uvw)' 下方的三个输入框中依次填入 1、0、0。完成后点击右上方 OK 确认。",
            "desc": "取向设置",
        },
        {
            "goal": "视图效果优化：首先进入 'Input2' 菜单关闭 'Perspective' 视图选项。随后再次进入 'Input2' 打开 'Background Color' 窗口，将Background Color设置为白色（255 255 255）。操作路径：点击窗口右侧的 'Select Color...' 按钮，在弹出的调色板中直接点击选中255 255 255左侧单选按钮，点击 OK 返回后再在背景窗口点击 OK。",
            "desc": "背景与视觉优化",
        },
        {
            "goal": f"保存结果：通过 'File' -> 'Save Graphics Window' 选 '.BMP' 格式。在保存对话框地址栏输入 '{bmp_dir}' 并回车。确认正确进入该路径后，点击右下角 '保存' 按钮。",
            "desc": "结果导出",
        },
    ]


def build_phase2_subtasks_stage_1():
    p = path_for_agent(resolve_user_path(PHASE2_STR_FILE))
    return [
        {
            "goal": f"启动位于 '{p}' 的 文件。",
            "desc": "数据加载",
        }
    ]


def build_phase2_subtasks_stage_2():
    xyz_dir = path_for_agent(DATA_XYZ_DIR)
    return [
        {
            "goal": f"双击界面左侧的角度输入框。在输入框内填入数字 {PHASE2_ROTATION_ANGLE} 。完成后，依次点击：1. 第二排右侧的向上箭头按钮（↑）；2. 第三排右侧的向左箭头按钮（←，即指向左侧但位于右边的按钮）。",
            "desc": "旋转修正",
        },
        {
            "goal": f"保存结果：通过 'File' -> 'Export' ，点击File format旁边的下拉框，在下拉框中选择'.xyz'格式。之后点击OK按钮保存。在保存对话框地址栏输入 '{xyz_dir}' 并回车。确认正确进入该路径后，点击右下角 '保存' 按钮。",
            "desc": "结果导出",
        },
    ]


def build_phase2_subtasks_stage_3():
    xlsx_path = path_for_agent(DATA_XLSX_DIR / DATA_TRANSACTION_XLSX)
    csv_dir = path_for_agent(DATA_CSV_DIR)
    txt_path = path_for_agent(DATA_TXT_DIR / DATA_TRANSACTION_TXT)
    return [
        {
            "goal": f"启动位于 '{xlsx_path}' 的 Data transation.xlsx 文件。",
            "desc": "打开xlsx文件",
        },
        {
            "goal": f"在 '文件' 菜单下打开 '打开' 选项，在弹出的对话框地址栏输入 '{csv_dir}' 地址并回车。确认正确进入该路径后，选择文件类型为 '所有文件' ，打开文件 '{PROCESSED_CSV}' 。",
            "desc": "在xlsx文件中打开csv文件",
        },
        {
            "goal": f"在 '{PROCESSED_CSV}' 文件中，全选并复制表格中的所有内容。",
            "desc": "复制csv文件中全部数据",
        },
        {
            "goal": f"打开 '{txt_path}'，在文件末尾的新一行中粘贴刚刚在'{PROCESSED_CSV}' 文件中复制的内容。",
            "desc": "将数据追加到目标文本文件",
        },
        {
            "goal": f"保存并关闭 '{DATA_TRANSACTION_TXT}'。关闭 '{DATA_TRANSACTION_XLSX}' 和 '{PROCESSED_CSV}' 窗口，且不对 '{DATA_TRANSACTION_XLSX}' 和 '{PROCESSED_CSV}' 进行保存。",
            "desc": "保存并清理工作环境",
        },
    ]
