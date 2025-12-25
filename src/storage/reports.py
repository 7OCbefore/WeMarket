"""
报表生成器
负责生成 Excel 格式的分析报表
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

from src.config import Config
from src.processor import TransactionRecord


class ReportGenerator:
    """报表生成器"""

    def __init__(self, config: Config):
        self.config = config
        reports_config = config.reports
        self.output_dir = reports_config.get('output_dir', './output')
        self.auto_open = reports_config.get('auto_open', True)

        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def _format_price(self, price: float) -> str:
        """格式化价格"""
        if price >= 10000:
            return f"{price/10000:.1f}w"
        elif price >= 1000:
            return f"{price/1000:.1f}k"
        else:
            return f"{price:.0f}"

    def generate_session_report(
        self,
        records: List[TransactionRecord],
        session_name: Optional[str] = None
    ) -> str:
        """
        生成会话报表

        Args:
            records: 交易记录列表
            session_name: 会话名称

        Returns:
            生成的报表文件路径
        """
        if not records:
            print("没有交易记录，跳过报表生成")
            return ""

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = session_name or f"Session_{timestamp}"

        # 构建 DataFrame
        data = []
        for record in records:
            data.append({
                "时间": record.message_time,
                "群组": record.group,
                "发送者": record.sender,
                "类型": record.action,
                "商品": record.item,
                "规格": record.specs,
                "价格": record.price,
                "价格(格式化)": self._format_price(record.price),
                "数量": record.quantity,
                "原始消息": record.raw_text
            })

        df = pd.DataFrame(data)

        # 按价格升序排列
        df = df.sort_values('价格', ascending=True)

        # 生成文件路径
        filename = f"Current_Session_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)

        # 写入 Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # 主数据表
            df.to_excel(writer, sheet_name='交易记录', index=False)

            # 统计摘要
            summary_data = {
                "指标": ["总记录数", "卖出记录", "买入记录", "平均价格", "最低价格", "最高价格"],
                "数值": [
                    len(df),
                    len(df[df['类型'] == 'SELL']),
                    len(df[df['类型'] == 'BUY']),
                    df['价格'].mean() if len(df) > 0 else 0,
                    df['价格'].min() if len(df) > 0 else 0,
                    df['价格'].max() if len(df) > 0 else 0,
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='统计摘要', index=False)

            # 按群组统计
            if df['群组'].nunique() > 1:
                group_stats = df.groupby('群组').agg({
                    '价格': ['count', 'mean', 'min', 'max']
                }).round(2)
                group_stats.columns = ['记录数', '平均价格', '最低价', '最高价']
                group_stats.to_excel(writer, sheet_name='按群组统计')

        print(f"报表已生成: {filepath}")

        # 自动打开
        if self.auto_open:
            self._open_file(filepath)

        return filepath

    def generate_trend_report(
        self,
        days: int = 7,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成趋势分析报表

        Args:
            days: 分析天数
            output_path: 输出路径

        Returns:
            生成的报表文件路径
        """
        from src.storage.database import DatabaseManager

        db = DatabaseManager(self.config.database['path'])
        records = db.query_records(limit=10000)

        if not records:
            print("数据库中没有足够的数据")
            return ""

        # 构建 DataFrame
        df = pd.DataFrame(records)

        # 转换时间
        df['message_time'] = pd.to_datetime(df['message_time'])

        # 按日期聚合
        df['date'] = df['message_time'].dt.date

        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Trend_Report_{days}days_{timestamp}.xlsx"
        output_path = output_path or os.path.join(self.output_dir, filename)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 原始数据
            df.to_excel(writer, sheet_name='原始数据', index=False)

            # 价格趋势透视表
            if len(df) > 0:
                pivot = pd.pivot_table(
                    df,
                    values='price',
                    index='date',
                    columns='action',
                    aggfunc=['count', 'mean']
                ).round(2)
                pivot.to_excel(writer, sheet_name='价格趋势')

                # 按商品统计
                item_stats = df.groupby('item_category').agg({
                    'price': ['count', 'mean', 'min', 'max']
                }).round(2)
                item_stats.columns = ['出现次数', '平均价格', '最低价', '最高价']
                item_stats = item_stats.sort_values('出现次数', ascending=False)
                item_stats.to_excel(writer, sheet_name='商品统计')

        print(f"趋势报表已生成: {output_path}")

        if self.auto_open:
            self._open_file(output_path)

        return output_path

    def _open_file(self, filepath: str) -> None:
        """打开文件"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # macOS/Linux
                subprocess.run(['open', filepath] if os.uname().sysname == 'Darwin' else ['xdg-open', filepath])
        except Exception as e:
            print(f"无法自动打开文件: {e}")


if __name__ == "__main__":
    # 测试报表生成
    from src.config import load_config
    from src.processor import TransactionRecord

    config = load_config("./config.yaml")

    # 模拟数据
    records = [
        TransactionRecord(
            action="SELL",
            item="iPhone 14 Pro Max",
            specs="256G 紫色 电池90%",
            price=5800,
            quantity=2,
            raw_text="出两台14pm 256 紫色 电池90 5800到付",
            sender="老王",
            group="测试群",
            message_time="14:02",
            capture_time=datetime.now().isoformat()
        ),
        TransactionRecord(
            action="BUY",
            item="iPhone 13",
            specs="256G",
            price=3000,
            quantity=1,
            raw_text="收一台iPhone 13 256G 预算3000",
            sender="张三",
            group="测试群",
            message_time="14:05",
            capture_time=datetime.now().isoformat()
        ),
    ]

    generator = ReportGenerator(config)
    generator.generate_session_report(records)
