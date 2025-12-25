"""
消息采集模块
负责从微信群聊中抓取消息
"""

from .collector import WeChatCollector, Message, CheckpointManager
from .extractor import MessageExtractor

__all__ = ['WeChatCollector', 'Message', 'CheckpointManager', 'MessageExtractor']
