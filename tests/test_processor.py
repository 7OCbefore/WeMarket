"""
单元测试
测试消息解析和数据库操作
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from datetime import datetime


class TestPriceNormalization(unittest.TestCase):
    """测试价格标准化"""

    def test_k_unit(self):
        """测试 k (千) 单位"""
        from src.processor.processor import LLMClient

        client = LLMClient.__new__(LLMClient)

        self.assertEqual(client._normalize_price("5k"), 5000)
        self.assertEqual(client._normalize_price("5.5k"), 5500)
        self.assertEqual(client._normalize_price("10K"), 10000)

    def test_w_unit(self):
        """测试 w (万) 单位"""
        from src.processor.processor import LLMClient

        client = LLMClient.__new__(LLMClient)

        self.assertEqual(client._normalize_price("5w"), 50000)
        self.assertEqual(client._normalize_price("1.5w"), 15000)

    def test_plain_number(self):
        """测试普通数字"""
        from src.processor.processor import LLMClient

        client = LLMClient.__new__(LLMClient)

        self.assertEqual(client._normalize_price("5800"), 5800)
        self.assertEqual(client._normalize_price("5,000"), 5000)

    def test_invalid_price(self):
        """测试无效价格"""
        from src.processor.processor import LLMClient

        client = LLMClient.__new__(LLMClient)

        self.assertEqual(client._normalize_price("暂无"), 0.0)


class TestQuantityParsing(unittest.TestCase):
    """测试数量解析"""

    def test_numeric_quantity(self):
        """测试数字数量"""
        from src.processor.processor import LLMClient

        client = LLMClient.__new__(LLMClient)

        self.assertEqual(client._parse_quantity("2"), 2)
        self.assertEqual(client._parse_quantity(5), 5)

    def test_chinese_quantity(self):
        """测试中文数量"""
        from src.processor.processor import LLMClient

        client = LLMClient.__new__(LLMClient)

        self.assertEqual(client._parse_quantity("两台"), 2)
        self.assertEqual(client._parse_quantity("一台"), 1)


class TestTransactionRecord(unittest.TestCase):
    """测试交易记录"""

    def test_to_dict(self):
        """测试转换为字典"""
        from src.processor import TransactionRecord

        record = TransactionRecord(
            action="SELL",
            item="iPhone 14 Pro Max",
            specs="256G 紫色",
            price=5800,
            quantity=2,
            raw_text="出两台14pm",
            sender="老王",
            group="测试群",
            message_time="14:02",
            capture_time=datetime.now().isoformat()
        )

        data = record.to_dict()

        self.assertEqual(data["action"], "SELL")
        self.assertEqual(data["item"], "iPhone 14 Pro Max")
        self.assertEqual(data["price"], 5800)


class TestDatabaseSchema(unittest.TestCase):
    """测试数据库"""

    def test_schema_creation(self):
        """测试数据库表创建"""
        import tempfile
        from src.storage.database import DatabaseManager

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            db = DatabaseManager(db_path)
            stats = db.get_statistics()

            self.assertIn("total_records", stats)
            self.assertIn("by_group", stats)
            self.assertIn("by_action", stats)
        finally:
            os.unlink(db_path)

    def test_insert_record(self):
        """测试插入记录"""
        import tempfile
        from src.storage.database import DatabaseManager
        from src.processor import TransactionRecord

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            db = DatabaseManager(db_path)

            record = TransactionRecord(
                action="SELL",
                item="iPhone 14",
                specs="256G",
                price=5000,
                quantity=1,
                raw_text="出iPhone 14",
                sender="测试",
                group="测试群",
                message_time="14:02",
                capture_time=datetime.now().isoformat()
            )

            record_id = db.insert_record(record)
            self.assertGreater(record_id, 0)
        finally:
            os.unlink(db_path)


class TestReportGeneration(unittest.TestCase):
    """测试报表生成"""

    def test_format_price(self):
        """测试价格格式化"""
        from src.storage.reports import ReportGenerator

        generator = ReportGenerator.__new__(ReportGenerator)

        self.assertEqual(generator._format_price(5000), "5.0k")
        self.assertEqual(generator._format_price(15000), "1.5w")
        self.assertEqual(generator._format_price(500), "500")


if __name__ == "__main__":
    unittest.main()
