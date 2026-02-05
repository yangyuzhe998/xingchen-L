
import sys
import os
import argparse
import uvicorn
import asyncio
from src.utils.logger import logger

# Add project root to sys.path
# We need to go up one level from src/ to the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def start_cli():
    """Start Debug CLI Mode"""
    from src.core.driver.engine import Driver
    from src.core.navigator.engine import Navigator
    from src.psyche import psyche_engine
    from src.memory.memory_core import Memory
    from src.core.managers.cycle_manager import CycleManager
    from src.ui.debug_app import DebugCLI

    logger.info("Initializing components for CLI mode...")
    
    memory = Memory()
    psyche = psyche_engine
    navigator = Navigator(memory=memory)
    memory.set_navigator(navigator)
    driver = Driver(memory=memory)
    cycle_manager = CycleManager(navigator, psyche)
    
    app = DebugCLI()
    
    def handler(content):
        # Sync bridge to driver
        psyche_state = psyche.state
        driver.think(content, psyche_state=psyche_state)

    app.set_input_handler(handler)
    
    try:
        app.run()
    finally:
        cycle_manager.running = False
        print("System Shutdown.")

def start_web():
    """Start Web Server Mode"""
    from src.core.driver.engine import Driver
    from src.core.navigator.engine import Navigator
    from src.psyche import psyche_engine
    from src.memory.memory_core import Memory
    from src.core.managers.cycle_manager import CycleManager
    from src.ui.web_app import web_ui
    
    logger.info("Initializing components for Web mode...")
    
    # Initialize Core Components
    memory = Memory()
    psyche = psyche_engine
    navigator = Navigator(memory=memory)
    memory.set_navigator(navigator)
    driver = Driver(memory=memory)
    cycle_manager = CycleManager(navigator, psyche)
    
    # Bind Web UI handler
    async def handler(content):
        psyche_state = psyche.state
        # Run in thread pool to avoid blocking async loop
        await asyncio.to_thread(driver.think, content, psyche_state=psyche_state)

    web_ui.set_input_handler(handler)
    
    logger.info("Starting Uvicorn Server...")
    print("\n🌐 Web UI available at: http://127.0.0.1:8000\n")
    
    # Start Uvicorn
    # Note: reload=False for production stability
    uvicorn.run(web_ui.app, host="127.0.0.1", port=8000, log_level="info")

def main():
    parser = argparse.ArgumentParser(description="XingChen-V Launcher")
    parser.add_argument("mode", nargs="?", choices=["cli", "web"], default="cli", help="Launch mode (cli or web)")
    
    args = parser.parse_args()
    
    if args.mode == "web":
        start_web()
    else:
        start_cli()

if __name__ == "__main__":
    main()
