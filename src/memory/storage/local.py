import json
import os

class JsonStorage:
    """
    JSON 文件存储服务 (长期记忆)
    """
    def __init__(self, file_path):
        self.file_path = file_path
        self._ensure_dir()
        self._dirty = False # Dirty Check Flag

    def _ensure_dir(self):
        if os.path.dirname(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def load(self):
        self._dirty = False
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Memory] JSON 加载失败: {e}")
            return []

    def save(self, data, force=False):
        # 注意: data 是外部传入的，JsonStorage 本身不持有 state (或者说 state 由调用者管理)
        # 这是一个设计上的妥协。为了支持 Dirty Check，我们假设只有当调用 save 时才意味着数据变了。
        # 但这并不严谨，因为 data 是一直在外部变的。
        # 更好的做法是：JsonStorage 持有 data，并提供 add/update 方法。
        # 不过鉴于目前架构，我们暂且认为：如果调用了 save，就说明调用者认为数据变了。
        # 可以在 MemoryService 层维护 dirty flag。
        
        # 但为了配合 force_save_all 的语义，我们在这里还是做一个简单的 check
        # 如果调用 save(data)，就写入。
        
        # 修正：JsonStorage 只是一个 Storage Provider，它不持有业务对象。
        # 所以 dirty check 应该在 MemoryService (持有 long_term list) 中做。
        # 这里只负责写文件。
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Memory] JSON 保存失败: {e}")
