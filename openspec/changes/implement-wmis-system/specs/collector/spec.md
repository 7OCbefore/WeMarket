## ADDED Requirements
### Requirement: WeChat Group Message Collection
The system SHALL use Windows UI Automation (uiautomation) to control WeChat PC client and extract chat messages from configured group names.

#### Scenario: Connect to WeChat window
- **WHEN** the system starts
- **THEN** it locates the WeChat PC client window by window title or process name
- **AND** establishes a stable connection for UI operations

#### Scenario: Navigate to target group
- **WHEN** group names are provided in config.yaml
- **THEN** the system searches and clicks on each target group in the sidebar or search box
- **AND** waits for the chat window to fully load

#### Scenario: Extract messages with scrolling
- **WHEN** the chat window is open
- **THEN** the system scrolls upward and extracts message elements including sender nickname, timestamp, and content
- **AND** stops when reaching the checkpoint anchor point or max scroll limit

#### Scenario: Incremental fetching
- **WHEN** a previous checkpoint exists
- **THEN** the system only extracts messages newer than the last recorded message
- **AND** updates the checkpoint after successful extraction

### Requirement: System Message Filtering
The system SHALL filter out non-user messages such as system notifications and recall indicators.

#### Scenario: Filter system messages
- **WHEN** processing raw chat data
- **THEN** the system excludes messages matching patterns like "XX撤回了一条消息"
- **AND** only preserves actual user-generated content
