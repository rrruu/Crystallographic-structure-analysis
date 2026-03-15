import os
import sys
import time
import pyautogui
import io
import traceback
import subprocess
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from config import API_KEY, BASE_URL, check_api_config

from gui_agents.s3.agents.grounding import OSWorldACI
from gui_agents.s3.agents.agent_s import AgentS3

# ================= 1. 基础配置 =================
# API_KEY / BASE_URL 从环境变量或 .env 读取
check_api_config()

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
GROUNDING_DIM = 1000

# ================= 2. 智能化任务目标模块 (完整保留) =================
SUB_TASKS = [
    {
        "goal": "启动位于 'D:\\ATOMS65\\Eragon.exe' 的 ATOMS 软件，并确保主窗口处于最大化状态。",
        "desc": "环境初始化"
    },
    {
        "goal": "在 ATOMS 软件中点击 'Open'，在弹出的对话框中，请先进入 'C:\\Users\\Lenovo\\Desktop\\演示5' 路径。确认正确进入该路径后，加载该路径下的数据文件 'ICSD_CollCode103903.str'，直到看到结构图显示在主窗口中。",
        "desc": "数据加载"
    },
    {
        "goal": "配置物理边界：在 'Input1' 菜单下打开 'Boundary' 选项，将模式更改为 'Sphere'，并将 'Radius' 数值修改为 45。完成后确认并返回主界面。",
        "desc": "边界配置"
    },
    {
        "goal": "空间取向调整：打开顶部 'Rotation' 菜单，选择 'Align Face or Vector'。重点：确保选中左侧的 'Vector' 单选按钮，并在 'Indices of vector (uvw)' 下方的三个输入框中依次填入 1、0、0。完成后点击右上方 OK 确认。",
        "desc": "取向设置"
    },
    {
        "goal": "视图效果优化：首先进入 'Input2' 菜单关闭 'Perspective' 视图选项。随后再次进入 'Input2' 打开 'Background Color' 窗口，将Background Color设置为白色（255 255 255）。操作路径：点击窗口右侧的 'Select Color...' 按钮，在弹出的调色板中直接点击选中255 255 255左侧单选按钮，点击 OK 返回后再在背景窗口点击 OK。",
        "desc": "背景与视觉优化"
    },
    {
        "goal": "保存结果：通过 'File' 菜单进入 'Save Graphics Window'，选择 '.BMP' 格式。在弹出的保存对话框中，请先进入 'D:\\code\\python\\AgentS_ATOMS\\utils\\bmp' 路径。确认正确进入该路径后，点击右下角的 '保存' 按钮完成保存图像结果。",
        "desc": "结果导出"
    }
]


# ================= 3. Agent 初始化函数 =================
def init_agent():
    """重新初始化 Agent 以重置轨迹记忆 (Trajectory)"""
    engine_params = {
        "engine_type": "openai",
        "model": "gpt-4o",
        "api_key": API_KEY,
        "base_url": BASE_URL,
        "temperature": 0.01
    }

    engine_params_for_grounding = {
        "engine_type": "openai",
        "model": "doubao-1-5-ui-tars-250428",
        "api_key": API_KEY,
        "base_url": BASE_URL,
        "grounding_width": GROUNDING_DIM,
        "grounding_height": GROUNDING_DIM,
        "temperature": 0.01
    }

    grounding_agent = OSWorldACI(
        env=None,
        platform="windows",
        engine_params_for_generation=engine_params,
        engine_params_for_grounding=engine_params_for_grounding,
        width=SCREEN_WIDTH,
        height=SCREEN_HEIGHT
    )

    return AgentS3(
        engine_params,
        grounding_agent,
        platform="windows",
        max_trajectory_length=8, # 保持较短记忆窗口，聚焦当前任务
        enable_reflection=True # 开启反思，确认操作是否生效
    )


# ================= 4. 运行后续处理脚本 (新增逻辑) =================
def run_post_processing():
    """按顺序运行 utils 文件夹下的脚本"""
    print("\n" + "=" * 50)
    print(">>> 所有 GUI 任务已完成，开始执行后续处理脚本...")
    print("=" * 50)

    # 定位 utils 文件夹路径
    current_dir = Path(__file__).resolve().parent
    utils_dir = current_dir / "utils"

    scripts = [
        utils_dir / "image_processing.py",
        utils_dir / "match.py"
    ]

    for script_path in scripts:
        if script_path.exists():
            print(f"\n[*] 正在运行: {script_path.name}...")
            try:
                # 使用当前环境的 python 解释器运行脚本
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=False,  # 设置为 False 直接在当前终端打印脚本输出
                    text=True,
                    check=True
                )
                print(f"[OK] {script_path.name} 执行成功。")
            except subprocess.CalledProcessError as e:
                print(f"[Error] {script_path.name} 执行失败，退出码: {e.returncode}")
                # 如果前一个脚本失败，通常后续匹配会报错，这里建议直接终止
                break
        else:
            print(f"[Skip] 未找到脚本: {script_path}")


# ================= 5. 主执行逻辑 =================
def run_automation():
    print(f">>> 智能 Agent 任务开始。屏幕分辨率: {SCREEN_WIDTH}x{SCREEN_HEIGHT}，缩放: 100%")

    for i, task in enumerate(SUB_TASKS):
        print(f"\n任务阶段 {i + 1}/{len(SUB_TASKS)}: [{task['desc']}]")
        print(f"目标: {task['goal']}")

        # 每个子任务开始前重置 Agent，清空历史干扰
        agent = init_agent()
        step_count = 0
        max_steps_per_task = 15  # 每个子任务给 15 步尝试空间
        task_done = False

        while step_count < max_steps_per_task and not task_done:
            step_count += 1
            print(f"  -> 尝试第 {step_count} 步...")
            try:
                # 1. 获取观察
                screenshot = pyautogui.screenshot()
                buffered = io.BytesIO()
                screenshot.save(buffered, format="PNG")
                obs = {"screenshot": buffered.getvalue()}

                # 2. 预测动作
                # 在智能化模式下，指令应包含“如果完成请输出 DONE”
                prompt = f"当前目标: {task['goal']}\n如果你认为目标已达成，请输出 'DONE'。"
                info, action = agent.predict(instruction=prompt, observation=obs)

                if not action:
                    print("     [警告] Agent 未返回有效动作，尝试刷新观察...")
                    time.sleep(2)
                    continue

                # 3. 执行动作
                for act_code in action:
                    print(f"     [执行] {act_code}")

                    # 检查是否达成 DONE 信号
                    if "DONE" in act_code or "DONE" in str(info):
                        print(f"     [成功] 阶段目标已完成！")
                        task_done = True
                        break

                    # 安全执行 pyautogui 相关的 GUI 代码
                    if any(kw in act_code for kw in ["pyautogui", "keyboard", "mouse", "time"]):
                        exec(act_code)
                time.sleep(2)
            except Exception as e:
                print(f"     [错误] 执行中发生异常: {e}")
                break

    # --- 核心改动：在所有 SUB_TASKS 完成后调用后续脚本 ---
    run_post_processing()
    print("\n>>> 流程全部结束。")


if __name__ == "__main__":
    try:
        run_automation()
    except KeyboardInterrupt:
        print("\n用户手动停止。")