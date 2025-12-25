"""
微信消息采集器
使用 uiautomation 控制微信 PC 客户端抓取消息
"""

import json
import time
import random
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

import uiautomation as auto

from src.config import Config


class Message:
    """消息数据结构"""

    def __init__(
        self,
        sender: str,
        time: str,
        content: str,
        group: str = ""
    ):
        self.sender = sender
        self.time = time
        self.content = content
        self.group = group

    def to_dict(self) -> Dict[str, str]:
        return {
            "sender": self.sender,
            "time": self.time,
            "content": self.content,
            "group": self.group
        }

    def __repr__(self):
        return f"[{self.time}] {self.sender}: {self.content}"


class CheckpointManager:
    """检查点管理器 - 记录上次抓取位置"""

    def __init__(self, checkpoint_path: str):
        self.checkpoint_path = checkpoint_path
        self.checkpoints: Dict[str, Dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        """加载检查点文件"""
        path = Path(self.checkpoint_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self.checkpoints = json.load(f)

    def save(self) -> None:
        """保存检查点"""
        Path(self.checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoints, f, ensure_ascii=False, indent=2)

    def get_anchor(self, group_name: str) -> Optional[Dict[str, str]]:
        """获取指定群的锚点"""
        return self.checkpoints.get(group_name)

    def update_anchor(self, group_name: str, last_message_time: str, last_message_content: str) -> None:
        """更新指定群的锚点"""
        self.checkpoints[group_name] = {
            "last_message_time": last_message_time,
            "last_message_content": last_message_content,
            "updated_at": datetime.now().isoformat()
        }
        self.save()


class WeChatCollector:
    """微信消息采集器主类"""

    def __init__(self, config: Config):
        self.config = config
        self.wechat_config = config.wechat
        self.groups = config.groups
        self.checkpoint_manager = CheckpointManager(config.checkpoint['path'])

        # 随机延迟设置
        self.delay_min = self.wechat_config.get('random_delay_min', 1)
        self.delay_max = self.wechat_config.get('random_delay_max', 3)

    def _random_delay(self) -> None:
        """随机延迟，模拟人类操作"""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)

    def _connect_wechat(self) -> auto.Control:
        """连接微信窗口"""
        window_title = self.wechat_config.get('window_title', '微信')

        # 查找微信窗口
        wechat_window = auto.WindowControl(searchDepth=5, Name=window_title)
        if not wechat_window.Exists(maxSearchSeconds=10):
            raise RuntimeError("未找到微信窗口，请确保微信 PC 客户端已启动")

        # 确保窗口在前台
        wechat_window.SetFocus()
        return wechat_window

    def _scroll_to_top(self, chat_control: auto.Control) -> None:
        """滚动到顶部加载更多消息"""
        max_scroll = self.wechat_config.get('max_scroll_attempts', 50)
        scroll_pause = self.wechat_config.get('scroll_pause', 0.5)

        for _ in range(max_scroll):
            # 尝试点击滚动条向上
            scroll_bar = chat_control.ScrollBarControl()
            if scroll_bar.Exists():
                # 点击滚动条上部来向上滚动
                rect = scroll_bar.BoundingRectangle
                x = rect.left + rect.width() // 2
                y = rect.top + 10
                auto.Click(x, y)
                time.sleep(scroll_pause)
            else:
                # 没有滚动条，可能已经到顶
                break

    def _extract_message_from_element(self, element: auto.Control, group_name: str) -> Optional[Message]:
        """从 UI 元素中提取消息"""
        try:
            # 消息元素通常包含发送者和内容
            # 这里需要根据实际 UI 结构调整
            # 常见的结构是：列表项包含发送者名称和消息内容

            # 尝试获取文本
            name = element.Name or ""
            description = element.GetValuePattern().Value if element.GetValuePattern() else ""

            # 简单解析 - 实际需要根据微信 UI 结构调整
            # 微信消息通常格式: "时间\n发送者: 消息内容"
            lines = name.split('\n') if name else []

            if len(lines) >= 2:
                time_str = lines[0]
                sender_content = lines[1]

                if ': ' in sender_content:
                    sender, content = sender_content.split(': ', 1)
                    return Message(
                        sender=sender.strip(),
                        time=time_str.strip(),
                        content=content.strip(),
                        group=group_name
                    )

            return None
        except Exception:
            return None

    def _find_chat_list(self, wechat_window: auto.Control) -> Optional[auto.Control]:
        """找到聊天消息列表区域"""
        # 聊天列表通常在消息区域
        # 需要根据实际 UI 结构调整选择器
        try:
            # 尝试查找消息列表
            chat_list = wechat_window.ListControl(searchDepth=10, Name="消息")
            if chat_list.Exists():
                return chat_list

            # 备选方案：查找任何列表控件
            chat_list = wechat_window.ListControl(searchDepth=10)
            if chat_list.Exists():
                return chat_list

            return None
        except Exception:
            return None

    def collect_from_group(self, group_name: str) -> List[Message]:
        """从指定群聊采集消息"""
        print(f"开始采集群: {group_name}")

        messages: List[Message] = []

        try:
            # 连接微信
            wechat_window = self._connect_wechat()
            self._random_delay()

            # 查找搜索框并搜索群组
            search_box = wechat_window.EditControl(searchDepth=8, Name="搜索")
            if search_box.Exists():
                search_box.Click()
                self._random_delay()
                search_box.SetValue(group_name)
                self._random_delay()

                # 点击搜索结果中的群组
                # 需要根据实际 UI 结构调整
                result = wechat_window.ListItemControl(searchDepth=10, Name=group_name)
                if result.Exists():
                    result.Click()
                    self._random_delay()

            # 找到聊天列表
            chat_list = self._find_chat_list(wechat_window)
            if not chat_list:
                print(f"未找到群 {group_name} 的聊天列表")
                return messages

            # 获取锚点
            anchor = self.checkpoint_manager.get_anchor(group_name)

            # 滚动并提取消息
            max_scroll = self.wechat_config.get('max_scroll_attempts', 50)
            scroll_pause = self.wechat_config.get('scroll_pause', 0.5)
            found_anchor = anchor is None  # 如果没有锚点，采集所有消息

            for scroll_attempt in range(max_scroll):
                # 获取当前可见的消息元素
                message_items = chat_list.GetChildren()

                for item in message_items:
                    message = self._extract_message_from_element(item, group_name)
                    if message:
                        # 检查是否到达锚点
                        if anchor and not found_anchor:
                            if (message.time == anchor.get('last_message_time') and
                                message.content == anchor.get('last_message_content')):
                                found_anchor = True
                                break

                        if not found_anchor or scroll_attempt == 0:
                            messages.append(message)

                if found_anchor:
                    break

                # 向上滚动
                self._scroll_to_top(chat_list)
                self._random_delay()

            # 消息按时间倒序（最新的在前），需要反转
            messages.reverse()

            # 更新锚点
            if messages:
                last_message = messages[-1]
                self.checkpoint_manager.update_anchor(
                    group_name,
                    last_message.time,
                    last_message.content
                )

            print(f"群 {group_name} 采集完成，共 {len(messages)} 条消息")

        except Exception as e:
            print(f"采集群 {group_name} 时出错: {e}")

        return messages

    def collect_all_groups(self) -> Dict[str, List[Message]]:
        """从所有配置群聊采集消息"""
        all_messages: Dict[str, List[Message]] = {}

        for group_name in self.groups:
            messages = self.collect_from_group(group_name)
            all_messages[group_name] = messages
            self._random_delay()  # 群之间随机延迟

        return all_messages


if __name__ == "__main__":
    # 测试采集器
    from src.config import load_config

    config = load_config("./config.yaml")
    collector = WeChatCollector(config)

    # 测试采集单个群
    messages = collector.collect_from_group(config.groups[0] if config.groups else "测试群")
    print(f"采集到 {len(messages)} 条消息")
    for msg in messages[:5]:
        print(msg)
