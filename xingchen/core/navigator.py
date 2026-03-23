from typing import Optional, Dict, Any, List
import threading
import time
from xingchen.utils.llm_client import LLMClient
from xingchen.memory.facade import Memory
from xingchen.core.event_bus import event_bus
from xingchen.config.settings import settings
from xingchen.managers.deep_clean import DeepCleanManager
from xingchen.utils.logger import logger

# 引入导航组件 (已扁平化到 navigator_components 目录下)
from .navigator_components.compressor import Compressor
from .navigator_components.reasoner import Reasoner
from .navigator_components.context import ContextManager
from .navigator_components.knowledge_integrator import KnowledgeIntegrator


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
        self._lock = threading.Lock() 
        self._compression_pending = False 
        self._internalization_lock = threading.Lock() 
        
        # 初始化组件
        self.context_manager = ContextManager(self.memory)
        self.compressor = Compressor(self.llm, self.memory)
        self.reasoner = Reasoner(self.llm, self.memory, self.context_manager)
        self.knowledge_integrator = KnowledgeIntegrator(self.llm, self.memory)
        
        # 初始化深度维护管理器
        self.deep_clean_manager = DeepCleanManager(self.memory.service)
        
        logger.info(f"[{self.name}] 初始化完成。模型: {self.llm.model}。组件已加载。")

    def request_diary_generation(self):
        """
        请求生成日记 (线程安全 & 任务排队)
        """
        if self._lock.acquire(blocking=False):
            self._lock.release()
            threading.Thread(target=self._run_compression_loop, daemon=True).start()
        else:
            self._compression_pending = True
            logger.info(f"[{self.name}] 压缩任务正在运行，新请求已加入队列 (Pending)...")

    def request_knowledge_internalization(self):
        """
        请求执行知识内化
        """
        if self._internalization_lock.acquire(blocking=False):
            self._internalization_lock.release()
            threading.Thread(target=self._run_internalization_task, daemon=True).start()
        else:
            logger.info(f"[{self.name}] 知识内化任务正在运行，跳过本次请求。")

    def _run_internalization_task(self):
        """知识内化任务逻辑"""
        with self._internalization_lock:
            # 延迟一点，避免跟日记压缩抢占太多资源
            time.sleep(settings.NAVIGATOR_DELAY_SECONDS + 2) 
            logger.info(f"[{self.name}] 开始知识内化扫描...")
            try:
                # 每次最多处理 3 个文件
                report = self.knowledge_integrator.scan_and_process(limit=3)
                if report:
                    logger.info(f"[{self.name}] 知识内化完成:\n{report}")
            except Exception as e:
                logger.error(f"[{self.name}] 知识内化任务出错: {e}", exc_info=True)

    def _run_compression_loop(self):
        """
        压缩任务循环
        """
        while True:
            if not self._lock.acquire(blocking=False):
                return

            try:
                self._compression_pending = False
                self.generate_diary()
            finally:
                self._lock.release()
            
            if not self._compression_pending:
                break
            else:
                logger.info(f"[{self.name}] 检测到排队任务，立即重新执行压缩...")

    def generate_diary(self):
        """
        生成 AI 日记 (核心逻辑)
        """
        time.sleep(settings.NAVIGATOR_DELAY_SECONDS) 
        
        start_time = time.time()
        logger.info(f"[{self.name}] 开始双重记忆压缩任务...")

        # 执行知识内化
        integration_report = self.knowledge_integrator.scan_and_process(limit=2)
        if integration_report:
            logger.info(f"[{self.name}] 知识内化报告:\n{integration_report}")
        
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
            diary_response = self.compressor.run_compression_tasks_parallel(current_psyche, time_context, script)

            # 3. 清理短期记忆 (委托给 Compressor)
            self.compressor.clean_short_term_memory()

            return diary_response
            
        except Exception as e:
            logger.error(f"[{self.name}] [ERROR] 记忆压缩流程异常: {e}", exc_info=True)
            
        finally:
            # 强制持久化所有记忆
            logger.info(f"[{self.name}] 正在持久化记忆...")
            t_save = time.time()
            self.memory.commit_long_term()
            self.memory.save_cache()
            logger.info(f"[{self.name}] 记忆压缩完成。耗时: {time.time() - start_time:.2f}s (刷盘: {time.time() - t_save:.2f}s)")

    def analyze_cycle(self):
        """
        基于 EventBus 的周期性分析 (R1 模式)
        """
        return self.reasoner.analyze_cycle()

    def analyze(self, current_input):
        """保持向后兼容"""
        return self.analyze_cycle()
