"""
工具模块
"""

import json
import os
from typing import Optional, Dict, Any
import logging

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or "config.json"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        # 首先尝试从环境变量加载配置
        config = {}
        
        # 尝试从环境变量加载关键配置
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            config["openai_api_key"] = openai_key
            
        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            config["log_level"] = log_level
            
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value
        self._save_config()
    
    def _save_config(self) -> None:
        """保存配置文件"""
        try:
            # 不保存从环境变量获取的配置到文件中
            save_config = {k: v for k, v in self.config.items() 
                          if k not in ['openai_api_key']}
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(save_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")


def setup_logger(name: str, log_file: str, level: int = 20) -> 'logging.Logger':
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别
        
    Returns:
        日志记录器对象
    """
    import logging
    # 从标准库导入RotatingFileHandler
    from logging.handlers import RotatingFileHandler
    # 如果需要更高级的功能，可以考虑使用concurrent_log_handler
    # from concurrent_log_handler import ConcurrentRotatingFileHandler
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger