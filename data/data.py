#实现将.xyz文件中所有数据先+50再/100，避免负数
import os


def process_xyz_file():
    # 1. 设置文件路径
    # 获取当前 data.py 所在的目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接输入文件的完整路径: 项目根目录/file/untitled.xyz
    input_path = os.path.join(base_dir, 'file', 'xyz', 'untitled.xyz')
    # 设置输出文件的路径: 项目根目录/file/processed_untitled.xyz (生成一个新文件)
    output_path = os.path.join(base_dir, 'file', 'xyz', 'processed.xyz')

    print(f"正在读取文件: {input_path}")

    # 2. 打开文件进行处理
    try:
        with open(input_path, 'r', encoding='utf-8') as f_in, \
                open(output_path, 'w', encoding='utf-8') as f_out:

            lines = f_in.readlines()

            # XYZ 文件通常第一行是原子数量，第二行是注释
            # 我们直接将这两行原封不动地写入新文件
            if len(lines) > 0:
                f_out.write(lines[0])  # 写入 "18444"
            if len(lines) > 1:
                f_out.write(lines[1])  # 写入空白行或注释行

            # 3. 处理从第三行开始的数据
            # 格式示例: "Ga        -5.99565   -20.49430   -39.60450"
            for i in range(2, len(lines)):
                line = lines[i].strip()  # 去除首尾空格
                if not line:
                    continue  # 跳过空行

                parts = line.split()  # 按空格分割每一行

                # parts[0] 是元素符号 (如 Ga, Pd)
                # parts[1], parts[2], parts[3] 是 X, Y, Z 坐标
                element = parts[0]

                try:
                    # 将字符串转换为浮点数进行计算
                    original_x = float(parts[1])
                    original_y = float(parts[2])
                    original_z = float(parts[3])

                    # 4. 执行你的计算公式: (数据 + 50) / 100
                    new_x = (original_x + 50) / 100
                    new_y = (original_y + 50) / 100
                    new_z = (original_z + 50) / 100

                    # 5. 将处理后的数据写入新文件
                    # 使用 f-string 格式化，保留6位小数，并用制表符或空格对齐
                    new_line = f"{element:<4} {new_x:.6f}   {new_y:.6f}   {new_z:.6f}\n"
                    f_out.write(new_line)

                except ValueError:
                    # 如果某行数据格式不对（不是数字），则原样写入或报错
                    print(f"警告：第 {i + 1} 行数据格式异常，已跳过处理。内容: {line}")
                    f_out.write(line + "\n")

        print(f"处理完成！新文件已保存为: {output_path}")

    except FileNotFoundError:
        print(f"错误：找不到文件。请检查路径是否正确：{input_path}")
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == "__main__":
    process_xyz_file()