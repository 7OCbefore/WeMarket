# Change: Implement WMIS System

## Why
构建微信市场情报自动化系统，实现从微信行业群抓取交易信息、LLM智能解析、数据持久化的完整链路，赋能倒货业务的市场情报收集与分析。

## What Changes
- 新增消息采集模块 (Collector): Windows UI Automation 驱动
- 新增智能解析模块 (NLP Processor): LLM 批量解析消息
- 新增数据存储模块 (Data Storage): SQLite + Excel 报表
- 新增主程序入口: ETL 工作流编排
- 新增配置文件: config.yaml, checkpoint.json

## Impact
- Affected specs: collector, nlp-processor, data-storage
- Affected code: src/ 目录下全部模块
