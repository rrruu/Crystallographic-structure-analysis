#更新Data transation.txt文件的首行地址，更新为该文件在电脑中的绝对地址
import os


def update_file_path():
    # 1. 使用相对路径定位文件
    # 获取当前脚本 (update_path.py) 所在的根目录
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 拼接得到目标文件的实际路径：根目录/file/txt/Data transation.txt
    target_file_path = os.path.join(base_dir, 'file', 'txt', 'Data transation.txt')

    print(f"正在处理文件: {target_file_path}")

    try:
        # 2. 读取文件内容
        if not os.path.exists(target_file_path):
            print(f"错误：在路径 {target_file_path} 下找不到文件。")
            return

        with open(target_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if len(lines) > 0:
            # 3. 构造新的第一行内容
            # 获取当前文件在系统中的真实绝对路径
            actual_absolute_path = os.path.abspath(target_file_path)

            # 保持原有的格式 file|路径
            new_first_line = f"file|{actual_absolute_path}\n"

            # 替换第一行
            lines[0] = new_first_line

            # 4. 将修改后的内容写回文件
            with open(target_file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            print("路径更新成功！")
            print(f"新路径已写入: {actual_absolute_path}")
        else:
            print("错误：文件内容为空。")

    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    update_file_path()