import os
import sys
from dotenv import load_dotenv

def check_environment():
    print("正在检查环境配置...")
    
    # 1. Check Python Version
    print(f"Python 版本: {sys.version.split()[0]}")
    if sys.version_info < (3, 8):
        print("错误: Python 版本需要 3.8 或更高。")
        return False

    # 2. Check .env file
    if not os.path.exists(".env"):
        print("警告: 未找到 .env 文件。请复制 .env.example 并配置环境变量。")
        # Don't fail here, maybe env vars are set in system
    else:
        print(".env 文件: 已存在")
        load_dotenv()

    # 3. Check Critical Variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("警告: OPENAI_API_KEY 未配置或为默认值。")
    else:
        print("OPENAI_API_KEY: 已配置 (掩码: " + api_key[:4] + "..." + api_key[-4:] + ")")

    print("\n环境检查完成。")
    return True

if __name__ == "__main__":
    check_environment()
