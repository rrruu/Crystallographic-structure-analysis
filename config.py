# -*- coding: utf-8 -*-
"""
API 配置：从环境变量或 .env 文件读取，避免将密钥提交到仓库。
使用前请设置 AGENTS_ATOMS_API_KEY 和 AGENTS_ATOMS_BASE_URL，
或复制 .env.example 为 .env 并填入后保存。
"""
import os

_root = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_root, ".env")


def _load_dotenv_fallback():
    """未安装 python-dotenv 时，手动读取 .env 并写入 os.environ。"""
    if not os.path.isfile(_env_path):
        return
    with open(_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"").strip()
                # 若当前环境变量为空或未设置，则用 .env 中的值
                if key and (key not in os.environ or not os.environ[key].strip()):
                    os.environ[key] = value


# 优先用 python-dotenv 加载 .env；否则用内置解析
try:
    from dotenv import load_dotenv

    load_dotenv(_env_path)
except ImportError:
    _load_dotenv_fallback()

# 若环境变量仍为空，再尝试一次手动加载（兼容 dotenv 未安装或路径问题）
if not os.environ.get("AGENTS_ATOMS_API_KEY") or not os.environ.get(
    "AGENTS_ATOMS_BASE_URL"
):
    _load_dotenv_fallback()

# 本项目使用的 API 配置（主模型与 Grounding 共用同一 base_url + api_key 时可只设这两项）
API_KEY = os.environ.get("AGENTS_ATOMS_API_KEY", "").strip()
BASE_URL = os.environ.get("AGENTS_ATOMS_BASE_URL", "").strip()


def check_api_config(exit_on_missing=True):
    """检查 API 是否已配置；若 exit_on_missing 为 True 且未配置则打印提示并退出。"""
    if API_KEY and BASE_URL:
        return True
    print(
        "错误：未配置 API。请设置环境变量 AGENTS_ATOMS_API_KEY 和 AGENTS_ATOMS_BASE_URL，"
    )
    print("或在项目根目录创建 .env 文件并填入（可参考 .env.example）。")
    if exit_on_missing:
        import sys

        sys.exit(1)
    return False
