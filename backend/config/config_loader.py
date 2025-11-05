# backend/config/config_loader.py
import yaml
from pathlib import Path

def load_config(config_name: str) -> dict:
    """
    讀取 config/*.yml 設定檔並回傳成 Python 字典
    """
    config_path = Path(__file__).parent / f"{config_name}.yml"
    if not config_path.exists():
        raise FileNotFoundError(f"設定檔 {config_name}.yml 不存在")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config
