"""
消息提取器
从微信 UI 元素中提取结构化消息
"""

import re
from typing import Optional, Tuple, List
from datetime import datetime

import uiautomation as auto


class MessageExtractor:
    """消息提取器 - 从 UI 元素中提取消息"""

    # 系统消息模式（需要过滤）
    SYSTEM_MESSAGE_PATTERNS = [
        r"撤回了一条消息",
        r"拍了拍",
        r"邀请.*加入了群聊",
        r".*修改了群名",
        r".*解散了群聊",
        r".*移除了.*",
        r"防撤回消息",
    ]

    # 消息时间格式
    TIME_PATTERNS = [
        r"\d{2}:\d{2}",           # 14:02
        r"\d{4}-\d{2}-\d{2}",     # 2024-01-01
        r"\d{4}年\d{1,2}月\d{1,2}日",  # 2024年1月1日
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """编译正则表达式"""
        self.system_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.SYSTEM_MESSAGE_PATTERNS
        ]
        self.time_patterns = [
            re.compile(pattern)
            for pattern in self.TIME_PATTERNS
        ]

    def is_system_message(self, text: str) -> bool:
        """判断是否为系统消息"""
        for pattern in self.system_patterns:
            if pattern.search(text):
                return True
        return False

    def extract_time(self, text: str) -> Optional[str]:
        """从文本中提取时间"""
        for pattern in self.time_patterns:
            match = pattern.search(text)
            if match:
                return match.group()
        return None

    def parse_sender_content(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        解析发送者和内容
        格式通常为: "发送者: 消息内容"
        """
        if ': ' in text:
            parts = text.split(': ', 1)
            return parts[0].strip(), parts[1].strip()

        # 备选格式: "发送者 消息内容" (空格分隔)
        parts = text.split(' ', 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()

        return None, text.strip()

    def extract_message(self, element: auto.Control) -> Optional[dict]:
        """
        从 UI 元素中提取完整消息

        Args:
            element: uiautomation 控件元素

        Returns:
            消息字典 或 None
        """
        try:
            # 获取元素名称（通常包含消息内容）
            name = element.Name or ""

            if not name:
                return None

            # 过滤系统消息
            if self.is_system_message(name):
                return None

            # 提取时间
            time_str = self.extract_time(name)

            # 解析发送者和内容
            sender, content = self.parse_sender_content(name)

            if not sender or not content:
                return None

            return {
                "sender": sender,
                "time": time_str,
                "content": content
            }

        except Exception:
            return None

    def extract_batch(self, elements: List[auto.Control]) -> List[dict]:
        """
        批量提取消息

        Args:
            elements: uiautomation 控件元素列表

        Returns:
            消息字典列表
        """
        messages = []
        for element in elements:
            msg = self.extract_message(element)
            if msg:
                messages.append(msg)
        return messages


def create_message_element_patterns() -> dict:
    """
    创建消息元素选择器模式
    用于适配不同版本的微信
    """
    return {
        # 微信版本 -> 选择器配置
        "3.9.x": {
            "chat_list": {"searchDepth": 10, "ControlType": "ListControl"},
            "message_item": {"searchDepth": 5, "ControlType": "ListItemControl"},
            "sender": {"searchDepth": 2, "Name": None},  # 根据实际结构调整
            "content": {"searchDepth": 2, "Name": None},
        },
        "3.8.x": {
            "chat_list": {"searchDepth": 12, "ControlType": "ListControl"},
            "message_item": {"searchDepth": 6, "ControlType": "ListItemControl"},
        }
    }


if __name__ == "__main__":
    # 测试提取器
    extractor = MessageExtractor()

    test_texts = [
        "14:02 老王: 出两台14pm 256 紫色 电池90 5800到付",
        "张三 收一台iPhone 13 256G 预算3000",
        "李四撤回了一条消息",
        "14:05 王五: 收到货了，谢谢",
    ]

    for text in test_texts:
        if extractor.is_system_message(text):
            print(f"系统消息，跳过: {text}")
            continue

        sender, content = extractor.parse_sender_content(text)
        time_str = extractor.extract_time(text)

        print(f"原始: {text}")
        print(f"  时间: {time_str}")
        print(f"  发送者: {sender}")
        print(f"  内容: {content}")
        print()
