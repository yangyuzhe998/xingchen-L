from typing import Optional, Dict, Any, List
from ...utils.llm_client import LLMClient
from ...memory.memory_core import Memory
from ..bus.event_bus import event_bus
from ...config.settings.settings import settings
from ...memory.managers.deep_clean_manager import DeepCleanManager
import threading
import time
from ...utils.logger import logger

# 引入新组件
from .components.compressor import Compressor
from .components.reasoner import Reasoner
from .components.context import ContextManager

class Navigator:
    """
    S脑 (Slow Brain) / 慢脑
    负责：长期规划、深度分析、反思总结。
    特点：异步运行，不直接控制输出，通过 Suggestion Board 给 Driver 提建议。
    模型：DeepSeek (模拟 R1 推理模式)
    """
    def __init__(self, name="Navigator", memory=None):
        self.name = name
        # S脑使用 DeepSeek
        self.llm = LLMClient(provider="deepseek")
        # 强制切换为 deepseek-reasoner
        self.llm.model = settings.S_BRAIN_MODEL
        self.memory = memory if memory else Memory()
        self.suggestion_board = []
        self._lock = threading.Lock() # 初始化线程锁
        self._compression_pending = False # [New] 压缩任务排队标志
        
        # 初始化组件
        self.context_manager = ContextManager(self.memory)
        self.compressor = Compressor(self.llm, self.memory)
        self.reasoner = Reasoner(self.llm, self.memory, self.context_manager)
        
        # 初始化深度维护管理器
        # 注意：这里会启动一个后台线程进行计时
        self.deep_clean_manager = DeepCleanManager(self.memory)
        
        logger.info(f"[{self.name}] 初始化完成。模型: DeepSeek (R1)。组件已加载。")

    def request_diary_generation(self):
        """
        [New] 请求生成日记 (线程安全 & 任务排队)
        如果当前没有任务在运行，立即开始。
        如果已有任务在运行，标记 pending，当前任务结束后会自动再次运行。
        """
        # 尝试获取锁
        if self._lock.acquire(blocking=False):
            # 成功获取锁，说明当前空闲，启动新线程
            self._lock.release() # 释放锁，让工作线程去获取
            threading.Thread(target=self._run_compression_loop, daemon=True).start()
        else:
            # 锁被占用，说明正在运行，标记 pending
            self._compression_pending = True
            logger.info(f"[{self.name}] 压缩任务正在运行，新请求已加入队列 (Pending)...")

    def _run_compression_loop(self):
        """
        [New] 压缩任务循环
        执行 generate_diary，并在结束后检查 pending 标志。
        """
        while True:
            # 尝试获取锁 (理应成功，除非极端并发情况)
            if not self._lock.acquire(blocking=False):
                return

            try:
                # 清除 pending 标志 (我们正在处理了)
                self._compression_pending = False
                
                # 执行实际逻辑
                self.generate_diary()
                
            finally:
                self._lock.release()
            
            # 检查是否在运行期间又有新请求
            if not self._compression_pending:
                break
            else:
                logger.info(f"[{self.name}] 检测到排队任务，立即重新执行压缩...")
                # 继续循环

    def generate_diary(self):
        """
        生成 AI 日记 (核心逻辑)
        注意：现在由 _run_compression_loop 调用，不需要再自己管理锁
        """
        # [延迟执行]
        # 让主线程先完成当前的对话响应，避免 LLM 请求抢占带宽/计算资源
        time.sleep(settings.NAVIGATOR_DELAY_SECONDS) 
        
        start_time = time.time()
        logger.info(f"[{self.name}] 开始双重记忆压缩任务...")
        
        # 获取最近的事件流
        events = event_bus.get_latest_cycle(limit=settings.NAVIGATOR_EVENT_LIMIT) 
        if not events:
            logger.info(f"[{self.name}] 事件不足，跳过压缩。")
            return

        diary_response = None
        
        try:
            # 1. 准备上下文 (委托给 ContextManager)
            script, time_context, current_psyche = self.context_manager.prepare_compression_context(events)

            # 2. 执行原子任务 (委托给 Compressor)
            # === 任务 1: 趣味日记 (Creative) ===
            diary_response = self.compressor.generate_creative_diary(current_psyche, time_context, script)

            # === 任务 2: 工程记忆 (Engineering/Fact) ===
            self.compressor.extract_facts(script)

            # === 任务 3: 认知图谱构建 (Cognitive Graph) ===
            self.compressor.build_cognitive_graph(current_psyche, script)

            # === 任务 4: 别名提取 (Alias Extraction) ===
            self.compressor.extract_aliases(script)

            # 3. 清理短期记忆 (委托给 Compressor)
            self.compressor.clean_short_term_memory()

            return diary_response
            
        except Exception as e:
            logger.error(f"[{self.name}] [ERROR] 记忆压缩流程异常: {e}", exc_info=True)
            
        finally:
            # [Fix] 无论成功失败，强制持久化所有记忆
            logger.info(f"[{self.name}] 正在持久化记忆...")
            t_save = time.time()
            self.memory.force_save_all()
            logger.info(f"[{self.name}] 记忆压缩完成。耗时: {time.time() - start_time:.2f}s (刷盘: {time.time() - t_save:.2f}s)")


    def analyze_cycle(self):
        """
        基于 EventBus 的周期性分析 (R1 模式)
        委托给 Reasoner 组件
        """
        return self.reasoner.analyze_cycle()

    # 保留旧接口以兼容（或者直接废弃）
    def analyze(self, current_input):
        return self.analyze_cycle()
