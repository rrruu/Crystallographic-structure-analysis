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
    "temperature": 0.01
}

# 2. 接地模型配置 (负责识别屏幕坐标)
# 修复说明：UI-TARS 模型输出坐标范围通常是 [0-1000]，
# 这里必须设置为 1000，Agent 才会自动将其映射到屏幕的 1920x1080
engine_params_for_grounding = {
    "engine_type": "openai",
    "model": "doubao-1-5-ui-tars-250428",
    "api_key": API_KEY,
    "base_url": BASE_URL,
    "grounding_width": 1000,   # 修改：从 1920 改为 1000
    "grounding_height": 1000,   # 修改：从 1080 改为 1000
    "temperature": 0.01
}

# ================= 初始化 Agent =================

print(">>> [1/3] 正在初始化视觉系统 (OSWorldACI)...")
# 注意：这里初始化的 width/height 依然要是屏幕真实分辨率 (1920/1080)
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
全局指令：请严格按顺序执行以下步骤。

=== 步骤 1：清空桌面 ===
目标：最小化所有窗口，显示桌面。
执行指令：请按下快捷键 Win + D。
（等待 1 秒，确保桌面已显示）

=== 步骤 2：打开运行输入 ===
目标：准备输入程序路径。
执行指令：请按下 Win 键。
（等待 0.5 秒，等待开始菜单输入框出现）

=== 步骤 3：启动 ATOMS 程序 ===
目标：运行 ATOMS 软件。
执行指令：在输入框中输入以下路径：
D:\ATOMS65\Eragon.exe
然后按下 Enter 键确认。
（等待 3 秒，等待 ATOMS 程序启动）

=== 步骤 4：最大化 ATOMS 窗口 ===
目标：将 ATOMS 窗口最大化。
执行指令：请按下快捷键 "Win" + "up"(向上方向键) 将主窗口最大化。
（等待 1 秒，确保窗口已最大化）

=== 步骤 5：进入文件打开界面 ===
目标：在 ATOMS 启动界面点击 “Open”。
执行指令：在 ATOMS 启动界面中，请识别左侧的 “Open” 按钮并点击它。
（等待 2 秒，等待 “Open an ATOMS Data File” 窗口弹出）

=== 步骤 6：输入文件名 ===
目标：选择指定结构文件。
执行指令：在 “Open an ATOMS Data File” 窗口中，单击文件名输入框，
输入文件名：
ICSD_CollCode103903.str

=== 步骤 7：确认打开文件 ===
目标：加载结构文件。
执行指令：请按下 Enter 键确认打开文件。
（等待 3 秒，等待 “ATOMS [ICSD_CollCode103903.str]” 主窗口显示）

=== 步骤 8：打开一级菜单 ===
目标：点击顶部菜单 "Input1"。
执行指令：请识别屏幕顶部菜单栏中的 "Input1" 文字并点击它。
（等待 1 秒，等待下拉菜单弹出）

=== 步骤 9：选择二级菜单 ===
目标：点击下拉菜单中的 "Boundary"。
执行指令：请识别下拉菜单中的 "Boundary..." 选项并点击它。
（等待 2 秒，等待新窗口弹出）

=== 步骤 10：点击更改选项 ===
目标：点击 "Change Boundary Option..." 按钮。
执行指令：请在弹出的窗口中，识别并点击 "Change Boundary Option..." 按钮。
（等待 2 秒，等待选项窗口弹出）

=== 步骤 11：选择 Sphere 模式 ===
目标：选中 "Sphere" 单选框。
执行指令：请在 "Boundary Option" 窗口左侧，识别 "Sphere" 文字或其旁边的单选按钮并点击它。

=== 步骤 12：确认模式选择 ===
目标：点击 "Boundary Option" 窗口的 OK 按钮。
执行指令：请识别 "Boundary Option" 窗口右上角的 "OK" 按钮并点击它。
（等待 2 秒，等待 Sphere 窗口弹出）

=== 步骤 13：输入半径数值 ===
目标：修改 Radius 数值为 45。
执行指令：请识别 "Radius of sphere (A):" 文字，找到其右侧的输入框。双击该输入框的中心位置（以选中已有文字），然后输入数字 "45"。
（说明：请确保输入框中的内容被替换为 45）

=== 步骤 14：确认半径设置 ===
目标：点击 "Boundary - Sphere" 窗口的 OK 按钮。
执行指令：请识别 "Boundary - Sphere" 窗口右上角的 "OK" 按钮并点击它。
（等待 2 秒，回到主界面）

=== 步骤 15：打开 Rotation 菜单 ===
目标：点击顶部菜单 "Rotation"。
执行指令：请识别屏幕顶部菜单栏中的 "Rotation" 文字并点击它。
（等待 1 秒，等待下拉菜单弹出）

=== 步骤 16：选择 Align 选项 ===
目标：点击下拉菜单中的 "Align Face or Vector"。
执行指令：请识别下拉菜单中的 "Align Face or Vector..." 选项并点击它。
（等待 2 秒，等待新窗口弹出）

=== 步骤 17：选择 Vector 模式 ===
目标：选中 "Vector" 单选框。
执行指令：请在 "Align Face or Vector" 窗口左侧，识别 "Vector" 文字或其旁边的单选按钮并点击它。

=== 步骤 18：输入向量值 U ===
目标：设置第一个输入框为 1。
执行指令：找到 "Indices of vector (uvw)" 文字下方的**第一个**输入框。双击该输入框中心，输入数字 "1"。

=== 步骤 19：输入向量值 V ===
目标：设置第二个输入框为 0。
执行指令：找到 "Indices of vector (uvw)" 文字下方的**第二个**输入框（位于第一个输入框右边）。双击该输入框中心，输入数字 "0"。

=== 步骤 20：输入向量值 W ===
目标：设置第三个输入框为 0。
执行指令：找到 "Indices of vector (uvw)" 文字下方的**第三个**输入框（位于第二个输入框右边）。双击该输入框中心，输入数字 "0"。

=== 步骤 21：确认对齐设置 ===
目标：点击 "Align Face or Vector" 窗口的 OK 按钮。
执行指令：识别 "Align Face or Vector" 窗口右上角的 "OK" 按钮并点击它。
（等待 2 秒，回到主界面）

=== 步骤 22：打开 Input2 菜单 ===
目标：点击顶部菜单 "Input2"。
执行指令：请识别屏幕顶部菜单栏中的 "Input2" 文字并点击它。
（等待 1 秒，等待下拉菜单弹出）

=== 步骤 23：选择 Perspective 选项 ===
目标：点击下拉菜单中的 "Perspective"。
执行指令：请识别下拉菜单中的 "Perspective..." 选项并点击它。
（等待 2 秒，等待 "Perspective" 窗口弹出）

=== 步骤 24：取消勾选透视视图 ===
目标：取消勾选 "Perspective viewing"。
执行指令：请在 "Perspective" 窗口左上角，识别 "Perspective viewing" 文字旁边的方框并点击方框中心位置。

=== 步骤 25：确认设置 ===
目标：点击 "Perspective" 窗口的 OK 按钮。
执行指令：请识别 "Perspective" 窗口右上角的 "OK" 按钮并点击它。
（等待 2 秒，回到主界面）

=== 步骤 26：打开 Input2 菜单 ===
目标：点击顶部菜单 "Input2"。
执行指令：请识别屏幕顶部菜单栏中的 "Input2" 文字并点击它。
（等待 1 秒，等待下拉菜单弹出）

=== 步骤 27：打开 Background Color 窗口 ===
目标：点击下拉菜单中的 "Background Color..."。
执行指令：请识别下拉菜单中的 "Background Color..." 选项并点击它。
（等待 2 秒，等待 "Background Color" 窗口弹出）

=== 步骤 28：打开 Select Color 窗口 ===
目标：点击 "Background Color" 窗口右下角的 "Select Color" 按钮。
执行指令：在 "Background Color" 窗口中，请识别右下角的 "Select Color" 按钮并点击它。
（等待 1 秒，等待 "Select Color" 窗口弹出）

=== 步骤 29：选择白色颜色值 ===
目标：选中 "255 255 255" 单选框。
执行指令：请在 "Select Color" 窗口中，识别 "255 255 255" 文字或其旁边的单选按钮并点击它。

=== 步骤 30：确认 Select Color 设置 ===
目标：点击 "Select Color" 窗口右上角的 OK 按钮。
执行指令：请识别 "Select Color" 窗口右上角的 "OK" 按钮并点击它。
（等待 1 秒，返回 "Background Color" 窗口）

=== 步骤 31：确认 Background Color 设置 ===
目标：点击 "Background Color" 窗口右上角的 OK 按钮。
执行指令：请识别 "Background Color" 窗口右上角的 "OK" 按钮并点击它。
（等待 2 秒，返回主界面）

=== 步骤 32：打开 File 菜单 ===
目标：点击顶部菜单 "File" 。
执行指令：请识别屏幕顶部菜单栏中的 "File" 文字并点击它。
（等待 1 秒，等待下拉菜单弹出）

=== 步骤 33：打开 Save Graphics Window 窗口 ===
目标：点击下拉菜单中的 "Save Graphics Window"。
执行指令：请识别下拉菜单中的 "Save Graphics Window" 选项并点击它。
（等待 2 秒，等待 "Save Graphics Window" 窗口弹出）

=== 步骤 34：选择 BMP 文件格式 ===
目标：选中 ".BMP File" 单选框。
执行指令：请在 "Save Graphics Window" 窗口左侧，识别 ".BMP File" 文字或其旁边的单选按钮并点击它。

=== 步骤 35：确认 Save Graphics Window 设置 ===
目标：点击 "Save Graphics Window" 窗口右上角的 OK 按钮。
执行指令：请识别 "Save Graphics Window" 窗口右上角的 "OK" 按钮并点击它。
（等待 1 秒，进入 "Copy Screen to .bmp File" 窗口）

=== 步骤 36：确认保存 ===
目标：点击 "Copy Screen to .bmp File" 窗口右下角的 OK 按钮。
执行指令：请识别 "Copy Screen to .bmp File" 窗口右下角的 "OK" 按钮并点击它。
（等待 2 秒，完成保存操作）

任务结束。


 


"""

print(f">>> [3/3] Agent 就绪。请双手离开鼠标和键盘！")

# # ================= ⚡ 新增：前置硬编码操作 (替代原步骤 1) =================
# print(">>> [系统初始化] 正在执行启动脚本...")
# pyautogui.click(656, 1060)  # 直接调用，精准且不会报错
# time.sleep(2)              # 等待前台就绪
# # ===================================================================

print(">>> 任务开始...")

# 简单的循环执行逻辑
max_steps = 60  # 防止无限循环，最多执行10步
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
            if "pyautogui" in act_code or "keyboard" in act_code or "mouse" in act_code or "time" in act_code:
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




# ================= ⚡ 新增：后置硬编码操作 (替代原步骤 16) =================
# print("\n>>> [系统复位] 正在执行结束脚本...")
# pyautogui.click(607, 1060)  # 直接调用
# ===================================================================

print("\n>>> 程序结束。")