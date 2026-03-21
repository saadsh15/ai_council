import os
import yaml
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class ProviderConfig(BaseModel):
    name: str
    model: str
    api_key: Optional[str] = None

class AppConfig(BaseModel):
    default_provider: str = "ollama"
    default_model: str = "qwen3-coder:30b"
    threshold: float = 80.0
    timeout: int = 30
    verbose: bool = False
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    user_preferences: str = "" # New field for RAG-based tailoring

import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

CONFIG_PATH = Path(get_resource_path("config/default_config.yaml"))

def load_config() -> AppConfig:
    if not CONFIG_PATH.exists():
        # Create default config if not exists
        config = AppConfig()
        # Add default Ollama provider
        config.providers["ollama"] = ProviderConfig(name="ollama", model="qwen3-coder:30b")
        save_config(config)
        return config
    
    with open(CONFIG_PATH, "r") as f:
        data = yaml.safe_load(f)
        if data is None:
            return AppConfig()
        return AppConfig(**data)

def save_config(config: AppConfig):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config.model_dump(), f)

def get_api_key(provider: str) -> Optional[str]:
    # Try environment variable first (e.g., GEMINI_API_KEY)
    env_key = f"{provider.upper()}_API_KEY"
    key = os.getenv(env_key)
    if key:
        return key
    
    # Try from config
    config = load_config()
    if provider in config.providers:
        return config.providers[provider].api_key
    return None
