import time
import pyautogui

print("请在 3 秒内把鼠标移到你想测试的地方，然后不要动……")
time.sleep(3)

x, y = pyautogui.position()
print(f"当前鼠标位置: ({x}, {y})")

time.sleep(1)
print("3 秒后我会在这个坐标点一下，请盯着屏幕看是不是点在同一个位置……")
time.sleep(3)

pyautogui.click(x, y)
print("点击完成。")
