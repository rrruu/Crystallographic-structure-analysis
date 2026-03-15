# -*- coding: utf-8 -*-
"""
API 配置：从环境变量或 .env 文件读取，避免将密钥提交到仓库。
使用前请设置 AGENTS_ATOMS_API_KEY 和 AGENTS_ATOMS_BASE_URL，
或复制 .env.example 为 .env 并填入后保存。
"""
import os

# 若已安装 python-dotenv，则自动加载项目根目录下的 .env
try:
    from dotenv import load_dotenv
    _root = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(_root, ".env"))
except ImportError:
    pass

# 本项目使用的 API 配置（主模型与 Grounding 共用同一 base_url + api_key 时可只设这两项）
API_KEY = os.environ.get("AGENTS_ATOMS_API_KEY", "").strip()
BASE_URL = os.environ.get("AGENTS_ATOMS_BASE_URL", "").strip()


def check_api_config(exit_on_missing=True):
    """检查 API 是否已配置；若 exit_on_missing 为 True 且未配置则打印提示并退出。"""
    if API_KEY and BASE_URL:
        return True
    print("错误：未配置 API。请设置环境变量 AGENTS_ATOMS_API_KEY 和 AGENTS_ATOMS_BASE_URL，")
    print("或在项目根目录创建 .env 文件并填入（可参考 .env.example）。")
    if exit_on_missing:
        import sys
        sys.exit(1)
    return False
