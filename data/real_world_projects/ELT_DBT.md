# E-Commerce ELT Pipeline Documentation

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


#### Data Extractor (`extraction/data_extractor.py`)

Orchestrates the extraction process:
- **Pagination**: Fetches all pages from paginated endpoints
- **Idempotency**: Skips unchanged data using MD5 hash comparison
- **Retry Logic**: Retries failed extractions with exponential backoff
- **Validation**: Validates data against Pydantic schemas


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



