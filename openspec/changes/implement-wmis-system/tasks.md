## 1. Project Structure
- [x] 1.1 创建 src/ 目录结构
- [x] 1.2 创建 config.yaml 配置文件模板
- [x] 1.3 创建 requirements.txt

## 2. Collector Module (Extract)
- [x] 2.1 实现微信窗口连接 (WeChatConnector)
- [x] 2.2 实现群组定位 (GroupLocator)
- [x] 2.3 实现消息滚动采集 (MessageScraper)
- [x] 2.4 实现增量 checkpoint 机制

## 3. NLP Processor Module (Transform)
- [x] 3.1 设计 LLM Prompt 模板
- [x] 3.2 实现 LLM API 客户端 (LLMClient)
- [x] 3.3 实现消息批量解析 (BatchProcessor)
- [x] 3.4 实现异常处理与降级策略

## 4. Data Storage Module (Load)
- [x] 4.1 创建 SQLite 数据库 schema
- [x] 4.2 实现数据库操作类 (DatabaseManager)
- [x] 4.3 实现 Excel 报表生成 (ReportGenerator)
- [x] 4.4 实现趋势分析脚本

## 5. Main Workflow
- [x] 5.1 实现 ETL 主流程 (ETLPipeline)
- [x] 5.2 实现错误处理与日志
- [x] 5.3 实现运行完成通知

## 6. Testing & Delivery
- [x] 6.1 单元测试 (10 tests passed)
- [x] 6.2 编写 README 文档

## 下一步
- [ ] 配置 API Key 并运行完整测试
- [ ] 根据实际微信 UI 调整选择器
