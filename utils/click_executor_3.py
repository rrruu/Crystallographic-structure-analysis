import pyautogui
import pandas as pd
import numpy as np
import time
import sys
from pathlib import Path

# =========================================================
# 配置与路径 (自动对齐项目结构)
# =========================================================
ROOT = Path(__file__).resolve().parent
# 坐标文件位于 utils/results 目录下
BLUE_CSV = ROOT / "results" / "final_screen_coords_blue.csv"
PURPLE_CSV = ROOT / "results" / "final_screen_coords_purple.csv"

# 安全设置：鼠标移动到屏幕角落可紧急停止
pyautogui.FAILSAFE = True


def get_distance(p1, p2):
    """计算两点间的欧几里得距离"""
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def build_nearest_path(points_list):
    """
    使用最近邻算法规划路径：
    1. 选出 x 坐标最小的点作为起点。
    2. 依次寻找距离当前点最近的下一个点。
    """
    if not points_list:
        return []

    remaining = points_list.copy()
    start_idx = np.argmin([p[0] for p in remaining])
    current_pt = remaining.pop(start_idx)
    path = [current_pt]

    while remaining:
        distances = [get_distance(current_pt, p) for p in remaining]
        next_idx = np.argmin(distances)
        current_pt = remaining.pop(next_idx)
        path.append(current_pt)

    return path


def execute_task(part_name):
    """
    执行指定部分的点击任务
    :param part_name: "A", "B", "UPPER", 或 "LOWER"
    """
    # 1. 加载由 detector_transform.py 生成的实时屏幕坐标
    if not BLUE_CSV.exists() or not PURPLE_CSV.exists():
        print(f"错误：缺少必要的坐标文件，请检查 {ROOT}/results 目录")
        return

    df_b = pd.read_csv(BLUE_CSV)
    df_p = pd.read_csv(PURPLE_CSV)

    # 2. 提取紫色锚点映射
    p_map = {row['type']: (row['screen_x'], row['screen_y']) for _, row in df_p.iterrows()}
    ml = p_map['purple_ML']
    mr = p_map['purple_MR']
    tl, tr = p_map['purple_TL'], p_map['purple_TR']
    bl, br = p_map['purple_BL'], p_map['purple_BR']

    # 计算上下分界线
    split_y = (ml[1] + mr[1]) / 2

    # 3. 划分点集并规划路径
    upper_blue_list = df_b[df_b['screen_y'] < split_y][['screen_x', 'screen_y']].values.tolist()
    lower_blue_list = df_b[df_b['screen_y'] >= split_y][['screen_x', 'screen_y']].values.tolist()

    upper_blue_path = build_nearest_path(upper_blue_list)
    lower_blue_path = build_nearest_path(lower_blue_list)

    # 4. 根据参数确定执行序列
    sequence = []
    close_pt = None

    if part_name == "A":
        # 任务 A: 左中紫色点小切割
        nearest_upper = upper_blue_path[np.argmin([get_distance(ml, p) for p in upper_blue_path])]
        nearest_lower = lower_blue_path[np.argmin([get_distance(ml, p) for p in lower_blue_path])]
        sequence = [ml, nearest_upper, nearest_lower]
        close_pt = ml

    elif part_name == "B":
        # 任务 B: 右中紫色点小切割
        nearest_upper = upper_blue_path[np.argmin([get_distance(mr, p) for p in upper_blue_path])]
        nearest_lower = lower_blue_path[np.argmin([get_distance(mr, p) for p in lower_blue_path])]
        sequence = [mr, nearest_upper, nearest_lower]
        close_pt = mr

    elif part_name == "UPPER":
        # 上半部分主切割
        sequence = [tl, ml] + upper_blue_path + [mr, tr]
        close_pt = tl

    elif part_name == "LOWER":
        # 下半部分主切割
        sequence = [bl, ml] + lower_blue_path + [mr, br]
        close_pt = bl

    else:
        print(f"未知任务名称: {part_name}")
        return

    # 5. 执行点击序列
    print(f"\n>>> 脚本正在执行 [{part_name}] 路径点击...")
    for i, pt in enumerate(sequence):
        # 模拟点击，duration 增加稳定性
        pyautogui.click(pt[0], pt[1], duration=0.2)
        print(f"  步骤 {i + 1}: 点击坐标 ({pt[0]:.1f}, {pt[1]:.1f})")
        time.sleep(0.8)  # 留出 UI 响应时间

    # 双击初始点以闭合切割路径
    if close_pt:
        pyautogui.doubleClick(close_pt[0], close_pt[1])
        print(f">>> 路径已闭合于 {close_pt}")


if __name__ == "__main__":
    # 接收来自 run_test.py 的参数
    if len(sys.argv) > 1:
        target = sys.argv[1]
        execute_task(target)
    else:
        # 默认执行任务 A (用于单文件调试)
        print("未指定参数，默认运行任务 A")
        execute_task("A")