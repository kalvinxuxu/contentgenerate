"""
多 Agent 文案生成系统 - 主程序入口

Usage:
    python main.py generate --topic "AI 写作" --audience "自媒体创作者" --platform xiaohongshu
    python main.py config
    python main.py research --topic "时间管理" --audience "职场人士"
    python main.py review draft.txt
"""

# 首先加载环境变量（必须在最前面）
from dotenv import load_dotenv
load_dotenv()

from src.cli import main

if __name__ == "__main__":
    main()
