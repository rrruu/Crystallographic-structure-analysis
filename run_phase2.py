import os
import re
import time
import atexit
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
from project_paths import (
    PROJECT_ROOT,
    build_phase2_subtasks_stage_1,
    build_phase2_subtasks_stage_2,
    build_phase2_subtasks_stage_3,
)

SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
GROUNDING_DIM = 1000

# 建议不再统一使用 GROUNDING_DIM，而是分设宽和高
GROUNDING_WIDTH = 1920
GROUNDING_HEIGHT = 1080
RESULTS_DIR = PROJECT_ROOT / "utils" / "results"
PHASE1_DONE_FILE = RESULTS_DIR / "phase1.done"
PHASE1_LOCK_FILE = RESULTS_DIR / "phase1.lock"
PHASE2_LOCK_FILE = RESULTS_DIR / "phase2.lock"
PHASE2_DONE_FILE = RESULTS_DIR / "phase2.done"
PHASE2_FAIL_FILE = RESULTS_DIR / "phase2.fail"

# ================= 2. 自动化任务流配置 =================
# 路径由 project_paths / paths_user 统一生成（见 paths_user.example.py）
SUB_TASKS_STAGE_1 = build_phase2_subtasks_stage_1()
SUB_TASKS_STAGE_2 = build_phase2_subtasks_stage_2()
SUB_TASKS_STAGE_3 = build_phase2_subtasks_stage_3()


# ================= 3. 通用辅助函数 =================
def _pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def acquire_phase_lock():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if PHASE2_LOCK_FILE.exists():
        old_pid = None
        try:
            old_pid = int(PHASE2_LOCK_FILE.read_text(encoding="utf-8").strip())
        except Exception:
            old_pid = None
        if old_pid and _pid_running(old_pid):
            raise RuntimeError(
                f"检测到 run_phase2.py 已在运行（PID={old_pid}）。为避免重复执行，本次退出。"
            )
        print("[警告] 检测到陈旧 phase2.lock，已自动清理。")
        PHASE2_LOCK_FILE.unlink(missing_ok=True)

    PHASE2_LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(release_phase_lock)


def release_phase_lock():
    PHASE2_LOCK_FILE.unlink(missing_ok=True)


def ensure_phase1_ready():
    if PHASE1_LOCK_FILE.exists():
        raise RuntimeError("检测到 phase1.lock，Phase 1 可能仍在执行。请等待其结束后再运行 Phase 2。")
    if not PHASE1_DONE_FILE.exists():
        raise RuntimeError("未检测到 phase1.done，拒绝执行 Phase 2。请先成功完成 run_phase1.py。")


def mark_phase_done():
    PHASE2_DONE_FILE.write_text(
        f"status=success\npid={os.getpid()}\ntime={time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        encoding="utf-8",
    )
    PHASE2_FAIL_FILE.unlink(missing_ok=True)


def mark_phase_fail(err: Exception):
    PHASE2_FAIL_FILE.write_text(
        (
            f"status=failed\npid={os.getpid()}\ntime={time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"error={repr(err)}\n"
        ),
        encoding="utf-8",
    )


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
    ensure_phase1_ready()
    acquire_phase_lock()
    PHASE2_DONE_FILE.unlink(missing_ok=True)
    PHASE2_FAIL_FILE.unlink(missing_ok=True)
    check_api_config()
    try:
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
        mark_phase_done()
        print("\n>>> [完成] 全流程自动化已结束。")
    except Exception as e:
        mark_phase_fail(e)
        raise


if __name__ == "__main__":
    main()
