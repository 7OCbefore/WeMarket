"""
配置加载模块
负责读取和解析 config.yaml 配置文件
"""

import os
import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path


class Config:
    """配置管理类"""

    def __init__(self, config_path: str = "./config.yaml"):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

    @property
    def llm(self) -> Dict[str, Any]:
        """LLM API 配置"""
        return self._config.get('llm', {})

    @property
    def wechat(self) -> Dict[str, Any]:
        """微信配置"""
        return self._config.get('wechat', {})

    @property
    def groups(self) -> List[str]:
        """目标群组列表"""
        return self._config.get('groups', [])

    @property
    def database(self) -> Dict[str, Any]:
        """数据库配置"""
        return self._config.get('database', {})

    @property
    def reports(self) -> Dict[str, Any]:
        """报表配置"""
        return self._config.get('reports', {})

    @property
    def checkpoint(self) -> Dict[str, Any]:
        """Checkpoint 配置"""
        return self._config.get('checkpoint', {})

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)


def load_config(config_path: str = "./config.yaml") -> Config:
    """加载配置的便捷函数"""
    return Config(config_path)
