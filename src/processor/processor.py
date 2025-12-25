"""
LLM 处理器
使用大语言模型解析聊天消息
"""

import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion

from src.config import Config
from src.collector import Message
from src.processor.prompt import LLM_PROMPT


@dataclass
class TransactionRecord:
    """交易记录数据结构"""
    action: str          # SELL / BUY
    item: str           # 商品名称
    specs: str          # 规格详情
    price: float        # 价格
    quantity: int       # 数量
    raw_text: str       # 原始消息

    # 元数据
    sender: str = ""
    group: str = ""
    message_time: str = ""
    capture_time: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "item": self.item,
            "specs": self.specs,
            "price": self.price,
            "quantity": self.quantity,
            "raw_text": self.raw_text,
            "sender": self.sender,
            "group": self.group,
            "message_time": self.message_time,
            "capture_time": self.capture_time
        }

    def to_db_dict(self) -> Dict[str, Any]:
        """转换为数据库插入格式"""
        return {
            "action": self.action,
            "item_category": self.item,
            "specs": self.specs,
            "price": self.price,
            "quantity": self.quantity,
            "raw_text": self.raw_text,
            "sender_nickname": self.sender,
            "group_name": self.group,
            "message_time": self.message_time,
            "capture_time": self.capture_time
        }


class LLMClient:
    """LLM API 客户端"""

    def __init__(self, config: Config):
        llm_config = config.llm
        self.api_base = llm_config.get('api_base', 'https://api.openai.com/v1')
        self.api_key = llm_config.get('api_key', '')
        self.model = llm_config.get('model', 'gpt-3.5-turbo')
        self.batch_size = llm_config.get('batch_size', 20)
        self.timeout = llm_config.get('timeout', 60)

        # 同步客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            timeout=self.timeout
        )

    def _normalize_price(self, price_str: str) -> float:
        """
        标准化价格单位
        支持: 5k, 5K, 5w, 5W, 5000, 5,000 等
        """
        if isinstance(price_str, (int, float)):
            return float(price_str)

        price_str = str(price_str).strip().lower()

        # 处理 k (千)
        if 'k' in price_str:
            price_str = price_str.replace('k', '').replace(' ', '')
            try:
                return float(price_str) * 1000
            except ValueError:
                return 0.0

        # 处理 w (万)
        if 'w' in price_str:
            price_str = price_str.replace('w', '').replace(' ', '')
            try:
                return float(price_str) * 10000
            except ValueError:
                return 0.0

        # 移除逗号和空格
        price_str = price_str.replace(',', '').replace(' ', '')

        try:
            return float(price_str)
        except ValueError:
            return 0.0

    def _parse_quantity(self, qty_str: str) -> int:
        """解析数量"""
        if isinstance(qty_str, int):
            return qty_str

        qty_str = str(qty_str).strip()

        # 提取数字
        numbers = re.findall(r'\d+', qty_str)
        if numbers:
            return int(numbers[0])

        # 中文数字
        chinese_nums = {'一': 1, '两': 2, '二': 2, '三': 3, '四': 4, '五': 5}
        for cn, num in chinese_nums.items():
            if cn in qty_str:
                return num

        return 1  # 默认数量为1

    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """解析 LLM 响应"""
        try:
            # 尝试直接解析 JSON
            data = json.loads(response)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get('results', data.get('data', []))
            return []
        except json.JSONDecodeError:
            pass

        # 尝试从文本中提取 JSON
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return []

    def _enhance_record(self, record: Dict[str, Any], message: Message) -> TransactionRecord:
        """增强记录，添加额外字段"""
        # 标准化价格
        price = self._normalize_price(record.get('price', 0))

        # 解析数量
        quantity = self._parse_quantity(record.get('quantity', 1))

        return TransactionRecord(
            action=record.get('action', 'UNKNOWN').upper(),
            item=record.get('item', 'Unknown'),
            specs=record.get('specs', ''),
            price=price,
            quantity=quantity,
            raw_text=message.content,
            sender=message.sender,
            group=message.group,
            message_time=message.time,
            capture_time=datetime.now().isoformat()
        )

    def process_batch(self, messages: List[Message]) -> List[TransactionRecord]:
        """
        处理一批消息

        Args:
            messages: 消息列表

        Returns:
            交易记录列表
        """
        if not messages:
            return []

        # 构建输入文本
        input_text = "\n".join(
            f"[{msg.time}] {msg.sender}: {msg.content}"
            for msg in messages
        )

        try:
            # 调用 LLM API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": LLM_PROMPT},
                    {"role": "user", "content": input_text}
                ],
                temperature=0.1,  # 低温度以获得更一致的输出
            )

            # 解析响应
            response_text = response.choices[0].message.content
            raw_records = self._parse_response(response_text)

            # 转换为 TransactionRecord
            records = []
            for record in raw_records:
                # 为每条原始消息创建记录
                # 由于 LLM 可能合并多条消息，我们为第一条消息创建记录
                enhanced = self._enhance_record(record, messages[0])
                records.append(enhanced)

            return records

        except Exception as e:
            print(f"LLM 处理出错: {e}")
            # 返回空列表，消息将被标记为未处理
            return []


class NLPProcessor:
    """NLP 处理器主类"""

    def __init__(self, config: Config):
        self.config = config
        self.llm_client = LLMClient(config)
        self.batch_size = config.llm.get('batch_size', 20)

    def process_messages(self, messages: List[Message]) -> List[TransactionRecord]:
        """
        处理消息列表

        Args:
            messages: 原始消息列表

        Returns:
            交易记录列表
        """
        if not messages:
            return []

        all_records: List[TransactionRecord] = []

        # 分批处理
        for i in range(0, len(messages), self.batch_size):
            batch = messages[i:i + self.batch_size]
            print(f"处理批次 {i // self.batch_size + 1}, "
                  f"消息 {i + 1} - {min(i + self.batch_size, len(messages))}")

            records = self.llm_client.process_batch(batch)
            all_records.extend(records)

        return all_records

    def process_group_messages(self, group_name: str, messages: List[Message]) -> List[TransactionRecord]:
        """
        处理单个群的消息

        Args:
            group_name: 群名称
            messages: 消息列表

        Returns:
            交易记录列表
        """
        # 为消息添加群名称
        for msg in messages:
            if not msg.group:
                msg.group = group_name

        return self.process_messages(messages)


if __name__ == "__main__":
    # 测试处理器
    from src.config import load_config
    from src.collector import Message

    config = load_config("./config.yaml")

    # 模拟测试消息
    test_messages = [
        Message(
            sender="老王",
            time="14:02",
            content="出两台14pm 256 紫色 电池90 5800到付",
            group="测试群"
        ),
        Message(
            sender="张三",
            time="14:05",
            content="收一台iPhone 13 256G 预算3000",
            group="测试群"
        ),
        Message(
            sender="李四",
            time="14:10",
            content="下午好，大家今天有什么行情",
            group="测试群"
        ),
    ]

    processor = NLPProcessor(config)
    records = processor.process_messages(test_messages)

    print(f"\n解析出 {len(records)} 条交易记录:")
    for record in records:
        print(f"  - {record.action}: {record.item} {record.specs} ¥{record.price} x{record.quantity}")
