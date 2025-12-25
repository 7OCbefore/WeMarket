## ADDED Requirements
### Requirement: LLM-based Message Parsing
The system SHALL use LLM API to transform unstructured chat messages into structured transaction data.

#### Scenario: Batch message processing
- **WHEN** new messages are collected
- **THEN** the system batches them in groups of 20
- **AND** sends each batch to the LLM API for structured extraction

#### Scenario: Transaction intent recognition
- **WHEN** processing chat messages
- **THEN** the LLM identifies whether a message contains BUY or SELL intent
- **AND** filters out casual chat, emojis, and spam

#### Scenario: Entity extraction
- **WHEN** a transaction message is identified
- **THEN** the LLM extracts: action (SELL/BUY), item_name, specs, price, quantity
- **AND** normalizes price units (e.g., "5k" becomes 5000)

#### Scenario: Failed parsing handling
- **WHEN** a message cannot be parsed
- **THEN** the system marks it as UNKNOWN
- **AND** preserves the raw text for manual review

### Requirement: JSON Output Normalization
The system SHALL return structured JSON that can be directly inserted into the database.

#### Scenario: Standardized output format
- **WHEN** LLM processing completes
- **THEN** the response MUST be a valid JSON object containing: action, item, specs, price, quantity
- **AND** price MUST be a numeric value
