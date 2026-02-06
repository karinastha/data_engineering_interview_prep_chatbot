# E-Commerce ELT Pipeline Documentation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Data Flow](#data-flow)
6. [ETL Pipeline Details](#etl-pipeline-details)
7. [Database Design](#database-design)
8. [Data Models](#data-models)
9. [Data Quality & Testing](#data-quality--testing)
10. [Configuration Management](#configuration-management)
11. [Setup Instructions](#setup-instructions)
12. [Usage Guide](#usage-guide)
13. [Engineering Decisions](#engineering-decisions)

---

## Project Overview

This is a **production-grade ELT (Extract, Load, Transform) pipeline** designed to extract data from an E-commerce REST API, validate and load raw data into PostgreSQL, and transform it using dbt into a dimensional data model suitable for analytics and reporting.

### Purpose

The pipeline enables end-to-end data processing for an e-commerce platform, handling:
- **Customer data** - Customer profiles and locations
- **Order data** - Order transactions and lifecycle events
- **Product data** - Product catalog with categories and physical attributes
- **Seller data** - Seller information and locations
- **Order items** - Line-item details for each order
- **Payments** - Payment transactions and methods
- **Reviews** - Customer reviews and ratings

### Key Production Features

| Feature | Description |
|---------|-------------|
| **Centralized Error Logging** | All failures logged with context and categorization |
| **OAuth Token Management** | Automatic token refresh before expiry with thread-safe operations |
| **Idempotent Extraction** | Skip already-extracted data using hash-based change detection |
| **Schema Validation** | Pydantic models validate data structure before loading |
| **Retry Logic** | Exponential backoff for transient failures |
| **Invalid Data Handling** | Segregate and track validation failures in separate tables |
| **Connection Pooling** | Efficient HTTP session and database connection management |
| **Metadata Tracking** | Track extraction history and data changes |
| **Dimensional Modeling** | Star schema design for analytics |

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           E-COMMERCE ELT PIPELINE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  REST    │    │   Python     │    │   Python     │    │     dbt      │   │
│  │  API     │───▶│  Extraction  │───▶│  Raw Loader  │───▶│  Transform   │   │
│  │          │    │  + Validate  │    │              │    │              │   │
│  └──────────┘    └──────────────┘    └──────────────┘    └──────────────┘   │
│       │                 │                   │                   │           │
│       ▼                 ▼                   ▼                   ▼           │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  OAuth   │    │  JSON Files  │    │  PostgreSQL  │    │  PostgreSQL  │   │
│  │  Tokens  │    │  (data/raw)  │    │  (raw schema)│    │  (marts)     │   │
│  └──────────┘    └──────────────┘    └──────────────┘    └──────────────┘   │
│                                             │                   │           │
│                                             ▼                   ▼           │
│                                    ┌──────────────────────────────────┐     │
│                                    │         ANALYTICS LAYER          │     │
│                                    │   (Dashboards, Reports, BI)      │     │
│                                    └──────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Simplified Data Flow

```
API → Python (Extract + Validate) → JSON Files → Python (Load) → PostgreSQL (Raw) → dbt (Transform) → PostgreSQL (Marts)
```

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXTRACTION LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐          │
│  │  TokenManager  │────▶│   APIClient    │────▶│ DataExtractor  │          │
│  │                │     │                │     │                │          │
│  │ - login()      │     │ - fetch_data() │     │ - extract()    │          │
│  │ - refresh()    │     │ - retry logic  │     │ - validate()   │          │
│  │ - get_header() │     │ - error_log    │     │ - paginate()   │          │
│  └────────────────┘     └────────────────┘     └────────────────┘          │
│         │                       │                      │                    │
│         ▼                       ▼                      ▼                    │
│  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐          │
│  │  ErrorLogger   │     │MetadataManager │     │ Pydantic       │          │
│  │                │     │                │     │ Schemas        │          │
│  │ - log_error()  │     │ - should_skip()│     │                │          │
│  │ - get_summary()│     │ - update()     │     │ - validate()   │          │
│  │ - save_to_file │     │ - data_hash    │     │ - extra=forbid │          │
│  └────────────────┘     └────────────────┘     └────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LOADING LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────┐     ┌────────────────┐     ┌────────────────┐          │
│  │  JSON Files    │────▶│  Raw Loader    │────▶│  PostgreSQL    │          │
│  │  (data/raw/)   │     │                │     │  (raw schema)  │          │
│  │                │     │ - validate     │     │                │          │
│  │ - customers    │     │ - bulk_insert  │     │ - JSONB tables │          │
│  │ - orders       │     │ - COPY cmd     │     │ - invalid tbl  │          │
│  │ - products     │     │                │     │                │          │
│  └────────────────┘     └────────────────┘     └────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TRANSFORMATION LAYER (dbt)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   RAW SCHEMA    │───▶│ STAGING SCHEMA  │───▶│  MARTS SCHEMA   │         │
│  │                 │    │                 │    │                 │         │
│  │ - JSONB tables  │    │ - stg_customers │    │ - dim_customer  │         │
│  │ - products      │    │ - stg_orders    │    │ - dim_product   │         │
│  │ - customers     │    │ - stg_products  │    │ - dim_seller    │         │
│  │ - orders        │    │ - stg_sellers   │    │ - dim_date      │         │
│  │ - order_items   │    │ - stg_order_*   │    │ - fact_orders   │         │
│  │ - order_payments│    │                 │    │ - fact_order_*  │         │
│  │ - order_reviews │    │ Views           │    │ - fct_payments  │         │
│  │ - sellers       │    │                 │    │ - fct_reviews   │         │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘         │
│                                                                             │
│                         ┌─────────────────┐                                 │
│                         │ INVALID SCHEMA  │                                 │
│                         │                 │                                 │
│                         │ - invalid_prods │                                 │
│                         │ - validation_   │                                 │
│                         │   failures      │                                 │
│                         └─────────────────┘                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Language** | Python | 3.11+ |
| **Database** | PostgreSQL | 16+ |
| **Transformation** | dbt Core | 1.11+ |
| **dbt Adapter** | dbt-postgres | 1.10+ |
| **Validation** | Pydantic | 2.5+ |
| **HTTP Client** | Requests | 2.32+ |
| **ORM** | SQLAlchemy | 2.0+ |
| **Data Processing** | Pandas | 2.3+ |
| **Environment** | python-dotenv | 1.2+ |
| **Logging** | python-json-logger | 2.0+ |

### Dependencies (requirements.txt)

```
boto3>=1.42.24
dbt-core>=1.11.2
dbt-postgres>=1.10.0
fastapi>=0.128.0
pandas>=2.3.3
psycopg2-binary>=2.9.11
pyarrow>=22.0.0
pydantic>=2.12.5
pyjwt>=2.10.1
python-dotenv>=1.2.1
requests>=2.32.5
sqlalchemy>=2.0.45
uvicorn>=0.40.0
pydantic-settings>=2.1.0
urllib3>=2.1.0
alembic>=1.13.0
python-json-logger>=2.0.7
```

---

## Project Structure

```
dbt_ecom1/
│
├── config/
│   └── settings.py              # Centralized Pydantic Settings configuration
│
├── data/
│   └── raw/                     # Extracted JSON files from API
│       ├── customers.json
│       ├── orders.json
│       ├── products.json
│       ├── sellers.json
│       ├── orders_items.json
│       ├── orders_payments.json
│       └── orders_reviews.json
│
├── ecom_transformation/         # dbt Project
│   ├── dbt_project.yml          # dbt project configuration
│   ├── profiles.yml             # Database connection profiles
│   ├── macros/
│   │   ├── data_quality.sql     # Data quality & validation macros
│   │   └── generate_schema_name.sql  # Schema naming macro
│   ├── models/
│   │   ├── staging/             # Staging models (views)
│   │   │   ├── sources.yml      # Source definitions
│   │   │   ├── schema.yml       # Model tests & documentation
│   │   │   ├── stg_customers.sql
│   │   │   ├── stg_orders.sql
│   │   │   ├── stg_order_items.sql
│   │   │   ├── stg_order_payments.sql
│   │   │   ├── stg_order_reviews.sql
│   │   │   ├── stg_products.sql
│   │   │   ├── stg_sellers.sql
│   │   │   └── invalid_products.sql
│   │   └── marts/               # Dimension & Fact tables
│   │       ├── schema.yml       # Model tests & documentation
│   │       ├── dim_customer.sql
│   │       ├── dim_date.sql
│   │       ├── dim_order_status.sql
│   │       ├── dim_payment_method.sql
│   │       ├── dim_product.sql
│   │       ├── dim_review_detail.sql
│   │       ├── dim_seller.sql
│   │       ├── fact_orders.sql
│   │       ├── fact_order_items.sql
│   │       ├── fct_payments.sql
│   │       └── fct_reviews.sql
│   └── tests/                   # Custom data quality tests
│       ├── assert_order_payments_match_order_totals.sql
│       └── assert_valid_delivery_dates.sql
│
├── etl_pipeline/                # Python ETL Code
│   ├── __init__.py
│   ├── client1.py               # Alternative API client (attached)
│   ├── run_extraction.py        # Main extraction orchestrator
│   ├── load_raw_data.py         # Load JSON to PostgreSQL
│   ├── schemas.py               # Pydantic schemas (root level)
│   │
│   ├── core/                    # Core utilities
│   │   ├── __init__.py
│   │   ├── client.py            # API client with retry logic
│   │   ├── token_manager.py     # OAuth token management
│   │   ├── error_logger.py      # Centralized error logging
│   │   └── exceptions.py        # Custom exception classes
│   │
│   ├── database/                # Database operations
│   │   ├── __init__.py
│   │   ├── connection.py        # Connection pooling
│   │   ├── raw_loader.py        # Raw data loader
│   │   └── staging_loader.py    # Staging data loader
│   │
│   ├── extraction/              # Data extraction
│   │   ├── __init__.py
│   │   ├── data_extractor.py    # Main extraction logic
│   │   ├── metadata_manager.py  # Extraction metadata tracking
│   │   └── utils.py             # Utility functions
│   │
│   ├── schemas/                 # Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── raw.py               # Raw data schemas
│   │   └── staging.py           # Staging schemas
│   │
│   └── validation/              # Validation logic
│       ├── __init__.py
│       └── schemas.py           # Validation schema map
│
├── logs/                        # Application logs
├── .env                         # Environment variables (gitignored)
├── .env_example                 # Environment template
├── requirements.txt             # Python dependencies
└── README.md                    # Project readme
```

---

## Data Flow

### End-to-End Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE DATA FLOW                                 │
└────────────────────────────────────────────────────────────────────────────┘

STEP 1: EXTRACTION
─────────────────────────────────────────────────────────────────────────────
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│   API Auth   │────▶│  Fetch Data  │────▶│  Validate    │────▶│ Save JSON  │
│ (OAuth JWT)  │     │ (Paginated)  │     │ (Pydantic)   │     │ (data/raw) │
└──────────────┘     └──────────────┘     └──────────────┘     └────────────┘
                                                │
                                                ▼
                                         ┌────────────┐
                                         │Invalid JSON│
                                         │  (DLQ)     │
                                         └────────────┘

STEP 2: LOADING
─────────────────────────────────────────────────────────────────────────────
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  Read JSON   │────▶│  Validate    │────▶│  Bulk Load   │────▶│ PostgreSQL │
│   Files      │     │  (Pydantic)  │     │ (COPY cmd)   │     │ (raw.*)    │
└──────────────┘     └──────────────┘     └──────────────┘     └────────────┘
                           │
                           ▼
                    ┌────────────────┐
                    │raw.invalid_rec │
                    │     ords       │
                    └────────────────┘

STEP 3: TRANSFORMATION (dbt)
─────────────────────────────────────────────────────────────────────────────
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  raw.* JSONB │────▶│JSON Extract  │────▶│ Clean/Cast   │────▶│staging.stg_│
│   Tables     │     │ (->>'key')   │     │ Deduplicate  │     │   *        │
└──────────────┘     └──────────────┘     └──────────────┘     └────────────┘
                                                                     │
                                                                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│  marts.*     │◀────│Surrogate Keys│◀────│ Business     │◀────│  staging.* │
│  dim_/fact_  │     │  (MD5 Hash)  │     │  Logic       │     │   Views    │
└──────────────┘     └──────────────┘     └──────────────┘     └────────────┘
```

### API Endpoints Extracted

| Endpoint | Description | Target Table |
|----------|-------------|--------------|
| `/products` | Product catalog | `raw.products` |
| `/customers` | Customer profiles | `raw.customers` |
| `/sellers` | Seller information | `raw.sellers` |
| `/orders` | Order headers | `raw.orders` |
| `/orders/reviews/` | Customer reviews | `raw.order_reviews` |
| `/orders/payments/` | Payment transactions | `raw.order_payments` |
| `/orders/items/` | Order line items | `raw.order_items` |

---

## ETL Pipeline Details

### 1. Extraction Phase

#### API Client (`core/client.py`)

The API client handles:
- **Authentication**: OAuth2 with JWT tokens
- **Retry Logic**: Exponential backoff for transient failures
- **Connection Pooling**: Reuses HTTP connections for efficiency
- **Error Logging**: Categorized error tracking

```python
class APIClient:
    """HTTP client with authentication, retry logic, and error handling."""
    
    def __init__(self, base_url, username, password, max_retries=3):
        self.token_manager = TokenManager(base_url, username, password)
        self.error_logger = ErrorLogger()
        self.session = self._create_session(max_retries)
```

#### Token Manager (`core/token_manager.py`)

Handles OAuth token lifecycle:
- **Login**: Initial authentication
- **Refresh**: Automatic token refresh before expiry (60-second buffer)
- **Thread-safe**: Concurrent token access protection

```python
class TokenManager:
    def __init__(self, base_url, username, password, refresh_buffer=60):
        self.expires_at = 0
        self.refresh_buffer = refresh_buffer
    
    def ensure_valid_token(self):
        if time.time() > self.expires_at:
            self.refresh()
```

#### Data Extractor (`extraction/data_extractor.py`)

Orchestrates the extraction process:
- **Pagination**: Fetches all pages from paginated endpoints
- **Idempotency**: Skips unchanged data using MD5 hash comparison
- **Retry Logic**: Retries failed extractions with exponential backoff
- **Validation**: Validates data against Pydantic schemas

```python
class DataExtractor:
    def extract_endpoint(self, endpoint, force=False):
        # Check if extraction should be skipped
        should_skip, reason = self.metadata_manager.should_skip(endpoint, force)
        if should_skip:
            return {'status': 'skipped', 'reason': reason}
        
        # Fetch all pages
        data = self._fetch_all_pages(endpoint)
        
        # Check if data changed
        data_hash = compute_data_hash(data)
        if self.metadata_manager.data_unchanged(endpoint, data_hash):
            return {'status': 'unchanged'}
        
        # Validate and save
        valid_records, invalid_records = validate_schema(data, endpoint)
        save_extraction_data(endpoint, valid_records)
```

#### Metadata Manager (`extraction/metadata_manager.py`)

Tracks extraction history for idempotency:
- **Last extraction timestamp**: Skip if extracted within 1 hour
- **Data hash**: Skip if data hasn't changed
- **History**: Maintains last 10 extraction records

### 2. Loading Phase

#### Raw Loader (`load_raw_data.py`)

Loads JSON files into PostgreSQL:
- **JSONB Storage**: Raw data stored as JSONB for flexibility
- **Bulk Insert**: Uses PostgreSQL COPY command for performance
- **Validation**: Second validation layer before loading
- **Invalid Handling**: Routes invalid records to `raw.invalid_records`

```python
def load_file_to_table_bulk(engine, filepath, table_config):
    # 1. Read JSON file
    raw_records = read_json_file(filepath)
    
    # 2. Prepare tables (create if not exists, truncate)
    prepare_tables(engine, table_name)
    
    # 3. Validate and split
    valid_batch, invalid_batch = validate_and_split(raw_records, schema_model)
    
    # 4. Bulk load valid records
    bulk_insert_csv(engine, table_name, valid_batch, columns=["data"])
    
    # 5. Log invalid records
    bulk_insert_csv(engine, INVALID_TABLE, invalid_batch, 
                   columns=["source_table", "raw_payload", "error_message"])
```

### 3. Transformation Phase (dbt)

#### Staging Layer

Staging models are materialized as **views** and perform:
- **JSON Extraction**: Extract fields from JSONB using `->>` operator
- **Data Type Casting**: Convert strings to appropriate types
- **Data Cleaning**: Handle nulls, trim whitespace, standardize formats
- **Deduplication**: Remove duplicate records using `DISTINCT ON`
- **Date Parsing**: Handle multiple date formats (ISO, DD/MM/YYYY, Unix epoch)

Example: `stg_orders.sql`
```sql
WITH json_extraction AS (
    SELECT
        data->>'order_id' as order_id,
        data->>'order_status' as order_status,
        data->>'order_purchase_timestamp' as order_purchase_timestamp
    FROM {{ source('ecommerce_raw', 'orders') }}
),

deduplicated AS (
    SELECT DISTINCT ON (order_id) * FROM json_extraction
)

SELECT
    order_id,
    LOWER(TRIM(order_status)) as order_status,
    -- Handle multiple date formats
    CASE 
        WHEN order_purchase_timestamp ~ '^\d+(\.\d+)?$' 
            THEN to_timestamp(order_purchase_timestamp::double precision)
        WHEN order_purchase_timestamp ~ '^\d{1,2}/\d{1,2}/\d{4}' 
            THEN to_timestamp(order_purchase_timestamp, 'DD/MM/YYYY HH24:MI:SS')
        ELSE CAST(order_purchase_timestamp AS TIMESTAMP)
    END AS purchase_at
FROM deduplicated
```

#### Marts Layer

Marts models are materialized as **tables** and implement:
- **Dimensional Modeling**: Star schema with dimension and fact tables
- **Surrogate Keys**: MD5 hash-based surrogate keys
- **Date Keys**: Integer date keys (YYYYMMDD format)
- **Derived Metrics**: Business metrics calculated from raw data
- **Foreign Key Relationships**: Links between facts and dimensions

---

## Database Design

### Medallion Architecture

The pipeline follows the **Medallion Architecture** pattern:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MEDALLION ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐                │
│   │   BRONZE    │      │   SILVER    │      │    GOLD     │                │
│   │   (raw)     │─────▶│  (staging)  │─────▶│   (marts)   │                │
│   │             │      │             │      │             │                │
│   │ • Raw JSONB │      │ • Cleaned   │      │ • Star      │                │
│   │ • As-is     │      │ • Typed     │      │   Schema    │                │
│   │ • Immutable │      │ • Deduped   │      │ • Aggregated│                │
│   │             │      │ • Views     │      │ • Tables    │                │
│   └─────────────┘      └─────────────┘      └─────────────┘                │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────┐                                                          │
│   │  INVALID    │                                                          │
│   │ (invalid)   │                                                          │
│   │             │                                                          │
│   │ • DLQ       │                                                          │
│   │ • Errors    │                                                          │
│   │ • Audit     │                                                          │
│   └─────────────┘                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Schemas

| Schema | Purpose | Materialization |
|--------|---------|-----------------|
| `raw` | Raw JSONB data as extracted from API | Tables (JSONB) |
| `staging` | Cleaned and typed data | Views |
| `marts` | Dimensional model for analytics | Tables |
| `invalid` | Invalid/failed records for debugging | Tables |

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DIMENSIONAL MODEL (STAR SCHEMA)                      │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────────┐
                              │    dim_date      │
                              ├──────────────────┤
                              │ date_key (PK)    │
                              │ date             │
                              │ year             │
                              │ month            │
                              │ day              │
                              └────────▲─────────┘
                                       │
    ┌──────────────────┐               │               ┌──────────────────┐
    │   dim_customer   │               │               │   dim_product    │
    ├──────────────────┤               │               ├──────────────────┤
    │ customer_key (PK)│               │               │ product_key (PK) │
    │ customer_id      │               │               │ product_id       │
    │ customer_city    │               │               │ product_category │
    │ customer_state   │               │               │ weight_g         │
    │ zip_code         │               │               │ volume_cm3       │
    └────────▲─────────┘               │               └────────▲─────────┘
             │                         │                        │
             │    ┌────────────────────┴────────────────────┐   │
             │    │                                         │   │
             │    │              FACT TABLES                │   │
             │    │                                         │   │
             │    ├─────────────────────────────────────────┤   │
             │    │                                         │   │
    ┌────────┴────┴───────┐               ┌────────────────┴───┴───────┐
    │    fact_orders      │               │    fact_order_items        │
    ├─────────────────────┤               ├────────────────────────────┤
    │ order_key (PK)      │◀──────────────│ order_item_sk (PK)         │
    │ order_id            │               │ order_key (FK)             │
    │ customer_key (FK)   │               │ product_key (FK)           │
    │ order_status_key(FK)│               │ seller_key (FK)            │
    │ purchase_date_key   │               │ price                      │
    │ time_to_approve_hrs │               │ freight_value              │
    │ days_to_ship        │               │ total_item_value           │
    │ total_order_price   │               └────────────────────────────┘
    └─────────────────────┘
             │
             │    ┌─────────────────────┐     ┌─────────────────────┐
             │    │   fct_payments      │     │    fct_reviews      │
             │    ├─────────────────────┤     ├─────────────────────┤
             └───▶│ payment_sk (PK)     │     │ review_id (PK)      │
                  │ order_id (FK)       │     │ order_id (FK)       │
                  │ customer_id         │     │ customer_id         │
                  │ installments        │     │ review_score        │
                  │ payment_value       │     │ response_time_hours │
                  └─────────────────────┘     └─────────────────────┘

    ┌──────────────────┐     ┌────────────────────┐     ┌──────────────────┐
    │   dim_seller     │     │ dim_order_status   │     │dim_payment_method│
    ├──────────────────┤     ├────────────────────┤     ├──────────────────┤
    │ seller_key (PK)  │     │ order_status_key   │     │payment_method_key│
    │ seller_id        │     │ status_name        │     │ payment_type     │
    │ seller_city      │     │ is_canceled        │     └──────────────────┘
    │ seller_state     │     │ is_completed       │
    └──────────────────┘     └────────────────────┘
```

---

## Data Models

### Staging Models

| Model | Description | Key Transformations |
|-------|-------------|---------------------|
| `stg_customers` | Customer staging | City/state normalization, INITCAP |
| `stg_orders` | Order headers | Multi-format date parsing, status normalization |
| `stg_order_items` | Order line items | Price/freight casting, date handling |
| `stg_order_payments` | Payments | Base64 decoding, type casting |
| `stg_order_reviews` | Reviews | Comment cleaning, date parsing |
| `stg_products` | Products | Base64 category decoding, numeric casting |
| `stg_sellers` | Sellers | City/state normalization |
| `invalid_products` | Failed validations | Captures validation failures |

### Dimension Tables

| Model | Description | Key Columns |
|-------|-------------|-------------|
| `dim_customer` | Customer dimension | customer_key, customer_id, city, state, zip |
| `dim_product` | Product dimension | product_key, category, weight_g, volume_cm3 |
| `dim_seller` | Seller dimension | seller_key, seller_id, city, state |
| `dim_date` | Date dimension | date_key, year, month, day (2016-2020) |
| `dim_order_status` | Order status lookup | status_key, is_canceled, is_completed |
| `dim_payment_method` | Payment types | payment_method_key, payment_type |
| `dim_review_detail` | Review content | review_detail_key, sentiment |

### Fact Tables

| Model | Description | Key Metrics |
|-------|-------------|-------------|
| `fact_orders` | Order transactions | time_to_approve_hours, days_to_ship, total_order_price |
| `fact_order_items` | Line item facts | price, freight_value, total_item_value |
| `fct_payments` | Payment facts | installments, payment_value |
| `fct_reviews` | Review facts | review_score, response_time_hours |

### Key Business Metrics Derived

| Metric | Source Model | Calculation |
|--------|--------------|-------------|
| **Time to Approve** | fact_orders | `approved_at - purchase_at` (hours) |
| **Days to Ship** | fact_orders | `delivered_at - purchase_at` (days) |
| **Delivery Variance** | fact_orders | `estimated_delivery - actual_delivery` (days) |
| **Response Time** | fct_reviews | `review_answer - review_creation` (hours) |
| **Sentiment** | dim_review_detail | Based on review_score (Positive/Neutral/Negative) |
| **Total Item Value** | fact_order_items | `price + freight_value` |
| **Product Volume** | dim_product | `length × height × width` |

---

## Data Quality & Testing

### Validation Strategies

#### 1. Extraction Validation (Pydantic)

```python
class BaseSchema(BaseModel):
    model_config = ConfigDict(extra='forbid')  # Strict validation

class Customer(BaseSchema):
    customer_id: str
    customer_unique_id: str
    customer_zip_code_prefix: str
    customer_city: str
    customer_state: str
```

**Key Features:**
- `extra='forbid'`: Rejects unexpected fields (alerts on schema changes)
- Required field validation
- Type coercion with strict mode

#### 2. Loading Validation

Second validation pass during loading:
- Split records into valid/invalid buckets
- Route invalid records to `raw.invalid_records` table
- Preserve original payload for debugging

#### 3. dbt Tests

**Schema Tests** (`schema.yml`):
```yaml
models:
  - name: stg_customers
    columns:
      - name: customer_id
        tests:
          - unique
          - not_null
```

**Custom Tests**:

1. **Payment Reconciliation** (`assert_order_payments_match_order_totals.sql`):
```sql
-- Ensures payment totals match order totals (within $1 tolerance)
SELECT order_id
FROM order_totals o
JOIN payment_totals p ON o.order_id = p.order_id
WHERE ABS(o.expected_total - p.actual_paid) > 1.00
```

2. **Delivery Date Validation** (`assert_valid_delivery_dates.sql`):
```sql
-- Ensures delivery date is after purchase date
SELECT order_id
FROM stg_orders
WHERE delivered_at < purchase_at
  AND delivered_at IS NOT NULL
```

### dbt Macros for Data Quality

```sql
-- Safe numeric casting with NaN/null handling
{% macro safe_cast_numeric(column_name, default_value=0) %}
    CAST(NULLIF(NULLIF(NULLIF({{ column_name }}, ''), 'NaN'), 'null') AS NUMERIC)
{% endmacro %}

-- Validate not null and not empty
{% macro validate_not_null(column_name) %}
    {{ column_name }} IS NOT NULL 
    AND {{ column_name }} != '' 
    AND {{ column_name }} != 'null'
{% endmacro %}
```

### Source Freshness Monitoring

```yaml
sources:
  - name: ecommerce_raw
    tables:
      - name: orders
        loaded_at_field: loaded_at
        freshness:
          warn_after: {count: 12, period: hour}
          error_after: {count: 24, period: hour}
```

---

## Configuration Management

### Environment Variables

Create a `.env` file based on `.env_example`:

```bash
# API Configuration
API_BASE_URL=http://localhost:8000/api/v1
USER_NAME=your_username
PASSWORD=your_password

# Database Configuration
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecom_db

# Schema Names
RAW_SCHEMA=raw
STAGING_SCHEMA=staging
MARTS_SCHEMA=marts
INVALID_SCHEMA=invalid

# API Behavior
MAX_RETRIES=3
RETRY_BACKOFF=1.0
REQUEST_TIMEOUT=30
DEFAULT_PAGE_LIMIT=100
```

### Centralized Settings (`config/settings.py`)

Uses Pydantic Settings for type-safe configuration:

```python
class Settings(BaseSettings):
    # API Configuration
    api_base_url: str
    username: Optional[str]
    password: Optional[str]
    
    # Database Configuration
    db_user: str
    db_password: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
```

### dbt Configuration

**profiles.yml**:
```yaml
ecom_transformation:
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: postgres
      pass: postgres
      dbname: ecom_db
      schema: raw
      threads: 1
  target: dev
```

**dbt_project.yml**:
```yaml
models:
  ecom_transformation:
    staging:
      +materialized: view
      +schema: staging
    marts:
      +materialized: table
      +schema: marts
```

---

## Setup Instructions

### Prerequisites

1. **Python 3.11+** installed
2. **PostgreSQL 16+** installed and running
3. **API access** credentials (username/password)

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd dbt_ecom1
```

#### 2. Create Virtual Environment

```bash
python -m venv env
.\env\Scripts\Activate.ps1  # Windows PowerShell
# or
source env/bin/activate  # Linux/Mac
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Copy example environment file
copy .env_example .env  # Windows
# cp .env_example .env  # Linux/Mac

# Edit .env with your configuration
```

#### 5. Set Up Database

```sql
-- Create database
CREATE DATABASE ecom_db;

-- Create schemas (optional - pipeline creates if missing)
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS invalid;
```

#### 6. Install dbt Dependencies

```bash
cd ecom_transformation
dbt deps
```

#### 7. Test dbt Connection

```bash
dbt debug
```

---

## Usage Guide

### Running the Full Pipeline

#### Step 1: Extract Data from API

```bash
cd etl_pipeline
python run_extraction.py
```

**Expected Output:**
```
======================================================================
Starting Extraction from http://localhost:8000/api/v1
Batch Size: 100 records per request
======================================================================

[+] Extracting: products...
   [OK] Success: 32951 valid, 2 invalid

[+] Extracting: customers...
   [OK] Success: 99441 valid, 0 invalid
...

======================================================================
Extraction Summary:
  Total Endpoints: 7
  [OK] Successful: 7
  [FAIL] Failed: 0
  [SKIP] Skipped: 0
  [SAME] Unchanged: 0
======================================================================
```

#### Step 2: Load Raw Data to PostgreSQL

```bash
python load_raw_data.py
```

**Expected Output:**
```
2024-01-15 10:30:00 - INFO - Validating 32951 records for products...
2024-01-15 10:30:05 - INFO -    -> Loaded 32949 VALID records to raw.products
2024-01-15 10:30:05 - WARNING -    -> Moved 2 INVALID records to raw.invalid_records
...
```

#### Step 3: Run dbt Transformations

```bash
cd ecom_transformation

# Run all models
dbt run

# Or run specific layers
dbt run --select staging.*
dbt run --select marts.*
```

#### Step 4: Run dbt Tests

```bash
# Run all tests
dbt test

# Run specific test
dbt test --select assert_order_payments_match_order_totals
```

#### Step 5: Generate Documentation

```bash
dbt docs generate
dbt docs serve
```

### Common Commands

| Command | Description |
|---------|-------------|
| `python run_extraction.py` | Extract data from API |
| `python load_raw_data.py` | Load JSON to PostgreSQL |
| `dbt run` | Run all dbt models |
| `dbt run --select staging.*` | Run staging models only |
| `dbt run --select marts.*` | Run marts models only |
| `dbt test` | Run all tests |
| `dbt source freshness` | Check source freshness |
| `dbt docs generate && dbt docs serve` | Generate and serve docs |

### Force Re-extraction

```bash
# To force extraction even if data unchanged
# Modify run_extraction.py: extract_endpoint(endpoint, force=True)
```

---

## Engineering Decisions

### Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **ELT over ETL** | Leverage dbt and PostgreSQL's processing power for transformations |
| **JSONB Storage** | Flexibility for schema evolution; extract during transformation |
| **Medallion Architecture** | Clear separation of concerns; easy debugging and reprocessing |
| **Star Schema** | Optimized for analytical queries; intuitive for BI tools |
| **MD5 Surrogate Keys** | Deterministic; no auto-increment issues; idempotent loads |

### Technology Choices

| Technology | Why Chosen | Alternatives Considered |
|------------|------------|------------------------|
| **PostgreSQL** | Mature, JSONB support, excellent dbt integration | MySQL, DuckDB |
| **dbt Core** | SQL-based transformations, testing, documentation | Pandas, Spark |
| **Pydantic** | Type-safe validation, clear error messages | Marshmallow, Cerberus |
| **Requests** | Simple, reliable, retry support | httpx, aiohttp |

### Data Quality Trade-offs

| Trade-off | Decision | Reasoning |
|-----------|----------|-----------|
| **Strict vs Lenient Validation** | Strict (`extra='forbid'`) | Alerts on schema drift; prevents silent failures |
| **Fail Fast vs Continue** | Route invalid to DLQ | Preserves valid data while tracking issues |
| **Real-time vs Batch** | Batch with idempotency | Simpler; API rate limits; cost-effective |

### Performance Optimizations

| Optimization | Implementation |
|--------------|----------------|
| **Connection Pooling** | SQLAlchemy QueuePool (5 connections, 10 overflow) |
| **Bulk Insert** | PostgreSQL COPY command |
| **HTTP Session Reuse** | requests.Session with HTTPAdapter |
| **Incremental Models** | dbt incremental for products |
| **Hash-based Change Detection** | MD5 hash comparison to skip unchanged data |

### Known Limitations

1. **No Real-time Processing**: Batch-only; minimum 1-hour extraction interval
2. **Single Database**: No read replicas or sharding
3. **No Orchestration**: Manual script execution (could add Airflow/Luigi)
4. **Limited Error Recovery**: Failed extractions require manual intervention

### Future Improvements

1. **Add Orchestration**: Implement Apache Airflow or Prefect
2. **Add Monitoring**: Prometheus metrics, Grafana dashboards
3. **Add CDC**: Change Data Capture for near-real-time updates
4. **Add API Layer**: RESTful API for data access (FastAPI skeleton exists)
5. **Add Visualization**: Power BI or Metabase dashboards

---

## Appendix

### A. Source Data Samples

#### Customers JSON
```json
{
  "customer_id": "06b8999e2fba1a1fbc88172c00ba8bc7",
  "customer_unique_id": "861eff4711a542e4b93843c6dd7febb0",
  "customer_zip_code_prefix": "14409",
  "customer_city": "franca",
  "customer_state": "SP"
}
```

#### Orders JSON (with data quality issues)
```json
{
  "order_id": "4cbf1cc60a2d1704a70e11ee8be1510a",
  "customer_id": "406c8e1382162dc6bef214e0c01fc297",
  "order_status": "delivered",
  "order_purchase_timestamp": "2018-01-01 17:03:13",
  "order_approved_at": "01/01/2018 17:11:48",  // Different date format
  "order_delivered_customer_date": "1515591930",  // Unix epoch
  "order_estimated_delivery_date": "2018-01-30 00:00:00"
}
```

#### Products JSON (with Base64 encoding)
```json
{
  "product_id": "5b951e54437768080925aabe01e24348",
  "product_category_name": "YWdyb19pbmR1c3RyaWFfZV9jb21lcmNpbw==",  // Base64
  "product_category_name_english": " agro industry and commerce ",
  "product_weight_g": "380.0",
  "product_length_cm": "22.0"
}
```

### B. Error Codes

| Error Type | Description | Action |
|------------|-------------|--------|
| `auth_failure` | Authentication failed | Check credentials |
| `token_refresh_failure` | Token refresh failed | Re-authenticate |
| `api_4xx` | Client error (400-499) | Check request parameters |
| `api_5xx` | Server error (500-599) | Retry with backoff |
| `api_timeout` | Request timeout | Increase timeout or retry |
| `api_connection_error` | Connection failed | Check network/API availability |

### C. Glossary

| Term | Definition |
|------|------------|
| **ELT** | Extract, Load, Transform - load raw data first, then transform |
| **dbt** | Data Build Tool - SQL-based transformation framework |
| **JSONB** | Binary JSON storage in PostgreSQL |
| **Surrogate Key** | Artificial key (e.g., MD5 hash) replacing natural key |
| **Idempotent** | Operation that produces same result when run multiple times |
| **DLQ** | Dead Letter Queue - storage for failed/invalid records |
| **Medallion Architecture** | Bronze/Silver/Gold data layers |

---

*Document Version: 1.0*  
*Last Updated: February 2026*
