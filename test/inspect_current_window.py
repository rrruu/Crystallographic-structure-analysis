from pywinauto.application import Application
import time


def inspect_current_atoms_window():
    print(">>> [侦察模式] 正在连接已运行的 ATOMS 软件...")

    try:
        # 1. 连接到当前正在运行的 ATOMS 进程
        # 注意：这里用 connect 而不是 start，所以它不会打开新窗口
        app = Application(backend="win32").connect(path=r"D:\ATOMS65\Eragon.exe")

        # 2. 获取当前最顶层（活跃）的窗口
        # 无论你现在打开的是主界面、Import弹窗还是Save弹窗，它都会自动抓取
        current_win = app.top_window()

        # 获取窗口标题
        title = current_win.window_text()
        print(f">>> 捕获到目标窗口: 【{title}】")
        print(">>> 正在扫描控件结构，请稍候...")
        print("=" * 50)

        # 3. 打印控件树
        # 结果会显示窗口里所有按钮、输入框的 ID
        current_win.print_control_identifiers()

        print("=" * 50)
        print(">>> 扫描完成！请向上滚动查看控件的 title 和 class_name。")

    except Exception as e:
        print(f"\n>>> 连接失败: {e}")
        print("请检查：\n1. ATOMS 软件是否已经手动打开？\n2. 是否有管理员权限限制？")


if __name__ == "__main__":
    inspect_current_atoms_window()
