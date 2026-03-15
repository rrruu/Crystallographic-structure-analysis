import pyautogui
import cv2
import numpy as np
import pandas as pd
from pathlib import Path

# =========================================================
# 基础参数配置 (基于 1.png 的原始属性)
# =========================================================
# SRC_IMAGE_W = 1718  # 原始图片 1.png 的宽度
# SRC_IMAGE_H = 997  # 原始图片 1.png 的高度

# 路径配置
ROOT = Path(__file__).resolve().parent

# 修改此处：自动获取尺寸
SRC_IMAGE_PATH = ROOT / "images" / "origin" / "1.png"
if SRC_IMAGE_PATH.exists():
    img_temp = cv2.imread(str(SRC_IMAGE_PATH))
    SRC_IMAGE_H, SRC_IMAGE_W = img_temp.shape[:2] # 自动获取
else:
    SRC_IMAGE_W, SRC_IMAGE_H = 1718, 997 # 兜底值

IN_BLUE_CSV = ROOT / "results" / "blue_points_in_source_2.csv"
OUT_BLUE_SCREEN_CSV = ROOT / "results" / "final_screen_coords_blue.csv"
OUT_PURPLE_SCREEN_CSV = ROOT / "results" / "final_screen_coords_purple.csv"


def get_atoms_realtime_workspace():
    """
    第一部分：实时探测屏幕上 ATOMS 软件的白色工作区并确定 6 个锚点坐标
    """
    print("正在扫描屏幕，请确保 ATOMS 软件已打开并处于最大化状态...")

    # 1. 截取全屏并处理
    screenshot = pyautogui.screenshot()
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. 识别白色背景区域 (阈值 250)
    _, mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print("错误：未在屏幕上检测到白色工作区。")
        return None

    # 3. 定位最大矩形 (ATOMS 画布)
    main_canvas = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(main_canvas)

    # 4. 确定 6 个紫色锚点 (基于当前屏幕实际位置)
    margin = 5
    anchors_data = [
        {"type": "purple_TL", "screen_x": x + margin, "screen_y": y + margin},
        {"type": "purple_TR", "screen_x": x + w - margin, "screen_y": y + margin},
        {"type": "purple_ML", "screen_x": x + margin, "screen_y": y + h // 2},
        {"type": "purple_MR", "screen_x": x + w - margin, "screen_y": y + h // 2},
        {"type": "purple_BL", "screen_x": x + margin, "screen_y": y + h - margin},
        {"type": "purple_BR", "screen_x": x + w - margin, "screen_y": y + h - margin}
    ]

    return (x, y, w, h), anchors_data


def run_integration():
    # 执行实时检测
    detect_res = get_atoms_realtime_workspace()
    if not detect_res: return

    (x_offset, y_offset, w_screen, h_screen), anchors = detect_res

    # --- 打印实时检测信息供验证 ---
    print("\n" + "=" * 50)
    print("             ATOMS 实时环境探测结果")
    print("=" * 50)
    print(f"工作区起点: ({x_offset}, {y_offset})")
    print(f"工作区尺寸: {w_screen} x {h_screen}")
    print("-" * 50)
    for a in anchors:
        print(f"  - {a['type']}: ({a['screen_x']}, {a['screen_y']})")
    print("=" * 50)

    # --- 第二部分：坐标转换与导出 ---
    # 1. 导出紫色锚点 CSV
    df_purple = pd.DataFrame(anchors)
    df_purple.to_csv(OUT_PURPLE_SCREEN_CSV, index=False)
    print(f"已生成紫色锚点坐标: {OUT_PURPLE_SCREEN_CSV.name}")

    # 2. 转换蓝色点 CSV
    if not IN_BLUE_CSV.exists():
        print(f"跳过蓝色点转换：找不到输入文件 {IN_BLUE_CSV}")
        return

    df_blue_in = pd.read_csv(IN_BLUE_CSV)

    # 计算实时缩放倍率
    r_w = w_screen / SRC_IMAGE_W
    r_h = h_screen / SRC_IMAGE_H

    print(f"实时计算倍率: 宽 x{r_w:.4f}, 高 x{r_h:.4f}")

    # 线性映射变换
    df_blue_out = pd.DataFrame()
    df_blue_out['screen_x'] = df_blue_in['src_x'] * r_w + x_offset
    df_blue_out['screen_y'] = df_blue_in['src_y'] * r_h + y_offset

    # 导出蓝色点屏幕坐标
    df_blue_out.to_csv(OUT_BLUE_SCREEN_CSV, index=False)
    print(f"已生成蓝色点屏幕坐标: {OUT_BLUE_SCREEN_CSV.name}")
    print(f"总计转换蓝色点数: {len(df_blue_out)}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    run_integration()