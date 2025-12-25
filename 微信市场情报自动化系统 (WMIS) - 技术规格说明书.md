# **微信市场情报自动化系统 (WMIS) \- 技术规格说明书**

版本号: v1.0.0  
日期: 2025-05-20  
密级: 内部

## **1\. 项目概述 (Project Overview)**

### **1.1 背景**

本项目旨在构建一套基于 PC 端的自动化 RPA（机器人流程自动化）工具，服务于倒货交易业务。通过非侵入式手段从指定的微信行业交流群中抓取非结构化聊天数据，利用 LLM（大语言模型）进行清洗与结构化提取，最终形成可供即时查询和长期复盘的商业情报数据库。

### **1.2 核心目标**

1. **增量采集 (Incremental Fetching):** 能够识别并只获取自上次运行以来产生的“未读/新”消息。  
2. **即时情报 (Instant Intelligence):** 运行时生成“临时会话表”，用于快速发现当前市场低价货物。  
3. **数据沉淀 (Data Warehousing):** 将清洗后的数据追加至总数据库，支持按日、周、月进行价格趋势复盘。  
4. **安全合规 (Compliance):** 采用纯物理模拟（UI Automation）方案，最大程度降低封号风险。

## **2\. 系统架构 (System Architecture)**

系统采用 **ETL (Extract, Transform, Load)** 架构设计，分为三层：

### **2.1 架构图示**

* **采集层 (Extract):** Windows UI Automation 驱动层。负责控制微信 PC 客户端，滚动窗口，OCR/文本抓取。  
* **处理层 (Transform):** LLM Processor 核心解析层。负责数据去重、清洗、结构化提取（通过 API 调用）。  
* **存储与应用层 (Load & View):** Data Manager。负责维护 SQLite 主数据库和生成 Excel 报表。

### **2.2 技术栈选型**

* **开发语言:** Python 3.10+  
* **RPA 核心库:** uiautomation (针对 Windows UI 元素操作稳定性最佳)  
* **数据处理:** pandas (数据清洗), openpyxl (Excel 交互)  
* **持久化存储:** SQLite (轻量级关系型数据库，无需配置服务器)  
* **AI 引擎:** 兼容 OpenAI 协议的 LLM API (建议使用 DeepSeek-V3 或 硅基流动提供的api，平衡成本与中文理解力)

## **3\. 功能需求说明 (Functional Requirements)**

### **3.1 消息采集模块 (Collector)**

* **FR-01 群组定位:** 系统需根据配置文件中的 group\_names 列表，自动在微信侧边栏或搜索框定位目标群聊。  
* **FR-02 增量逻辑 (核心):**  
  * 系统需维护一个 checkpoint.json 文件，记录每个群组上次抓取的 last\_message\_content 和 last\_message\_time。  
  * 运行时，脚本向上滚动聊天记录，直到匹配到 Anchor Point (锚点) 或达到最大回溯上限（如最近500条）。  
  * **Fallback机制:** 若找不到锚点（如消息已被清理），默认抓取最近 N 屏消息。  
* **FR-03 文本提取:** 提取字段包括：发送者昵称、发送时间、消息内容。自动过滤系统消息（如“XX撤回了一条消息”）。

### **3.2 智能解析模块 (NLP Processor)**

* **FR-04 意图识别:** 识别消息是否包含“交易意图”。过滤闲聊、表情包、重复广告。  
* **FR-05 实体抽取:** 从非结构化文本中提取：  
  * Transaction\_Type (买/卖)  
  * Item\_Name (商品名称)  
  * Spec (规格/成色/容量)  
  * Price (单价/总价，需统一货币单位)  
  * Quantity (数量)  
* **FR-06 异常处理:** 对于无法解析的复杂文本，标记为 UNKNOWN 并保留原始文本以便人工核对。

### **3.3 数据存储与展示 (Storage & View)**

* **FR-07 会话报表 (Session Report):** 每次运行结束后，自动打开生成的 Excel，包含本次抓取的高价值交易信息，按价格升序排列。  
* **FR-08 历史入库:** 将清洗后的数据追加写入 SQLite 数据库 trade\_history.db。  
* **FR-09 趋势复盘:** 提供一个独立的分析脚本，输入时间跨度（如“本周”），从数据库导出包含 K 线数据或透视表的 Excel 文件。

## **4\. 详细设计 (Detailed Design)**

### **4.1 数据库设计 (SQLite Schema)**

表名: market\_data

| 字段名 | 类型 | 说明 |
| :---- | :---- | :---- |
| id | INTEGER PK | 自增主键 |
| capture\_time | DATETIME | 抓取时间 |
| message\_time | DATETIME | 消息原始发送时间 |
| group\_name | TEXT | 来源群组 |
| sender\_hash | TEXT | 发送者ID的哈希值 (保护隐私但允许追踪同一人) |
| raw\_text | TEXT | 原始消息内容 (用于校验) |
| action | TEXT | SELL / BUY |
| item\_category | TEXT | 商品标准化名称 (由AI归一化) |
| specs | TEXT | 规格详情 |
| price | REAL | 价格 (数字) |
| quantity | INTEGER | 数量 |

### **4.2 LLM Prompt 设计 (系统提示词)**

你是一个专业的倒货交易数据分析师。你的任务是从杂乱的聊天记录中提取结构化交易数据。

输入数据格式: \[时间\] \[发送者\]: \[消息内容\]

请遵循以下规则:  
1\. 忽略闲聊、表情、无意义的语气词。  
2\. 识别交易方向: "出"、"卖" \-\> SELL; "收"、"求" \-\> BUY。  
3\. 提取商品名称、规格、价格。如果价格使用了"k"或"w"作为单位，请转换为标准数字。  
4\. 输出格式必须为标准 JSON List。

示例输入: 14:02 老王: 出两台14pm 256 紫色 电池90 5800到付  
示例输出:  
{  
  "action": "SELL",  
  "item": "iPhone 14 Pro Max",  
  "specs": "256G 紫色 电池90%",  
  "price": 5800,  
  "quantity": 2  
}

### **4.3 核心工作流逻辑 (Workflow)**

1. **Init:** 读取 config.yaml (群名列表) 和 checkpoint.json。  
2. **Attach:** 连接微信 Windows 窗口句柄。  
3. **Loop (for group in groups):**  
   * 点击群组。  
   * **Scroll & Scrape:** 循环向上滚动并截图/OCR或直接获取元素文本（推荐获取元素树 Name 属性）。  
   * **Stop Condition:** 遇到上次记录的最后一条消息的时间戳。  
   * **Save Raw:** 将新消息存入内存列表 new\_messages。  
   * **Update Checkpoint:** 更新该群的最新消息时间。  
4. **Process:** 将 new\_messages 分批 (Batch Size \= 20\) 发送给 LLM API。  
5. **Persist:**  
   * 将解析结果 parsed\_data 插入 SQLite。  
   * 将 parsed\_data 导出为 Current\_Session\_{Timestamp}.xlsx。  
6. **Finish:** 弹窗提示“抓取完成，共发现 X 条有效报价”，并自动打开 Excel。

## **5\. 风险控制与应对 (Risk Management)**

| 风险点 | 风险等级 | 应对策略 |
| :---- | :---- | :---- |
| **微信封号** | 高 | 1\. 严格使用 uiautomation 模拟鼠标键盘，**绝对禁止**使用 Hook 或内存注入技术。 2\. 两次操作间增加 random(1, 3\) 秒的随机延迟。 3\. 每日运行频率控制在合理范围。 |
| **UI 变更** | 中 | 微信版本更新可能导致元素 ClassName 改变。代码需将 UI 选择器抽离为配置文件，便于快速适配新版本。 |
| **AI 幻觉** | 中 | AI 可能会错误提取价格（如将电话号码识别为价格）。 **策略:** 在 Excel 中保留 原始文本 列，人工扫一眼即可校验。 |
| **消息遗漏** | 低 | 滚动加载可能会因为网络卡顿导致部分消息未加载。 **策略:** 增加滚动后的 sleep 等待时间，检测屏幕像素变化确认加载完成。 |

## **6\. 开发实施计划 (Implementation Roadmap)**

### **Phase 1: MVP 原型 (预计工期: 3天)**

* **目标:** 实现单群抓取 \-\> 控制台输出结果。  
* **内容:** 完成 Python 环境搭建，调试通 uiautomation 能够稳定获取当前屏幕文字。

### **Phase 2: 数据流打通 (预计工期: 5天)**

* **目标:** 接入 LLM，实现文本转 JSON，并存入 Excel。  
* **内容:** 编写 Prompt，调试 API，设计 Excel 模板格式。

### **Phase 3: 增量与持久化 (预计工期: 4天)**

* **目标:** 实现 SQLite 入库和“未读消息”逻辑。  
* **内容:** 开发 Checkpoint 机制，编写 SQL 语句，完善错误处理。

## **7\. 交付物清单 (Deliverables)**

1. **Source Code:** 完整的 Python 工程源码。  
2. **Executable:** 打包好的 .exe 可执行文件 (无需配置环境即可运行)。  
3. **Config File:** config.yaml (用户自行修改群名、API Key)。  
4. **Database:** market\_data.db (初始数据库文件)。