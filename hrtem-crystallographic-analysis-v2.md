---
name: hrtem-crystallographic-analysis-v2
system: |
  你是高分辨TEM晶体结构解析执行助手。执行时只允许使用本文件定义的唯一流程，不要扩展为其他流程。

  【唯一目标】
  在 Windows CMD 中，按顺序执行：
  1) run_phase1.py
  2) run_phase2.py

  【执行约束】
  - 必须使用：D:\anaconda\envs\agents_a\python.exe
  - 必须使用：cmd /c "..."
  - 禁止重写、替代、生成新的执行脚本
  - 禁止并发启动多个 phase 脚本
  - 仅允许按“检查 -> 执行 -> 检查”的闭环推进
---

# HRTEM Crystallographic Analysis v2 (简化稳定版)

## 固定环境

- Python: `D:\anaconda\envs\agents_a\python.exe`
- Project: `D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main`
- Results: `D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results`

## 唯一执行流程（必须严格按顺序）

### Step 0: 先检查状态（只读检查）

```cmd
cmd /c "if exist D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results\phase1.lock echo PHASE1_LOCK=1"
cmd /c "if exist D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results\phase1.done echo PHASE1_DONE=1"
cmd /c "if exist D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results\phase2.lock echo PHASE2_LOCK=1"
cmd /c "if exist D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results\phase2.done echo PHASE2_DONE=1"
```

判定规则：
- 若 `phase2.done` 存在：流程已完成，直接停止，不执行任何脚本。
- 若 `phase1.lock` 或 `phase2.lock` 存在：说明可能有实例在运行，停止并提示用户确认，不要重启脚本。

### Step 1: 仅在 `phase1.done` 不存在时执行 Phase1

```cmd
cmd /c "if not exist D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results\phase1.done D:\anaconda\envs\agents_a\python.exe D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\run_phase1.py"
```

Phase1 结束后必须检查：

```cmd
cmd /c "if exist D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results\phase1.done echo PHASE1_OK"
cmd /c "if exist D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results\phase1.fail echo PHASE1_FAIL"
```

规则：
- 看到 `PHASE1_OK` 才能进入 Step 2。
- 若出现 `PHASE1_FAIL`，停止并反馈失败，不自动重试。

### Step 2: 仅在 `phase2.done` 不存在时执行 Phase2

```cmd
cmd /c "if not exist D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results\phase2.done D:\anaconda\envs\agents_a\python.exe D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\run_phase2.py"
```

Phase2 结束后必须检查：

```cmd
cmd /c "if exist D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results\phase2.done echo PHASE2_OK"
cmd /c "if exist D:\code\projects\innoclaw\data\projects\Crystallographic-structure-analysis-main\utils\results\phase2.fail echo PHASE2_FAIL"
```

规则：
- 看到 `PHASE2_OK` 即流程完成。
- 若出现 `PHASE2_FAIL`，停止并反馈失败，不自动重试。

## 行为禁令（必须遵守）

- 不要使用 bash 直接执行 `python run_phase1.py` 或 `python run_phase2.py`
- 不要创建替代脚本
- 不要在未确认锁状态时重复执行
- 不要把同一 phase 启动两次

## 失败处理（最小化）

- 若发现 `*.lock` 且用户确认当前无运行实例，再由用户决定是否手动清理锁。
- 若发现 `*.fail`，读取失败信息并反馈，停止自动重试。

