## ADDED Requirements
### Requirement: SQLite Data Persistence
The system SHALL store all parsed transaction data in a SQLite database.

#### Scenario: Database schema creation
- **WHEN** the system first runs
- **THEN** it creates the market_data table with columns: id, capture_time, message_time, group_name, sender_nickname, raw_text, action, item_category, specs, price, quantity

#### Scenario: Data insertion
- **WHEN** LLM processing produces valid results
- **THEN** the system inserts each record into the SQLite database
- **AND** captures the current timestamp as capture_time

### Requirement: Excel Report Generation
The system SHALL generate Excel reports after each run.

#### Scenario: Session report generation
- **WHEN** a scraping session completes
- **THEN** the system generates an Excel file named Current_Session_{timestamp}.xlsx
- **AND** includes all high-value transaction records sorted by price ascending

#### Scenario: Trend analysis report
- **WHEN** trend analysis script is invoked with a time range
- **THEN** the system exports data with pivot tables showing price trends over time

### Requirement: Checkpoint Persistence
The system SHALL maintain checkpoint state to enable incremental fetching.

#### Scenario: Checkpoint file management
- **WHEN** a scraping session completes
- **THEN** the system updates checkpoint.json with the latest message_time and content for each group
- **AND** uses this file on next run to determine the starting point
