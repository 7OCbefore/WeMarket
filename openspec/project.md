# Project Context

## Purpose

**微信市场情报自动化系统 (WMIS)** - A PC-based RPA automation tool for the reselling/fliipping business. It extracts unstructured chat data from WeChat industry groups, cleans and structures it using LLM, and creates a commercial intelligence database for instant querying and long-term trend analysis.

### Core Objectives

1. **Incremental Fetching**: Only capture new/unread messages since last run
2. **Instant Intelligence**: Generate "temporary session tables" for real-time market price discovery
3. **Data Warehousing**: Persist cleaned data for daily/weekly/monthly price trend analysis
4. **Compliance**: Use pure UI automation to minimize WeChat account ban risk

## Tech Stack

- **Language**: Python 3.10+
- **RPA Core**: `uiautomation` (Windows UI element automation)
- **Data Processing**: `pandas`, `openpyxl`
- **Database**: SQLite (lightweight, serverless)
- **AI Engine**: OpenAI-compatible LLM API (DeepSeek-V3 recommended for cost/performance balance)
- **Output**: Excel reports (.xlsx)

## Project Conventions

### Code Style

- Clear function naming with action verbs (e.g., `collect_messages()`, `parse_with_llm()`)
- Modular architecture following ETL pattern: Extract → Transform → Load
- Configuration externalized to `config.yaml`
- Checkpoint mechanism via `checkpoint.json` for incremental采集

### Architecture Patterns

- **ETL Architecture**:
  - **Extract Layer**: Windows UI Automation driver (controls WeChat PC client)
  - **Transform Layer**: LLM Processor for deduplication and structured extraction
  - **Load & View Layer**: Data Manager for SQLite persistence and Excel reporting

- **Batch Processing**: LLM API calls in batches of 20 messages
- **Fallback Strategy**: When anchor point not found (messages cleared), default to last N screens

### Testing Strategy

- Manual validation during Phase 1 MVP (single group scraping)
- Keep `raw_text` column in Excel for manual verification (AI hallucination mitigation)
- Pixel change detection to confirm message loading completion

### Git Workflow

- Feature branches for each implementation phase
- Phase 1: MVP single group scraping
- Phase 2: LLM integration + Excel output
- Phase 3: SQLite + incremental fetching

## Domain Context

### WeChat Group Chat Intelligence

- Target: Industry exchange groups for reselling/flip trading
- Data: Unstructured chat messages containing buy/sell intentions
- Key Entities to Extract:
  - Transaction Type (SELL/BUY)
  - Item Name (product)
  - Specs (condition, capacity, color)
  - Price (normalized, handling "k"/"w" units)
  - Quantity

## Important Constraints

1. **WeChat Compliance**:
   - Absolute prohibition on Hook or memory injection techniques
   - Only use UI Automation (`uiautomation`)
   - Random delays between operations: 1-3 seconds
   - Control daily run frequency

2. **UI Stability**:
   - WeChat version updates may change element ClassName
   - UI selectors must be externalized to configuration

3. **AI Reliability**:
   - AI may hallucinate prices (e.g., phone numbers)
   - Always preserve raw text for manual verification

## External Dependencies

- **WeChat PC Client**: Target application for automation
- **LLM API**: OpenAI-compatible endpoint (DeepSeek-V3 or similar)
- **Windows OS**: Required for `uiautomation` library

## Database Schema

Primary table: `market_data`

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER PK | Auto-increment primary key |
| capture_time | DATETIME | Time when message was captured |
| message_time | DATETIME | Original message send time |
| group_name | TEXT | Source WeChat group |
| sender_nickname | TEXT | Sender's display name in the group |
| raw_text | TEXT | Original message content |
| action | TEXT | SELL or BUY |
| item_category | TEXT | Normalized product name |
| specs | TEXT | Spec details |
| price | REAL | Numeric price |
| quantity | INTEGER | Quantity |
