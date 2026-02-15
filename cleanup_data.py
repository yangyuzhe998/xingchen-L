import os
import shutil
import glob

def cleanup():
    """危险清理脚本：会删除本项目的运行数据与缓存。

    注意：此脚本会删除 memory_data、storage、logs 等目录，可能导致“记忆/知识库”不可恢复。
    仅在你明确需要重置环境/清空运行数据时使用。

    建议：在执行前先备份 src/memory_data/ 与 storage/。
    """
    # 1. Defined Targets
    targets = [
        "src/bridge",
        "src/memory_data",
        "storage",
        "logs",
        "minecraft_server",
        "node_modules",
        "debug_log_2.txt",
        "setup_mc_server.py"
    ]
    
    print("--- Cleaning up Project Data ---")
    
    # 2. Delete Directories/Files
    for target in targets:
        if os.path.exists(target):
            try:
                if os.path.isdir(target):
                    shutil.rmtree(target)
                    print(f"[Deleted] Directory: {target}")
                else:
                    os.remove(target)
                    print(f"[Deleted] File: {target}")
            except Exception as e:
                print(f"[Error] Failed to delete {target}: {e}")
        else:
            print(f"[Skipped] Not found: {target}")

    # 3. Recursive __pycache__ Cleanup
    print("\n--- Cleaning up __pycache__ ---")
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                path = os.path.join(root, d)
                try:
                    shutil.rmtree(path)
                    print(f"[Deleted] Cache: {path}")
                except Exception as e:
                    print(f"[Error] Failed to delete {path}: {e}")

if __name__ == "__main__":
    cleanup()
