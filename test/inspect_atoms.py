from pywinauto.application import Application
import time

# 配置软件路径
app_path = r"D:\ATOMS65\Eragon.exe"

try:
    print(">>> 正在尝试启动 ATOMS...")
    # 启动软件 (backend="win32" 适合老软件，如果报错找不到元素，改成 "uia")
    app = Application(backend="win32").start(app_path)

    # 强制等待软件完全启动
    print(">>> 等待软件加载 (10秒)...")
    time.sleep(10)

    # 连接到主窗口
    # 我们尝试通过标题来模糊匹配窗口
    # 你的截图显示标题是 "ATOMS Startup Window"
    dlg = app.window(title_re=".*ATOMS Startup Window.*")

    # 将窗口最大化 (为了看清楚)
    # dlg.maximize()

    print(">>> 正在扫描窗口内的所有控件...")
    print("==================================================")

    # 这一步会打印出窗口里所有的按钮、输入框及其 ID
    # 输出会非常长，请在控制台里仔细看
    dlg.print_control_identifiers()

    print("==================================================")
    print(">>> 扫描完成。请在上方日志中寻找 'Import' 字样。")

except Exception as e:
    print(f"\n>>> 发生错误: {e}")
    print("建议尝试将代码中的 backend='win32' 改为 backend='uia' 再试一次。")