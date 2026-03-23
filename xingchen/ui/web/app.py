import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from xingchen.utils.logger import logger
from xingchen.config.settings import settings
from .routes import router

def create_web_app():
    """创建并配置 FastAPI Web 应用"""
    app = FastAPI(title="XingChen-V Web Console")

    # 跨域配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 挂载静态文件
    static_path = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(static_path):
        os.makedirs(static_path, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_path), name="static")

    # 注册路由
    app.include_router(router)

    @app.on_event("startup")
    async def startup_event():
        logger.info("[Web] FastAPI Server started.")

    return app

# Singleton app instance
app = create_web_app()
