"""
数据库管理器
负责 SQLite 数据库的创建和操作
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.processor import TransactionRecord


class DatabaseManager:
    """SQLite 数据库管理器"""

    def __init__(self, db_path: str = "./data/market_data.db"):
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self) -> None:
        """确保数据库和表存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建 market_data 表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capture_time DATETIME NOT NULL,
                message_time DATETIME,
                group_name TEXT,
                sender_nickname TEXT,
                raw_text TEXT,
                action TEXT,
                item_category TEXT,
                specs TEXT,
                price REAL,
                quantity INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_market_data_group
            ON market_data(group_name)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_market_data_time
            ON market_data(message_time)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_market_data_action
            ON market_data(action)
        ''')

        conn.commit()
        conn.close()

    def insert_record(self, record: TransactionRecord) -> int:
        """
        插入单条记录

        Args:
            record: 交易记录

        Returns:
            插入记录的 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = record.to_db_dict()

        cursor.execute('''
            INSERT INTO market_data (
                capture_time, message_time, group_name, sender_nickname,
                raw_text, action, item_category, specs, price, quantity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['capture_time'],
            data.get('message_time'),
            data.get('group_name'),
            data.get('sender_nickname'),
            data.get('raw_text'),
            data['action'],
            data['item_category'],
            data['specs'],
            data['price'],
            data['quantity']
        ))

        record_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return record_id

    def insert_records(self, records: List[TransactionRecord]) -> int:
        """
        批量插入记录

        Args:
            records: 交易记录列表

        Returns:
            插入的记录数量
        """
        if not records:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for record in records:
            data = record.to_db_dict()
            cursor.execute('''
                INSERT INTO market_data (
                    capture_time, message_time, group_name, sender_nickname,
                    raw_text, action, item_category, specs, price, quantity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['capture_time'],
                data.get('message_time'),
                data.get('group_name'),
                data.get('sender_nickname'),
                data.get('raw_text'),
                data['action'],
                data['item_category'],
                data['specs'],
                data['price'],
                data['quantity']
            ))

        count = len(records)
        conn.commit()
        conn.close()

        return count

    def query_records(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        group_name: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        查询记录

        Args:
            start_time: 开始时间
            end_time: 结束时间
            group_name: 群名称
            action: 交易方向 (SELL/BUY)
            limit: 返回数量限制

        Returns:
            记录列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM market_data WHERE 1=1"
        params = []

        if start_time:
            query += " AND message_time >= ?"
            params.append(start_time)

        if end_time:
            query += " AND message_time <= ?"
            params.append(end_time)

        if group_name:
            query += " AND group_name = ?"
            params.append(group_name)

        if action:
            query += " AND action = ?"
            params.append(action)

        query += f" ORDER BY capture_time DESC LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 获取列名
        columns = [desc[0] for desc in cursor.description]

        conn.close()

        return [dict(zip(columns, row)) for row in rows]

    def get_price_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取价格趋势数据

        Args:
            days: 天数

        Returns:
            按日期聚合的价格数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                DATE(message_time) as date,
                action,
                AVG(price) as avg_price,
                COUNT(*) as count
            FROM market_data
            WHERE message_time >= datetime('now', ?)
            GROUP BY DATE(message_time), action
            ORDER BY date DESC
        ''', (f'-{days} days',))

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        conn.close()

        return [dict(zip(columns, row)) for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # 总记录数
        cursor.execute("SELECT COUNT(*) FROM market_data")
        stats['total_records'] = cursor.fetchone()[0]

        # 按群组统计
        cursor.execute('''
            SELECT group_name, COUNT(*) as count
            FROM market_data
            GROUP BY group_name
        ''')
        stats['by_group'] = dict(cursor.fetchall())

        # 按交易类型统计
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM market_data
            GROUP BY action
        ''')
        stats['by_action'] = dict(cursor.fetchall())

        # 平均价格
        cursor.execute("SELECT AVG(price) FROM market_data WHERE price > 0")
        stats['avg_price'] = cursor.fetchone()[0]

        conn.close()

        return stats


if __name__ == "__main__":
    # 测试数据库
    db = DatabaseManager("./data/market_data.db")
    stats = db.get_statistics()
    print(f"数据库统计: {stats}")
