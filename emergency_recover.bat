@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM =========================================================
REM emergency_recover.bat
REM 一键恢复：急停 Python/ATOMS + 清理 Phase 状态文件
REM 用法：
REM   1) emergency_recover.bat
REM   2) emergency_recover.bat "D:\code\projects\AuraID\data\projects\Crystallographic-structure-analysis"
REM =========================================================

chcp 65001 >nul
echo.
echo [恢复] 开始执行紧急恢复...

REM 1) 确定项目根目录（优先使用传入参数）
set "PROJECT_ROOT=%~dp0"
if not "%~1"=="" set "PROJECT_ROOT=%~1"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

set "RESULTS_DIR=%PROJECT_ROOT%\utils\results"

echo [信息] PROJECT_ROOT = %PROJECT_ROOT%
echo [信息] RESULTS_DIR  = %RESULTS_DIR%
echo.

REM 2) 急停常见进程（GUI 自动化最容易失控）
echo [步骤1/3] 正在终止可能残留的进程...
taskkill /F /IM python.exe >nul 2>nul
if %errorlevel%==0 (
  echo   - 已尝试终止 python.exe
) else (
  echo   - 未发现 python.exe 或无需终止
)

taskkill /F /IM Eragon.exe >nul 2>nul
if %errorlevel%==0 (
  echo   - 已尝试终止 Eragon.exe
) else (
  echo   - 未发现 Eragon.exe 或无需终止
)
echo.

REM 3) 清理 lock/done/fail 状态文件
echo [步骤2/3] 正在清理 phase 状态文件...
if exist "%RESULTS_DIR%" (
  for %%F in (phase1.lock phase2.lock phase1.done phase2.done phase1.fail phase2.fail) do (
    if exist "%RESULTS_DIR%\%%F" (
      del /Q "%RESULTS_DIR%\%%F" >nul 2>nul
      if exist "%RESULTS_DIR%\%%F" (
        echo   - 清理失败: %%F
      ) else (
        echo   - 已清理: %%F
      )
    ) else (
      echo   - 不存在: %%F
    )
  )
) else (
  echo   - 警告: 结果目录不存在，跳过状态文件清理
)
echo.

REM 4) 回显当前残留进程，帮助确认恢复状态
echo [步骤3/3] 当前进程状态检查:
echo --- python.exe ---
tasklist | findstr /I "python.exe"
if errorlevel 1 echo   (无)
echo --- Eragon.exe ---
tasklist | findstr /I "Eragon.exe"
if errorlevel 1 echo   (无)
echo.

echo [完成] 紧急恢复已执行完毕。
echo [建议] 在 InnoClaw/AuraID 中新开会话再执行 skill。
echo.
pause
endlocal
