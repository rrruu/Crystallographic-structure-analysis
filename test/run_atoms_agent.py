import os
import sys
import time
import pyautogui
import io
import traceback
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from config import API_KEY, BASE_URL, check_api_config

from gui_agents.s3.agents.grounding import OSWorldACI
from gui_agents.s3.agents.agent_s import AgentS3

# ================= 配置区域 =================
# API_KEY / BASE_URL 从环境变量或 .env 读取，请勿在此处硬编码
check_api_config()

# 1. 主模型配置 (负责规划任务)
engine_params = {
    "engine_type": "openai",
    "model": "gpt-4o",
    "api_key": API_KEY,
    "base_url": BASE_URL,
    "temperature": 0.0
}

# 2. 接地模型配置 (负责识别屏幕坐标)
# 使用 UI-TARS 模型
engine_params_for_grounding = {
    "engine_type": "openai",
    "model": "doubao-1-5-ui-tars-250428",
    "api_key": API_KEY,
    "base_url": BASE_URL,
    "grounding_width": 1920,
    "grounding_height": 1080
}

# ================= 初始化 Agent =================

print(">>> [1/3] 正在初始化视觉系统 (OSWorldACI)...")
grounding_agent = OSWorldACI(
    env=None,
    platform="windows",
    engine_params_for_generation=engine_params,
    engine_params_for_grounding=engine_params_for_grounding,
    width=1920,
    height=1080
)

print(">>> [2/3] 正在初始化主智能体 (AgentS3)...")

# 按顺序传参
agent = AgentS3(
    engine_params,  # 第1个参数：配置字典
    grounding_agent,  # 第2个参数：视觉对象
    platform="windows",
    max_trajectory_length=8,
    enable_reflection=True
)

# ================= 任务执行循环 =================

task_prompt = """
任务：在最大化窗口下，通过鼠标点击打开 ATOMS 数据文件。

步骤 1：环境清理
执行代码：pyautogui.hotkey('win', 'd')
(最小化所有干扰，确保桌面干净)。

步骤 2：启动软件
按下 Win 键，输入 "D:\\ATOMS65\\Eragon.exe" 并回车。
**强制等待 10 秒**（确保软件启动）。

步骤 3：最大化窗口
按下键盘上的 "Win" + "Up" (向上方向键)。
等待 2 秒。

步骤 4：点击 Import 按钮 
找到左侧的 "Import" 按钮并点击它。请尽量点击按钮的中心位置。
**等待 3 秒**，等待 "Import File" 弹窗出现。

任务结束。
"""

print(f">>> [3/3] Agent 就绪。请双手离开鼠标和键盘！")
print(">>> 任务开始...")

# 简单的循环执行逻辑
max_steps = 10  # 防止无限循环，最多执行10步
step_count = 0

try:
    while step_count < max_steps:
        step_count += 1
        print(f"\n>>> --- 第 {step_count} 步 ---")

        # 1. 获取屏幕截图
        screenshot = pyautogui.screenshot()
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        screenshot_bytes = buffered.getvalue()

        obs = {"screenshot": screenshot_bytes}

        # 2. 让 Agent 思考下一步 (Predict)
        # instruction 在第一步传入即可，后续步骤 Agent 会根据历史记忆自动判断
        # 但 AgentS3 的接口设计通常每次都需要传入 instruction
        info, action = agent.predict(instruction=task_prompt, observation=obs)

        print(f">>> Agent 思考结果: {action}")

        # 3. 如果没有动作，或者动作是空的，可能任务结束了
        if not action:
            print(">>> Agent 未返回动作，任务可能已完成或卡住。")
            break

        # 4. 执行动作代码
        # action 通常是一个包含字符串代码的列表，例如 ["pyautogui.click(100, 100)"]
        for act_code in action:
            print(f">>> 执行代码: {act_code}")
            # 安全检查：只允许执行 gui_agents 或 pyautogui 相关的代码，防止意外
            if "pyautogui" in act_code or "keyboard" in act_code or "mouse" in act_code:
                try:
                    exec(act_code)
                except Exception as exec_err:
                    print(f"!!! 代码执行失败: {exec_err}")
            elif "DONE" in act_code or "finish" in act_code.lower():
                print(">>> Agent 示意任务完成。")
                step_count = max_steps + 1  # 退出循环
            else:
                print(f"!!! 跳过未知命令: {act_code}")

        # 暂停一下，给界面反应时间
        time.sleep(2)

except Exception as e:
    print(f"\n>>> 发生严重错误: {e}")
    traceback.print_exc()

print("\n>>> 程序结束。")