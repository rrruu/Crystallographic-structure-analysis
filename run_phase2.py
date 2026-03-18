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
GROUNDING_DIM = 1000

# 建议不再统一使用 GROUNDING_DIM，而是分设宽和高
GROUNDING_WIDTH = 1920
GROUNDING_HEIGHT = 1080

# ================= 2. 自动化任务流配置 =================
# 阶段 1：初始设置与保存图片 (原有逻辑)
# SUB_TASKS_STAGE_1 = [
#     {
#         "goal": "启动位于 'D:\\ATOMS65\\Eragon.exe' 的 ATOMS 软件，并确保主窗口处于最大化状态。",
#         "desc": "环境初始化"
#     },
#     {
#         "goal": "在 ATOMS 软件中点击 'Open'。在弹出的对话框地址栏输入 'D:\\yan\\agent\\第二阶段_测试' 并回车。确认正确进入该路径后，加载文件 'Pd2Ga-400-a-02.str'，直到结构图显示在主窗口中。",
#         "desc": "数据加载"
#     }
#
# ]
SUB_TASKS_STAGE_1 = [
    {
        "goal": "启动位于 'D:\\yan\\agent\\4\\Pd2Ga-400-a-02.str' 的 文件。",
        "desc": "数据加载",
    }
]


# 阶段 2：
SUB_TASKS_STAGE_2 = [
    {
        "goal": f"双击界面左侧的角度输入框。在输入框内填入数字 90 。完成后，依次点击：1. 第二排右侧的向上箭头按钮（↑）；2. 第三排右侧的向左箭头按钮（←，即指向左侧但位于右边的按钮）。",
        "desc": "旋转修正",
    },
    {
        "goal": "保存结果：通过 'File' -> 'Export' ，点击File format旁边的下拉框，在下拉框中选择'.xyz'格式。之后点击OK按钮保存。在保存对话框地址栏输入 'D:\\code\\projects\\innoclaw\\data\\projects\\Crystallographic-structure-analysis-main\\data\\file\\xyz' 并回车。确认正确进入该路径后，点击右下角 '保存' 按钮。",
        "desc": "结果导出",
    },
]


# 阶段 3：用Data transaction.txt打开csv文件
SUB_TASKS_STAGE_3 = [
    {
        "goal": "启动位于 'D:\\code\\projects\\innoclaw\\data\\projects\\Crystallographic-structure-analysis-main\\data\\file\\xlsx\\Data transation.xlsx' 的 Data transation.xlsx 文件。",
        "desc": "打开xlsx文件",
    },
    {
        "goal": "在 '文件' 菜单下打开 '打开' 选项，在弹出的对话框地址栏输入 'D:\\code\\projects\\innoclaw\\data\\projects\\Crystallographic-structure-analysis-main\\data\\file\\csv' 地址并回车。确认正确进入该路径后，选择文件类型为 '所有文件' ，打开文件 'processed_data.csv' 。",
        "desc": "在xlsx文件中打开csv文件",
    },
    {
        "goal": "在 'processed_data.csv' 文件中，全选并复制表格中的所有内容。",
        "desc": "复制csv文件中全部数据",
    },
    {
        "goal": "打开 'D:\\code\\projects\\innoclaw\\data\\projects\\Crystallographic-structure-analysis-main\\data\\file\\txt\\Data transation.txt'，在文件末尾的新一行中粘贴刚刚在'processed_data.csv' 文件中复制的内容。",
        "desc": "将数据追加到目标文本文件",
    },
    {
        "goal": "保存并关闭 'Data transation.txt'。关闭 'Data transation.xlsx' 和 'processed_data.csv' 窗口，且不对 'Data transation.xlsx' 和 'processed_data.csv' 进行保存。",
        "desc": "保存并清理工作环境",
    },
]


# ================= 3. 通用辅助函数 =================
def run_python_script(script_name, args=[]):
    data_dir = Path(__file__).resolve().parent / "data"
    script_path = data_dir / script_name
    print(f"\n[*] 正在运行脚本: {script_name} {' '.join(args)}...")
    subprocess.run([sys.executable, str(script_path)] + args, check=True)


def init_agent():
    engine_params = {
        "engine_type": "openai",
        "model": "gpt-4o",
        # "model": "Pro/Qwen/Qwen2.5-VL-7B-Instruct",
        # "model": "doubao-seed-2-0-pro-260215",
        "api_key": API_KEY,
        "base_url": BASE_URL,
        "temperature": 0.01,
    }
    engine_params_grounding = {
        "engine_type": "openai",
        "model": "doubao-1-5-ui-tars-250428",
        "api_key": API_KEY,
        "base_url": BASE_URL,
        "grounding_width": GROUNDING_DIM,
        "grounding_height": GROUNDING_DIM,
        # "grounding_width": GROUNDING_WIDTH,
        # "grounding_height": GROUNDING_HEIGHT,
        "temperature": 0.01,
    }
    grounding_agent = OSWorldACI(
        env=None,
        platform="windows",
        engine_params_for_generation=engine_params,
        engine_params_for_grounding=engine_params_grounding,
        width=SCREEN_WIDTH,
        height=SCREEN_HEIGHT,
    )
    return AgentS3(
        engine_params,
        grounding_agent,
        platform="windows",
        max_trajectory_length=8,
        enable_reflection=True,
    )


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
                info, action = agent.predict(
                    instruction=f"{task['goal']}\n完成请输出 DONE", observation=obs
                )

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
                    if any(
                        kw in act_code
                        for kw in ["pyautogui", "keyboard", "mouse", "time"]
                    ):
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
                info, action = agent.predict(
                    instruction=f"{task['goal']}\n完成请输出 DONE", observation=obs
                )

                if not action:
                    print("  [警告] Agent 未能生成动作，可能正在思考或已卡住。")
                    continue

                # 详细打印 Agent 生成的每一行操作代码
                for act_code in action:

                    # --- 1. 拦截 Ctrl+A 并替换为双击选中+退格 ---
                    if "ctrl" in act_code.lower() and (
                        "'a'" in act_code.lower() or '"a"' in act_code.lower()
                    ):
                        print(f"  [安全过滤] 已剔除 Ctrl+A，替换为双击清除。")
                        act_code = act_code.replace(
                            "pyautogui.hotkey('ctrl', 'a')",
                            "pyautogui.doubleClick(); pyautogui.press(['backspace']*5)",
                        )
                        act_code = act_code.replace(
                            'pyautogui.hotkey("ctrl", "a")',
                            "pyautogui.doubleClick(); pyautogui.press(['backspace']*5)",
                        )

                    # 2. 增强逻辑：修复 UnicodeEscape 错误
                    if "pyautogui.write" in act_code:
                        match = re.search(r"pyautogui\.write\((.*?)\)", act_code)
                        if match:
                            # 提取原始内容并去除多余引号
                            content = match.group(1).split(",")[0].strip("'\" ")
                            # 使用 repr(content) 自动处理反斜杠转义
                            paste_code = f"pyperclip.copy({repr(content)}); pyautogui.hotkey('ctrl', 'v')"
                            act_code = re.sub(
                                r"pyautogui\.write\(.*?\)", paste_code, act_code
                            )

                    # # --- 2. 核心改进：将 write 转换为 复制+粘贴 (解决丢字符问题) ---
                    # if "pyautogui.write" in act_code:
                    #     print(f"  [稳定性增强] 已将 write 转换为剪贴板粘贴模式。")
                    #     # 提取 write 括号中的内容
                    #     match = re.search(r"pyautogui\.write\((.*?)\)", act_code)
                    #     if match:
                    #         content = match.group(1).split(',')[0].strip("'\" ")
                    #         # 构建新指令：先复制到剪贴板，再执行 Ctrl+V
                    #         paste_code = f"pyperclip.copy('{content}'); pyautogui.hotkey('ctrl', 'v')"
                    #         act_code = re.sub(r"pyautogui\.write\(.*?\)", paste_code, act_code)

                    # --- 3. 注入延迟，确保软件响应 ---
                    act_code = act_code.replace(");", "); time.sleep(0.5);")

                    print(f"  [指令确认] >>> {act_code}")

                    if "DONE" in act_code or "DONE" in str(info):
                        print("  [状态] 收到 DONE 信号，阶段目标达成。")
                        done = True
                        break

                    # 检查并执行 GUI 操作
                    if any(
                        kw in act_code
                        for kw in ["pyautogui", "keyboard", "mouse", "time"]
                    ):
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


# ================= 4. 主流程 =================
def main():
    check_api_config()
    # 1. 第一部分自动化
    execute_agent_tasks(SUB_TASKS_STAGE_1)

    # 2. 第二部分自动化
    execute_agent_tasks_withoutctrla(SUB_TASKS_STAGE_2)

    # 3. python实现文件处理操作，依次调用data/data.py,data/convert_to_xlsx.py,data/update_path.py这三个python文件
    run_python_script("data.py")
    run_python_script("convert_to_xlsx.py")
    run_python_script("update_path.py")

    # 4. 第三部分自动化
    execute_agent_tasks(SUB_TASKS_STAGE_3)
    print("\n>>> [完成] 全流程自动化已结束。")


if __name__ == "__main__":
    main()
