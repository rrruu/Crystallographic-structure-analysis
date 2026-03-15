# 将processed.xyz转化为.xlsx和.csv格式，同时添加其他列，使最终文件有10列
import os
import pandas as pd


def process_xyz_to_excel():
    # 1. 设置路径（使用相对路径）
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "file", "xyz", "processed.xyz")
    xlsx_output_dir = os.path.join(base_dir, "file", "xlsx")
    csv_output_dir = os.path.join(base_dir, "file", "csv")

    # 确保输出目录存在
    os.makedirs(xlsx_output_dir, exist_ok=True)
    os.makedirs(csv_output_dir, exist_ok=True)

    xlsx_path = os.path.join(xlsx_output_dir, "processed_data.xlsx")
    csv_path = os.path.join(csv_output_dir, "processed_data.csv")

    print(f"正在读取: {input_path}")

    try:
        # 2. 读取 processed.xyz 文件
        # 跳过前两行（原子数和注释）
        data = []
        with open(input_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[2:]  # 从第三行开始读
            for index, line in enumerate(lines):
                parts = line.split()
                if len(parts) < 4:
                    continue

                element = parts[0]
                x, y, z = parts[1], parts[2], parts[3]

                # 3. 按照规则构建每一行数据
                # 第一列: atom[index] + 元素符号 (例如 atom0Ga)
                col1 = f"atom[{index}]{element}"
                # 第二列: 固定 a
                col2 = "a"
                # 第三、四、五列: X, Y, Z
                col3, col4, col5 = x, y, z
                # 第六列: 固定 0.005
                col6 = "0.005"
                # 第七列: 固定 1
                col7 = "1"
                # 第八列: 根据元素判定
                if "Ga" in element:
                    col8 = "0.019"
                elif "Pd" in element:
                    col8 = "0.034"
                else:
                    col8 = "0.000"  # 兜底值
                # 第九列: 固定 Def
                col9 = "Def"
                # 第十列: 固定 0
                col10 = "0"

                data.append(
                    [col1, col2, col3, col4, col5, col6, col7, col8, col9, col10]
                )

        # 4. 创建 DataFrame
        # columns = [
        #     "Atom ID", "Type", "X", "Y", "Z",
        #     "Sigma", "Weight", "Element Val", "Status", "Flags"
        # ]
        # df = pd.DataFrame(data, columns=columns)
        df = pd.DataFrame(data)

        # 5. 导出 Excel
        df.to_excel(xlsx_path, index=False, header=False, engine="openpyxl")
        print(f"Excel文件已生成: {xlsx_path}")

        # 6. 导出 CSV
        df.to_csv(csv_path, index=False, header=False, encoding="utf-8-sig")
        print(f"CSV文件已生成: {csv_path}")

    except FileNotFoundError:
        print(f"错误：找不到输入文件 {input_path}")
    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    process_xyz_to_excel()
