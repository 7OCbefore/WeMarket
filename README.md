# 微信市场情报自动化系统 (WMIS)

> A PC-based RPA automation tool for WeChat market intelligence.

## 简介

WMIS 是一个基于 PC 端的自动化 RPA 工具，用于从微信行业交流群中抓取交易信息，利用 LLM 进行智能解析，并生成商业情报数据库。

## 功能特性

- **增量采集**: 只抓取新消息，支持断点续传
- **智能解析**: 使用 LLM 从非结构化文本中提取结构化交易数据
- **数据持久化**: SQLite 数据库存储，支持历史查询
- **报表生成**: 自动生成 Excel 报表，按价格排序

## 环境要求

- Windows 10/11
- Python 3.10+
- 微信 PC 客户端 (已登录)
- LLM API Key (OpenAI 兼容)

## 安装步骤

1. **克隆项目**
   ```bash
   git clone <your-repo-url>
   cd wechat1day
   ```

2. **创建虚拟环境** (推荐)
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置**
   编辑 `config.yaml`:
   ```yaml
   llm:
     api_base: "https://api.openai.com/v1"  # API 地址
     api_key: "your-api-key-here"           # API Key
     model: "deepseek-chat"                 # 模型名称

   groups:
     - "iPhone 行情交流群"
     - "安卓旗舰报价群"
   ```

5. **运行**
   ```bash
   python main.py
   ```

## 项目结构

```
wechat1day/
├── main.py              # 入口文件
├── run.bat              # Windows 启动脚本
├── config.yaml          # 配置文件
├── requirements.txt     # 依赖列表
├── README.md            # 说明文档
├── src/
│   ├── __init__.py
│   ├── config.py        # 配置加载
│   ├── pipeline.py      # ETL 主流程
│   ├── collector/       # 消息采集模块
│   │   ├── collector.py
│   │   └── extractor.py
│   ├── processor/       # LLM 解析模块
│   │   ├── processor.py
│   │   └── prompt.py
│   └── storage/         # 数据存储模块
│       ├── database.py
│       └── reports.py
├── data/                # 数据库文件
├── output/              # 报表输出
└── tests/               # 测试文件
```

## 配置说明

### config.yaml

| 配置项 | 说明 |
|--------|------|
| `llm.api_base` | LLM API 地址 |
| `llm.api_key` | API Key |
| `llm.model` | 模型名称 |
| `wechat.window_title` | 微信窗口标题 |
| `wechat.max_scroll_attempts` | 最大滚动次数 |
| `groups` | 目标群组列表 |
| `database.path` | SQLite 数据库路径 |
| `reports.output_dir` | 报表输出目录 |

## 注意事项

1. **合规性**: 本工具仅使用 UI 自动化，不使用 Hook 或内存注入
2. **安全性**: 请妥善保管 API Key，不要提交到代码仓库
3. **稳定性**: 微信版本更新可能导致 UI 选择器失效

## License

MIT
