import os
import re
import time
import pyautogui
import pyperclip
import io
import traceback
import subprocess
import sys
from pathlib import Path
from gui_agents.s3.agents.grounding import OSWorldACI
from gui_agents.s3.agents.agent_s import AgentS3

# ================= 1. 基础配置 =================
from config import API_KEY, BASE_URL, check_api_config

SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
GROUNDING_DIM =1000

# ================= 2. 自动化任务流配置 =================
# 阶段 1：初始设置与保存图片 (原有逻辑)
SUB_TASKS_STAGE_1 = [
    {
        "goal": "启动位于 'D:\\ATOMS65\\Eragon.exe' 的 ATOMS 软件，并确保主窗口处于最大化状态。",
        "desc": "环境初始化"
    },
    {
        "goal": "在 ATOMS 软件中点击 'Open'。在弹出的对话框地址栏输入 'C:\\Users\\Lenovo\\Desktop\\演示8' 并回车。确认正确进入该路径后，加载文件 'ICSD_CollCode103903.str'，直到结构图显示在主窗口中。",
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
        "goal": "保存结果：通过 'File' -> 'Save Graphics Window' 选 '.BMP' 格式。在保存对话框地址栏输入 'D:\\code\\python\\AgentS_ATOMS\\utils\\bmp' 并回车。确认正确进入该路径后，点击右下角 '保存' 按钮。",
        "desc": "结果导出"
    }
]


# 阶段 2：根据 match.py 结果进行二次设置 (新增逻辑)
def get_stage_2_tasks(angle_val):
    # match.py 返回 -76，则输入 76 并点逆时针
    abs_angle = str(abs(float(angle_val)))
    return [
        # {"goal": f"在界面左侧的角度输入框中输入 {abs_angle}，之后点击输入框上方的顺时针旋转按钮（向右弯的箭头）。",
        #  "desc": "修正旋转"},
        # {"goal": f"在主界面左侧的角度输入框中点击并输入 {angle_val}。注意：请务必点击输入框的中心，避免点击到顶部的菜单栏。完成后点击上方代表顺时针旋转的‘向右弯’箭头图标。",
        #  "desc": "修正旋转"
        # },
        # {"goal": f"双击界面左侧的角度输入框，在角度输入框中输入 284 ，之后点击输入框上方的顺时针旋转按钮（向右弯的箭头）。",
        #  "desc": "修正旋转"},
        # {"goal": f"双击界面左侧的角度输入框。在输入框内填入数字 76 。完成后，点击输入框上方代表逆时针旋转的‘向左弯’箭头按钮。",
        #  "desc": "旋转修正"
        # },
        {"goal": f"双击界面左侧的角度输入框。在输入框内填入数字 {abs_angle} 。完成后，点击输入框上方代表顺时针旋转的‘向右弯’箭头按钮。",
         "desc": "旋转修正"
        },
        # {"goal": f"在界面左侧的角度输入框内‘双击’以选中已有数值，随后直接键盘输入{angle_val}。注意：严禁使用 'Ctrl+A' 快捷键，因为它会触发 About 窗口。完成后，点击输入框上方代表顺时针旋转的‘向右弯’箭头按钮。",
        #  "desc": "安全修正旋转"
        # },
        {"goal": "在 'Input2' 菜单下打开 'Centering and Displacements'，选中 'No centering or displacements'，点击 OK。",
         "desc": "关闭自动中心"}
    ]


# 阶段 3：循环切割操作 (新增逻辑)
CUT_PARTS = ["A", "B", "UPPER", "LOWER"]


# ================= 3. 通用辅助函数 =================
def run_python_script(script_name, args=[]):
    utils_dir = Path(__file__).resolve().parent / "utils"
    script_path = utils_dir / script_name
    print(f"\n[*] 正在运行脚本: {script_name} {' '.join(args)}...")
    subprocess.run([sys.executable, str(script_path)] + args, check=True)


def init_agent():
    engine_params = {"engine_type": "openai",
                     "model": "gpt-4o",
                     # "model": "Pro/Qwen/Qwen2.5-VL-7B-Instruct",
                     "api_key": API_KEY,
                     "base_url": BASE_URL,
                     "temperature": 0.01}
    engine_params_grounding = {"engine_type": "openai",
                               "model": "doubao-1-5-ui-tars-250428",
                               "api_key": API_KEY,
                               "base_url": BASE_URL,
                               "grounding_width": GROUNDING_DIM,
                               "grounding_height": GROUNDING_DIM,
                               "temperature": 0.01}
    grounding_agent = OSWorldACI(env=None,
                                 platform="windows",
                                 engine_params_for_generation=engine_params,
                                 engine_params_for_grounding=engine_params_grounding,
                                 width=SCREEN_WIDTH,
                                 height=SCREEN_HEIGHT)
    return AgentS3(engine_params,
                   grounding_agent,
                   platform="windows",
                   max_trajectory_length=8,
                   enable_reflection=True)


def execute_agent_tasks(tasks):
    for task in tasks:
        print(f"\n" + "=" * 60)
        print(f"开始任务阶段: [{task['desc']}]")
        print(f"详细目标: {task['goal']}")
        print("=" * 60)
        # print(f"\n任务: [{task['desc']}] -> {task['goal']}")
        agent = init_agent()
        step, done = 0, False
        while step < 12 and not done:
            step += 1
            print(f"\n  [步数 {step}] 获取屏幕快照并进行视觉推理...")

            try:
                screenshot = pyautogui.screenshot()
                buffered = io.BytesIO()
                screenshot.save(buffered, format="PNG")
                obs = {"screenshot": buffered.getvalue()}

                # 获取 Agent 预测
                info, action = agent.predict(instruction=f"{task['goal']}\n完成请输出 DONE", observation=obs)

                if not action:
                    print("  [警告] Agent 未能生成动作，可能正在思考或已卡住。")
                    continue

                # 详细打印 Agent 生成的每一行操作代码
                for act_code in action:


                    print(f"  [指令确认] >>> {act_code}")

                    if "DONE" in act_code or "DONE" in str(info):
                        print("  [状态] 收到 DONE 信号，阶段目标达成。")
                        done = True
                        break

                    # 检查并执行 GUI 操作
                    if any(kw in act_code for kw in ["pyautogui", "keyboard", "mouse", "time"]):
                        print(f"  [正在执行] 正在调用底层接口执行上述代码...")
                        exec(act_code)
                        print("  [执行成功] 操作已下达。")
                    else:
                        print(f"  [跳过] 指令不含受信任的 GUI 操作库。")

                time.sleep(1.5)
            except Exception as e:
                print(f"  [严重错误] 在第 {step} 步发生异常: {e}")
                traceback.print_exc()
                break




            # step += 1
            # screenshot = pyautogui.screenshot()
            # buffered = io.BytesIO()
            # screenshot.save(buffered, format="PNG")
            # obs = {"screenshot": buffered.getvalue()}
            # info, action = agent.predict(instruction=f"{task['goal']}\n完成请输出 DONE", observation=obs)
            # if not action: continue
            # for act_code in action:
            #     if "DONE" in act_code or "DONE" in str(info):
            #         done = True;
            #         break
            #     if any(kw in act_code for kw in ["pyautogui", "keyboard", "mouse", "time"]):
            #         exec(act_code)
            # time.sleep(1.5)


def execute_agent_tasks_withoutctrla(tasks):
    for task in tasks:
        print(f"\n" + "=" * 60)
        print(f"开始任务阶段: [{task['desc']}]")
        print(f"详细目标: {task['goal']}")
        print("=" * 60)
        # print(f"\n任务: [{task['desc']}] -> {task['goal']}")
        agent = init_agent()
        step, done = 0, False
        while step < 12 and not done:
            step += 1
            print(f"\n  [步数 {step}] 获取屏幕快照并进行视觉推理...")

            try:
                screenshot = pyautogui.screenshot()
                buffered = io.BytesIO()
                screenshot.save(buffered, format="PNG")
                obs = {"screenshot": buffered.getvalue()}

                # 获取 Agent 预测
                info, action = agent.predict(instruction=f"{task['goal']}\n完成请输出 DONE", observation=obs)

                if not action:
                    print("  [警告] Agent 未能生成动作，可能正在思考或已卡住。")
                    continue

                # 详细打印 Agent 生成的每一行操作代码
                for act_code in action:

                    # # --- 核心拦截逻辑：防止 Agent 偷跑 Ctrl+A ---
                    # clean_code = act_code.lower().replace(" ", "")
                    # if "ctrl" in clean_code and "'a'" in clean_code:
                    #     print(f"  [拦截提示] 检测到危险指令: {act_code}。已将其替换为 5 次 Backspace。")
                    #     # 找到坐标并替换为安全动作 [cite: 297]
                    #     pyautogui.press(['backspace'] * 5)
                    #     continue

                    # # --- 改进的拦截逻辑：仅剔除 Ctrl+A 语句，保留其他语句 ---
                    # if "ctrl" in act_code.lower() and "'a'" in act_code.lower():
                    #     print(f"  [安全过滤] 已从指令流中剔除 Ctrl+A 动作，替换为 Backspace。")
                    #     # 将 hotkey('ctrl', 'a') 替换为 press('backspace') 的 5 次序列
                    #     # 这样即使是一行代码，其中的 click 和 write 也会被保留并执行
                    #     act_code = act_code.replace("pyautogui.hotkey('ctrl', 'a')", "pyautogui.press(['backspace']*5)")
                    #     act_code = act_code.replace('pyautogui.hotkey("ctrl", "a")', "pyautogui.press(['backspace']*5)")
                    #
                    # # --- 核心修复 2: 解决“丢字符”问题 (注入延迟与间隔) ---
                    # # 在 click 之后插入 0.5s 的休眠
                    # act_code = act_code.replace(");", "); time.sleep(0.5);")
                    # # 给所有的 write 加上 interval 模拟真实打字
                    # if "pyautogui.write" in act_code and "interval" not in act_code:
                    #     act_code = act_code.replace("pyautogui.write(", "pyautogui.write(interval=0.1, ")

                    # # --- 1. 安全拦截 Ctrl+A 并保持后续指令可用 ---
                    # if "ctrl" in act_code.lower() and "'a'" in act_code.lower():
                    #     print(f"  [拦截] 剔除 Ctrl+A，替换为退格序列。")
                    #     act_code = act_code.replace("pyautogui.hotkey('ctrl', 'a')", "pyautogui.press(['backspace']*5)")
                    #     act_code = act_code.replace('pyautogui.hotkey("ctrl", "a")', "pyautogui.press(['backspace']*5)")

                    # # --- 1. 安全拦截 Ctrl+A 并替换为：双击当前位置 + 5次退格 ---
                    # # 这样可以确保先选中输入框内的文字，再进行物理清理，完全避开快捷键冲突
                    # if "ctrl" in act_code.lower() and ("'a'" in act_code.lower() or '"a"' in act_code.lower()):
                    #     print(f"  [拦截] 已将危险的 Ctrl+A 替换为：双击选中 + 5次退格。")
                    #
                    #     # 定义替换后的指令序列
                    #     # doubleClick() 不带坐标时会直接双击当前鼠标所在的位置
                    #     safe_sequence = "pyautogui.doubleClick(); pyautogui.press(['backspace']*5)"
                    #
                    #     # 同时兼容单引号和双引号的情况
                    #     act_code = act_code.replace("pyautogui.hotkey('ctrl', 'a')", safe_sequence)
                    #     act_code = act_code.replace('pyautogui.hotkey("ctrl", "a")', safe_sequence)
                    #
                    #
                    # # --- 2. 注入点击后的强制延迟 ---
                    # act_code = act_code.replace(");", "); time.sleep(0.5);")
                    #
                    # # --- 3. 正则修复 write 参数顺序 (解决丢字符且不报错) ---
                    # # 将 pyautogui.write('xxx') 转换为 pyautogui.write('xxx', interval=0.1)
                    # if "pyautogui.write" in act_code and "interval" not in act_code:
                    #     act_code = re.sub(r"pyautogui\.write\((.*?)\)", r"pyautogui.write(\1, interval=0.1)", act_code)
                    #
                    #

                    # --- 1. 拦截 Ctrl+A 并替换为双击选中+退格 ---
                    if "ctrl" in act_code.lower() and ("'a'" in act_code.lower() or '"a"' in act_code.lower()):
                        print(f"  [安全过滤] 已剔除 Ctrl+A，替换为双击清除。")
                        act_code = act_code.replace("pyautogui.hotkey('ctrl', 'a')",
                                                    "pyautogui.doubleClick(); pyautogui.press(['backspace']*5)")
                        act_code = act_code.replace('pyautogui.hotkey("ctrl", "a")',
                                                    "pyautogui.doubleClick(); pyautogui.press(['backspace']*5)")

                    # --- 2. 核心改进：将 write 转换为 复制+粘贴 (解决丢字符问题) ---
                    if "pyautogui.write" in act_code:
                        print(f"  [稳定性增强] 已将 write 转换为剪贴板粘贴模式。")
                        # 提取 write 括号中的内容
                        match = re.search(r"pyautogui\.write\((.*?)\)", act_code)
                        if match:
                            content = match.group(1).split(',')[0].strip("'\" ")
                            # 构建新指令：先复制到剪贴板，再执行 Ctrl+V
                            paste_code = f"pyperclip.copy('{content}'); pyautogui.hotkey('ctrl', 'v')"
                            act_code = re.sub(r"pyautogui\.write\(.*?\)", paste_code, act_code)

                    # --- 3. 注入延迟，确保软件响应 ---
                    act_code = act_code.replace(");", "); time.sleep(0.5);")



                    print(f"  [指令确认] >>> {act_code}")

                    if "DONE" in act_code or "DONE" in str(info):
                        print("  [状态] 收到 DONE 信号，阶段目标达成。")
                        done = True
                        break

                    # 检查并执行 GUI 操作
                    if any(kw in act_code for kw in ["pyautogui", "keyboard", "mouse", "time"]):
                        print(f"  [正在执行] 正在调用底层接口执行上述代码...")
                        exec(act_code)
                        print("  [执行成功] 操作已下达。")
                    else:
                        print(f"  [跳过] 指令不含受信任的 GUI 操作库。")

                time.sleep(1.5)
            except Exception as e:
                print(f"  [严重错误] 在第 {step} 步发生异常: {e}")
                traceback.print_exc()
                break




            # step += 1
            # screenshot = pyautogui.screenshot()
            # buffered = io.BytesIO()
            # screenshot.save(buffered, format="PNG")
            # obs = {"screenshot": buffered.getvalue()}
            # info, action = agent.predict(instruction=f"{task['goal']}\n完成请输出 DONE", observation=obs)
            # if not action: continue
            # for act_code in action:
            #     if "DONE" in act_code or "DONE" in str(info):
            #         done = True;
            #         break
            #     if any(kw in act_code for kw in ["pyautogui", "keyboard", "mouse", "time"]):
            #         exec(act_code)
            # time.sleep(1.5)


# ================= 4. 主流程 =================
def main():
    check_api_config()
    # 1. 第一部分自动化
    execute_agent_tasks(SUB_TASKS_STAGE_1)

    # 2. 图像处理与配准
    run_python_script("image_processing.py")
    run_python_script("match.py")

    # #test
    # pyautogui.click(678, 1062)

    # 读取旋转角度
    angle_file = Path(__file__).resolve().parent / "utils" / "results" / "angle.txt"
    angle = "284.0"  # 默认值
    if angle_file.exists():
        angle = angle_file.read_text().strip()

    # 3. 第二部分自动化：旋转与中心设置
    execute_agent_tasks_withoutctrla(get_stage_2_tasks(angle))

    # 4. 实时探测并转换坐标
    run_python_script("detector_transform.py")

    # 5. 第三部分：切割循环
    for part in CUT_PARTS:
        print(f"\n>>> 开始切割部分: {part}")
        # Agent: 开启 Delete Tool
        execute_agent_tasks(
            [{"goal": "点击主界面右侧的 'Delete Tool' 按钮，在弹出的提示窗口中点击 '确定' 以开始切割模式。",
              "desc": "启动切割工具"}])

        # 脚本: 执行路径点击
        run_python_script("click_executor_3.py", [part])

        # Agent: 确认切割
        execute_agent_tasks(
            [{"goal": "点击界面中出现的 '确认' 按钮以完成本次切割操作。", "desc": "确认切割成果"}])
        time.sleep(2)

    print("\n>>> [完成] 全流程自动化已结束。")


if __name__ == "__main__":
    main()