"""
ETL 管道主流程
编排采集、处理、存储的完整工作流
"""

import sys
import time
from datetime import datetime
from typing import Dict, List

from src.config import Config
from src.collector import WeChatCollector, Message
from src.processor import NLPProcessor, TransactionRecord
from src.storage import DatabaseManager, ReportGenerator


class ETLPipeline:
    """ETL 管道主类"""

    def __init__(self, config_path: str = "./config.yaml"):
        self.config = Config(config_path)

        # 初始化各模块
        self.collector = WeChatCollector(self.config)
        self.processor = NLPProcessor(self.config)
        self.db = DatabaseManager(self.config.database['path'])
        self.reporter = ReportGenerator(self.config)

        # 统计
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_messages": 0,
            "total_records": 0,
            "groups_processed": 0
        }

    def run(self) -> None:
        """执行完整的 ETL 流程"""
        print("=" * 60)
        print("微信市场情报自动化系统 (WMIS)")
        print("=" * 60)
        print()

        self.stats["start_time"] = datetime.now()

        try:
            # Step 1: 采集消息
            print("[1/4] 开始采集消息...")
            all_messages = self._collect_messages()
            self.stats["total_messages"] = sum(len(msgs) for msgs in all_messages.values())

            if self.stats["total_messages"] == 0:
                print("没有采集到任何消息，程序退出")
                return

            # Step 2: 解析消息
            print("\n[2/4] 开始解析消息...")
            all_records = self._process_messages(all_messages)

            # Step 3: 存储数据
            print("\n[3/4] 存储数据到数据库...")
            if all_records:
                count = self.db.insert_records(all_records)
                print(f"已存储 {count} 条交易记录")
                self.stats["total_records"] = count

            # Step 4: 生成报表
            print("\n[4/4] 生成报表...")
            if all_records:
                self.reporter.generate_session_report(all_records)

            # 输出统计
            self._print_summary()

        except KeyboardInterrupt:
            print("\n用户中断程序")
        except Exception as e:
            print(f"\n程序出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.stats["end_time"] = datetime.now()

    def _collect_messages(self) -> Dict[str, List[Message]]:
        """采集所有群的消息"""
        all_messages: Dict[str, List[Message]] = {}

        for group_name in self.config.groups:
            try:
                messages = self.collector.collect_from_group(group_name)
                if messages:
                    all_messages[group_name] = messages
                    self.stats["groups_processed"] += 1
            except Exception as e:
                print(f"采集群 {group_name} 失败: {e}")

        return all_messages

    def _process_messages(self, all_messages: Dict[str, List[Message]]) -> List[TransactionRecord]:
        """处理所有消息"""
        all_records: List[TransactionRecord] = []

        for group_name, messages in all_messages.items():
            print(f"  解析群: {group_name}, {len(messages)} 条消息")
            records = self.processor.process_group_messages(group_name, messages)
            all_records.extend(records)

        return all_records

    def _print_summary(self) -> None:
        """打印运行统计"""
        duration = self.stats["end_time"] - self.stats["start_time"]

        print()
        print("=" * 60)
        print("运行统计")
        print("=" * 60)
        print(f"运行时间: {duration.seconds} 秒")
        print(f"处理群组: {self.stats['groups_processed']}")
        print(f"采集消息: {self.stats['total_messages']}")
        print(f"有效记录: {self.stats['total_records']}")
        print("=" * 60)


def main():
    """主入口"""
    # 默认配置文件
    config_path = "./config.yaml"

    # 支持命令行参数
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    # 检查配置文件
    if not config_path.endswith('.yaml'):
        config_path = config_path + '.yaml'

    pipeline = ETLPipeline(config_path)
    pipeline.run()


if __name__ == "__main__":
    main()
