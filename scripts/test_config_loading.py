
import sys
import os
import time

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config.settings.settings import settings
from src.memory.memory_core import Memory
from src.core.navigator.core import Navigator

def test_config_loading():
    print("Testing Configuration Loading...")
    
    # Check Settings
    print(f"SHORT_TERM_MAX_COUNT: {settings.SHORT_TERM_MAX_COUNT} (Expected: 30)")
    print(f"NAVIGATOR_DELAY_SECONDS: {settings.NAVIGATOR_DELAY_SECONDS} (Expected: 5)")
    print(f"NAVIGATOR_EVENT_LIMIT: {settings.NAVIGATOR_EVENT_LIMIT} (Expected: 50)")
    
    assert settings.SHORT_TERM_MAX_COUNT == 30
    assert settings.NAVIGATOR_DELAY_SECONDS == 5
    assert settings.NAVIGATOR_EVENT_LIMIT == 50
    
    print("✅ Settings.py loaded correctly.")

    # Check Memory Usage
    memory = Memory()
    # We can't easily check the internal logic without mocking, but if it initialized without error, that's a good sign.
    # We can check if settings are accessible inside memory instance if we really wanted to, 
    # but the code uses `settings.SHORT_TERM_MAX_COUNT` directly in methods.
    
    print("✅ Memory module initialized successfully (Settings imported).")

    # Check Navigator Usage
    navigator = Navigator(memory=memory)
    print("✅ Navigator module initialized successfully (Settings imported).")
    
    print("\nAll configuration tests passed!")

if __name__ == "__main__":
    test_config_loading()
