from pywinauto.application import Application
import time
import pyautogui  # 用于处理文件路径输入，兼容性最好


def automate_atoms_open():
    # 软件路径
    app_path = r"D:\ATOMS65\Eragon.exe"

    print(">>> [1/3] 启动 ATOMS...")
    # 启动应用 (backend="win32" 适合 ATOMS 这种老软件)
    app = Application(backend="win32").start(app_path)

    # 连接主窗口
    # 标题匹配：ATOMS Startup Window
    main_win = app.window(title="ATOMS Startup Window")

    print(">>> 等待窗口加载...")
    main_win.wait("visible", timeout=20)

    # ==========================================================
    # 关键操作：点击 Open 按钮
    # ==========================================================
    print(">>> [2/3] 点击 Open 按钮 (底层操作)...")

    # 根据之前的探测日志：Button - 'Open'
    # 我们可以直接通过 .Open 来调用它
    try:
        main_win.Open.click()
    except Exception as e:
        # 双重保险：如果直接属性访问失败，尝试用标题查找
        print(f"直接点击失败，尝试查找控件: {e}")
        main_win.child_window(title="Open", class_name="Button").click()

    print(">>> Open 按钮已点击。等待文件选择弹窗...")

    # ==========================================================
    # 处理 "Open an ATOMS Data File" 弹窗
    # ==========================================================
    # 目标文件名
    target_filename = "Li2ZrFe(PO4)3.str"

    # 连接新弹出的窗口
    # 根据你的截图，窗口标题是 "Open an ATOMS Data File"
    open_dialog = app.window(title="Open an ATOMS Data File")

    print(">>> 等待弹窗出现...")
    open_dialog.wait("visible", timeout=10)

    print(f">>> [3/3] 选择文件: {target_filename} 并打开...")

    # 【核心技巧】
    # 在 Windows 标准文件弹窗中，直接输入文件名会自动选中该文件。
    # 这比去文件列表(List View)里用鼠标一个个找要精准得多。

    time.sleep(1)  # 给窗口一点反应时间

    # 1. 输入文件名 (这一步等同于“点击 Li2ZrFe(PO4)3.str 文件”)
    pyautogui.write(target_filename)

    # 2. 稍作等待
    time.sleep(0.5)

    # 3. 按下回车 (这一步等同于“点击 打开 按钮”)
    # 在文件输入框有内容时，回车键默认触发“打开”动作
    pyautogui.press("enter")

    # 如果你一定要点击那个“打开”按钮（物理点击），可以使用下面的代码（可选）：
    # 注意：中文系统下按钮通常叫 "打开(O)"，英文系统叫 "Open"
    # open_dialog.Button1.click()  # Button1 通常是默认的确认按钮

    print(f"\n>>> ✅ 成功！已打开文件: {target_filename}")


if __name__ == "__main__":
    try:
        automate_atoms_open()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        # 如果报错，很有可能是窗口标题变了，或者弹窗没出来
        print("请检查：\n1. 软件路径是否正确？\n2. 弹窗标题是否完全匹配？")
