
import docker
import os
import time
from typing import Dict, Any, Optional
import shutil

from src.config.settings.settings import settings
from src.utils.logger import logger

class Sandbox:
    """
    Docker Sandbox Manager
    负责管理 Docker 容器的生命周期，提供安全的技能执行环境。
    """
    def __init__(self):
        self.client = None
        self.containers = {} # container_id -> info
        
        try:
            self.client = docker.from_env()
            logger.info("[Sandbox] Docker client initialized.")
        except Exception as e:
            logger.warning(f"[Sandbox] Docker client initialization failed: {e}")
            logger.warning("[Sandbox] Sandbox will run in MOCK mode (or fail). Please ensure Docker Desktop is running.")

    def is_available(self):
        return self.client is not None

    def build_image(self, skill_name: str, skill_dir: str) -> Optional[str]:
        """
        构建技能的 Docker 镜像
        :param skill_name: 技能名称 (e.g. "qrcode_generator")
        :param skill_dir: 技能目录 (必须包含 Dockerfile)
        :return: image_tag or None
        """
        if not self.is_available():
            return None
            
        tag = f"xingchen-skill-{skill_name.lower()}:latest"
        dockerfile_path = os.path.join(skill_dir, "Dockerfile")
        
        if not os.path.exists(dockerfile_path):
            logger.warning(f"[Sandbox] Dockerfile not found for {skill_name}")
            return None
            
        logger.info(f"[Sandbox] Building image for {skill_name}...")
        try:
            image, logs = self.client.images.build(path=skill_dir, tag=tag, rm=True)
            for chunk in logs:
                if 'stream' in chunk:
                    logger.debug(chunk['stream'].strip())
            logger.info(f"[Sandbox] Image built successfully: {tag}")
            return tag
        except Exception as e:
            logger.error(f"[Sandbox] Build failed: {e}", exc_info=True)
            return None

    def run_skill(self, image_tag: str, command: str, env: Dict[str, str] = None, timeout: int = None) -> Dict[str, Any]:
        """
        在容器中运行一次性命令
        """
        if not self.is_available():
            return {"error": "Docker not available"}
            
        if timeout is None:
            timeout = settings.SANDBOX_TIMEOUT

        logger.info(f"[Sandbox] Running {command} in {image_tag}...")
        try:
            container = self.client.containers.run(
                image_tag,
                command=command,
                environment=env or {},
                detach=True,
                # 限制资源
                mem_limit=settings.SANDBOX_MEM_LIMIT,
                nano_cpus=settings.SANDBOX_CPU_LIMIT, 
                network_mode="none" # 默认无网络，安全第一 (需要联网则由 Skill 声明)
            )
            
            # 等待结束或超时
            start_time = time.time()
            while container.status in ['created', 'running']:
                container.reload()
                if time.time() - start_time > timeout:
                    container.kill()
                    return {"error": "Timeout"}
                time.sleep(0.1)
                
            logs = container.logs().decode('utf-8')
            exit_code = container.attrs['State']['ExitCode']
            
            container.remove()
            
            return {
                "exit_code": exit_code,
                "logs": logs
            }
            
        except Exception as e:
            return {"error": str(e)}

# Global Instance
sandbox = Sandbox()
