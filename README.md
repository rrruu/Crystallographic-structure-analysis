# Crystallographic-structure-analysis 项目说明

本文档描述 **Crystallographic-structure-analysis** 项目的实际结构、用途与运行方式，面向本仓库的二次开发与日常使用。  
项目根目录下的 `README_agents.md` 为 [simular-ai/Agent-S](https://github.com/simular-ai/Agent-S) 原仓库说明；**本文件（README.md）为基于当前项目实际情况编写的说明。**

---

## 一、项目简介

- **基础来源**：2025 年 11 月末从 [simular-ai/Agent-S](https://github.com/simular-ai/Agent-S/tree/main) 的 `main` 分支手动下载并放入本文件夹。当前上游仓库已有更新，本仓库保留当时快照并在此基础上扩展。
- **目标**：利用 Agent（基于 Agent S3 的视觉 + 规划能力）实现**电脑本地的自动化操作**，主要围绕 **ATOMS** 软件操作与后续**数据处理**流程。
- **流程划分**：整体分为**三个阶段**。目前仅完成**第一阶段**与**第二阶段**的流程实现，并分别对应两个入口脚本；**第三阶段**的具体流程待补充。最终计划是将三阶段整合为**单一入口**，运行一个文件即可完成全流程。

---

## 二、项目结构概览

### 2.1 自行添加或修改的部分

| 路径 | 说明 |
|------|------|
| **config.py** | API 配置：从环境变量 `AGENTS_ATOMS_API_KEY`、`AGENTS_ATOMS_BASE_URL` 或根目录 `.env` 读取，避免密钥写进代码。 |
| **.env.example** | 环境变量示例；复制为 `.env` 并填入真实 API Key 与 Base URL 后使用（`.env` 已加入 .gitignore，不会提交）。 |
| **project_paths.py** | 路径统一入口：`utils/bmp`、`data/file/...` 等相对项目根自动解析；Agent 任务文案中的路径由此生成。 |
| **paths_user.example.py** | 本机路径模板（ATOMS 路径、第一阶段打开目录、第二阶段 .str 文件等）；复制为 **paths_user.py** 后按需修改（`paths_user.py` 已加入 .gitignore，勿提交）。未创建时回退到项目内占位路径。 |
| **run_phase1.py** | 第一阶段完整流程入口：ATOMS 自动化 + 图像处理与配准 + 旋转/中心设置 + 坐标转换 + 切割循环。 |
| **run_phase2.py** | 第二阶段完整流程入口：加载文件、旋转与导出 xyz → 数据处理脚本 → Agent 操作 xlsx/csv/txt 合并数据。 |
| **test/** | 项目运行与调试过程中使用的测试文件（如 `run.py`、`run_test - 副本_1.py` 等）。 |
| **utils/** | 第一阶段所依赖的脚本与中间/结果文件（图像处理、配准、坐标转换、切割点击执行等）。 |
| **data/** | 第二阶段所依赖的脚本与数据文件（xyz 处理、xlsx/csv 转换、路径更新及 `file/` 下的各类数据）。 |

### 2.2 原 Agent-S 仓库保留内容（未在 2.1 中列出的部分）

- **gui_agents/**：Agent S 核心库（含 S3 的 agent、grounding、memory 等）。
- **run.py**：原仓库的示例运行脚本（长任务提示词 + Agent 循环）。
- **README_agents.md**、**WAA_setup.md**、**models.md**：原仓库的说明与配置文档。
- **setup.py**、**requirements.txt**：依赖与安装配置。
- **images/**、**.github/**、**evaluation_sets/**、**osworld_setup/**、**integrations/** 等：原仓库的其余目录与文件。

---

## 三、阶段流程说明

### 3.1 第一阶段（run_phase1.py）

1. **Agent 自动化**：启动 ATOMS、打开指定路径与结构文件、配置 Boundary（Sphere, Radius=45）、Rotation（Align Face or Vector, 向量 1,0,0）、Input2（关闭 Perspective、背景白）、保存图形窗口为 BMP 到 `utils/bmp`。
2. **图像处理**：调用 `utils/image_processing.py`（BMP→PNG、去白底、红点提取等），产出供配准用的图像。
3. **图像配准与角度**：调用 `utils/match.py`，进行原图与目标图的配准与蓝点匹配，输出旋转角度到 `utils/results/angle.txt` 以及边界/坐标等 CSV。
4. **Agent 二次操作**：根据 `angle.txt` 生成“旋转修正”与“关闭自动中心”等子任务，由 Agent 执行（内部使用 `execute_agent_tasks_withoutctrla`，对 Ctrl+A 等做安全替换，并用剪贴板粘贴替代部分 `write` 以提升稳定性）。
5. **坐标转换**：调用 `utils/detector_transform.py`，实时探测屏幕上的 ATOMS 工作区，将图像坐标映射为屏幕坐标，供切割点击使用。
6. **切割循环**：对 `CUT_PARTS`（A, B, UPPER, LOWER）依次：Agent 打开 Delete Tool 并确认 → 调用 `utils/click_executor_3.py` 按部分名执行路径点击 → Agent 点击“确认”完成切割。

### 3.2 第二阶段（run_phase2.py）

1. **Agent 自动化（阶段 1）**：按 `SUB_TASKS_STAGE_1` 加载指定文件（当前脚本中为打开某一 str 文件）。
2. **Agent 自动化（阶段 2）**：按 `SUB_TASKS_STAGE_2` 执行旋转（如双击角度框输入 90、点击箭头等）并导出图形为 xyz 到 `data/file/xyz`。
3. **数据处理脚本（按顺序）**：  
   - `data/data.py`：读取 `data/file/xyz/untitled.xyz`，对坐标做 `(x+50)/100` 等处理，写出 `processed.xyz`。  
   - `data/convert_to_xlsx.py`：将 `processed.xyz` 转为带多列的 `processed_data.xlsx` 与 `processed_data.csv`。  
   - `data/update_path.py`：更新 `data/file/txt/Data transation.txt` 的首行路径为当前机器上的绝对路径。
4. **Agent 自动化（阶段 3）**：按 `SUB_TASKS_STAGE_3` 打开 Data transation.xlsx、在软件中打开 processed_data.csv、全选复制、粘贴到 Data transation.txt 末尾、保存并关闭相关窗口。

### 3.3 第三阶段

第三阶段的具体步骤尚未给出，待提供后再实现并（与 Phase1/Phase2）整合到统一入口。

---

## 四、目录与脚本说明

### 4.1 utils/（第一阶段）

| 文件/目录 | 说明 |
|-----------|------|
| **image_processing.py** | BMP→PNG、去白底、红点提取等；输出到 `png/`、`images/origin/` 等。 |
| **match.py** | 原图与目标图（如 `images/origin/1.png` 与 `images/solution/2.png`）配准与蓝点匹配；输出 `results/angle.txt`、`results/*.csv`、对齐叠加图等。 |
| **detector_transform.py** | 实时截屏识别 ATOMS 白色工作区，将图像坐标映射为屏幕坐标；读写 `results/blue_points_in_source_2.csv`、`final_screen_coords_blue.csv`、`final_screen_coords_purple.csv`。 |
| **click_executor_3.py** | 根据 `results/` 下蓝/紫屏幕坐标 CSV，按部分名（A/B/UPPER/LOWER）规划路径并执行 pyautogui 点击。 |
| **bmp/**、**png/**、**images/**、**results/** | 各脚本的输入/输出与中间结果（BMP、PNG、配准图、CSV、angle.txt 等）。 |

### 4.2 data/（第二阶段）

| 文件/目录 | 说明 |
|-----------|------|
| **data.py** | 读取 `file/xyz/untitled.xyz`，坐标做 `(x+50)/100` 等运算，写出 `file/xyz/processed.xyz`。 |
| **convert_to_xlsx.py** | 读取 `file/xyz/processed.xyz`，生成多列表格，写出 `file/xlsx/processed_data.xlsx` 与 `file/csv/processed_data.csv`。 |
| **update_path.py** | 将 `file/txt/Data transation.txt` 首行更新为“file|该文件的绝对路径”。 |
| **file/** | 按任务或实验组织的 xlsx、csv、txt、xyz 等数据与结果（如 `file/xyz/`、`file/xlsx/`、`file/txt/`、`file/1/1/` 等）。 |

### 4.3 test/

存放运行与调试时使用的测试脚本（如与 `run.py` 同名的测试入口、`run_test - 副本_1.py` 等），不参与 Phase1/Phase2 主流程。

---

## 五、安装与配置

### 5.1 当前开发/运行环境说明

本项目在以下环境中开发与测试，若复现问题或界面坐标异常，可优先对照本环境：

- **操作系统**：Windows
- **显示**：屏幕缩放 100%，分辨率 **1920×1080**，显示方向**横向**
- **输入法**：美式键盘 - 英语（美国）
- **主模型**：**gpt-4o**
- **Grounding 模型**：**doubao-1-5-ui-tars-250428**

脚本中的屏幕尺寸与 grounding 参数已按上述设置；更换分辨率、缩放或模型时需相应修改配置。

### 5.2 环境概览

- **推荐 Python 版本**：**3.10**（本项目当前使用环境为 **Python 3.10.19**，见 `conda_list.txt`）。
- **推荐环境管理**：使用 **Conda** 创建独立环境（如 `agents_a`），避免与系统或其他项目冲突。
- **参考文件**：
  - **conda_list.txt**：当前可用环境 `agents_a` 的完整依赖列表（`conda list` 导出），用于**完全复现**环境。
  - **requirements.txt**：原 Agent-S 仓库的 pip 依赖列表，可与本说明结合使用。
  - **README_agents.md**：原仓库的安装、API 配置、模型与 Grounding 说明，与本项目共用同一套 Agent 能力时请一并阅读。

### 5.3 使用 Conda 创建并激活环境（推荐）

在项目根目录 `AgentS_ATOMS` 下执行：

```bash
# 创建 Python 3.10 环境，环境名可自定（此处以 agents_a 为例）
conda create -n agents_a python=3.10 -y

# 激活环境
conda activate agents_a
```

### 5.4 安装依赖（两种方式任选其一）

#### 方式一：按当前项目环境完整复现（推荐）

本仓库已提供 **conda_list.txt**，对应环境名为 `agents_a`。若需在新机器上复现相同环境，可：

1. 按 5.3 创建并激活同名（或新名）Conda 环境，且 **Python 版本为 3.10**。
2. 在激活的环境中安装本仓库（可编辑模式，便于改代码）：

   ```bash
   cd D:\code\python\AgentS_ATOMS
   pip install -e .
   ```

3. 对照 **conda_list.txt** 中与 pip 相关的包，对缺失或版本不一致的包进行安装或升级。关键包及本项目实测版本如下（节选自 conda_list.txt，仅供参考）：

   | 包名 | 用途 | 实测版本 |
   |------|------|----------|
   | gui-agents | Agent S3 核心库 | 0.3.1 |
   | openai | 主模型 / Grounding API 调用 | 2.8.1 |
   | pyautogui | 鼠标键盘自动化 | 0.9.54 |
   | pyperclip | 剪贴板（Phase 脚本中替代 write） | 1.11.0 |
   | opencv-contrib-python | 图像处理（utils 配准、坐标转换） | 4.10.0.84 |
   | pandas | 数据处理（data/、match 等） | 2.3.3 |
   | numpy | 数值计算 | 2.2.6 |
   | paddlepaddle / paddleocr | OCR 等（原 Agent-S 依赖） | 3.2.2 / 3.3.2 |
   | pywinauto / pywin32 | Windows GUI 自动化（原仓库 Windows 依赖） | 0.6.9 / 311 |
   | pytesseract | 文字识别（原仓库） | 0.3.13 |
   | scikit-learn | match.py 中最近邻等 | 1.7.2 |
   | fastapi / uvicorn | 原仓库服务相关 | 0.121.3 / 0.38.0 |
   | backoff / tiktoken / anthropic / google-genai / together | 原仓库多模型与工具 | 见 conda_list.txt |

4. 若某包缺失，可直接安装，例如：

   ```bash
   pip install pyperclip opencv-contrib-python
   ```

#### 方式二：从 requirements.txt 起步

原仓库依赖见 **requirements.txt**（无版本钉死）。在已激活的 Conda 环境中执行：

```bash
cd D:\code\python\AgentS_ATOMS
pip install -r requirements.txt
pip install -e .
```

注意：**requirements.txt** 中未列出本项目 Phase 脚本额外依赖，需**手动补充**安装，例如：

```bash
pip install pyperclip opencv-contrib-python
```

（原仓库使用 `opencv-python` 亦可，本项目环境中为 `opencv-contrib-python`。）

### 5.5 Windows 平台说明

- 在 **Windows** 下运行需安装 **pywin32** 与 **pywinauto**（Agent-S 的 Windows 支持依赖）。若通过 `pip install -e .` 安装，`setup.py` 已按平台声明，一般会自动安装。
- **conda_list.txt** 中已包含上述两包（版本 311、0.6.9），若复现环境时缺少，请单独安装：

  ```bash
  pip install pywin32 pywinauto
  ```

- **Mac/Linux**：原仓库说明见 **README_agents.md**（如 Mac 需 `pyobjc`，Linux 无额外 GUI 依赖）。

### 5.6 API 与模型配置（参考 README_agents.md）

#### API 密钥与 Base URL（必配，且勿提交仓库）

本项目**不再在代码中写死 API Key**，统一从**环境变量**或 **.env 文件**读取，便于将仓库公开而不会泄露密钥。

**方式一：环境变量**

在终端或系统环境中设置（PowerShell 示例，仅当前会话）：

```powershell
$env:AGENTS_ATOMS_API_KEY = "你的 API Key"
$env:AGENTS_ATOMS_BASE_URL = "https://你的接口地址/v1"
```

若需长期生效，可在 Windows “系统环境变量”中新增 `AGENTS_ATOMS_API_KEY` 与 `AGENTS_ATOMS_BASE_URL`。

**方式二：.env 文件（推荐）**

1. 在项目根目录 `AgentS_ATOMS` 下，将 **.env.example** 复制为 **.env**。
2. 用文本编辑器打开 `.env`，将 `your_api_key_here`、`your-api-endpoint` 替换为你的真实 API Key 与 Base URL，保存。
3. **不要**将 `.env` 提交到 Git（`.gitignore` 已忽略 `.env`）。

`.env` 示例内容：

```
AGENTS_ATOMS_API_KEY=sk-xxxxxxxx
AGENTS_ATOMS_BASE_URL=http://34.13.73.248:3888/v1
```

若已安装 **python-dotenv**，运行 `run_phase1.py`、`run_phase2.py` 或 `test/` 下脚本时会自动加载根目录下的 `.env`；未安装则仅从系统环境变量读取。

未配置时，运行 Phase 脚本会提示“未配置 API”并退出，请按上述任一种方式配置后再运行。

- **主模型与 Grounding 模型**：支持 Azure OpenAI、Anthropic、Gemini、Open Router、vLLM 等，详见 **models.md**；Grounding 模型（如 UI-TARS）的部署与参数见 **README_agents.md** 的 “Grounding Models (Required)” 与 “Grounding Model Dimensions”。
- **屏幕与坐标**：脚本中屏幕分辨率为 1920×1080，grounding 输出为 1000×1000 等，需与所用 Grounding 模型一致；更换分辨率或模型时请同步修改脚本内常量。

### 5.7 路径与任务配置

当前版本已将 `run_phase1.py` / `run_phase2.py` 中的大部分路径文案统一到 `project_paths.py`，并将“每台机器不同”的路径抽离到 `paths_user.py`（本地文件，不提交仓库）。

---

#### 一、你现在真正需要改的文件

1. **复制模板**：将 `paths_user.example.py` 复制为 `paths_user.py`。  
2. **只改 4 个变量**（按你的电脑实际路径）：

- `ATOMS_EXE`：ATOMS 可执行文件路径（如 `D:\ATOMS65\Eragon.exe`）
- `PHASE1_OPEN_DIALOG_DIR`：第一阶段在 Open 对话框中要进入的目录
- `PHASE1_STR_FILENAME`：第一阶段加载的 `.str` 文件名（仅文件名）
- `PHASE2_STR_FILE`：第二阶段要直接打开的结构文件（可用绝对路径，也可相对项目根）

> `paths_user.py` 已加入 `.gitignore`，不会被提交；公开仓库时每位使用者只需保留自己的本机配置。

---

#### 二、`project_paths.py` 的职责（统一管理）

`project_paths.py` 负责两件事：

- **项目内固定路径**（相对仓库根）
  - `utils/bmp`
  - `data/file/xyz`
  - `data/file/xlsx`
  - `data/file/csv`
  - `data/file/txt`
- **生成给 Agent 的任务文案**
  - `build_phase1_subtasks_stage_1()`
  - `build_phase2_subtasks_stage_1()`
  - `build_phase2_subtasks_stage_2()`
  - `build_phase2_subtasks_stage_3()`

这意味着：你不再需要在 `run_phase1.py` / `run_phase2.py` 里手工改一堆绝对路径。

---

#### 三、两阶段脚本现在从哪里取路径

- `run_phase1.py`
  - `SUB_TASKS_STAGE_1 = build_phase1_subtasks_stage_1()`
  - `angle.txt` 读取路径：`PROJECT_ROOT / "utils" / "results" / "angle.txt"`
- `run_phase2.py`
  - `SUB_TASKS_STAGE_1 = build_phase2_subtasks_stage_1()`
  - `SUB_TASKS_STAGE_2 = build_phase2_subtasks_stage_2()`
  - `SUB_TASKS_STAGE_3 = build_phase2_subtasks_stage_3()`

---

#### 四、哪些路径仍可能需要你按项目需求调整

这些路径在代码里是“统一管理”了，但如果你改了业务输入输出习惯，仍需在对应文件改一次：

- `project_paths.py`
  - `PHASE2_ROTATION_ANGLE`（默认 90）
  - `DATA_TRANSACTION_XLSX`、`DATA_TRANSACTION_TXT`、`PROCESSED_CSV`（若文件名变化）
- `data/data.py`
  - 默认读取 `data/file/xyz/untitled.xyz`；若 ATOMS 导出文件名不是 `untitled.xyz`，需改这里
- `utils/match.py`
  - 目标参考图默认 `utils/images/solution/2.png`；如果换参考图，需替换该文件或改 `TGT_PATH`

---

#### 五、给新用户的最小配置步骤（可直接写在仓库说明里）

1. `git clone` 后进入项目根目录。  
2. 复制 `.env.example` 为 `.env`，填写 `AGENTS_ATOMS_API_KEY` 与 `AGENTS_ATOMS_BASE_URL`。  
3. 复制 `paths_user.example.py` 为 `paths_user.py`，填写本机路径。  
4. 运行：
   - `python run_phase1.py`
   - `python run_phase2.py`

这样即可避免“下载后要到处改绝对路径”的问题。

---

## 六、运行方式

- **仅运行第一阶段**：  
  `python run_phase1.py`
- **仅运行第二阶段**：  
  `python run_phase2.py`

两阶段**相互独立**，目前**未**整合为“运行一个文件走完三阶段”；第三阶段流程确定后，再考虑合并为单入口并在此文档中更新说明。

---

## 七、后续计划

- **后续**：实现第三阶段流程，并将 Phase1 + Phase2 + Phase3 整合到同一入口脚本。

---

## 八、致谢与引用

本项目的 Agent 与 GUI 控制能力基于 [simular-ai/Agent-S](https://github.com/simular-ai/Agent-S)（Agent S3）。若在学术或工程中使用其代码或思路，请按原仓库 README 与论文进行引用。

---

*文档最后更新：2026 年 3 月，与当前仓库状态一致。*
