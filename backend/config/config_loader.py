# backend/config/config_loader.py
import yaml
from pathlib import Path

def load_config(config_name: str) -> dict:
    """
    Load config/*.yml configuration file and return it as a Python dictionary
    """
    config_path = Path(__file__).parent / f"{config_name}.yml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file {config_name}.yml does not exist")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config
