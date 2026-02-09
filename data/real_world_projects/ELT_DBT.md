# E-Commerce ELT Pipeline Documentation

## Project Overview

This is a **production-grade ELT (Extract, Load, Transform) pipeline** designed to extract data from an E-commerce REST API, validate and load raw data into PostgreSQL, and transform it using dbt into a dimensional data model suitable for analytics and reporting.

**Key Features:**
*   **Idempotency:** Skips already-extracted data using hash-based change detection.
*   **Resilience:** Centralized error logging, OAuth token management, and exponential backoff retries.
*   **Data Quality:** Pydantic schema validation and segregation of invalid records.
*   **Performance:** Connection pooling and bulk loading via PostgreSQL `COPY`.

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
API Extraction: Authenticate via OAuth, fetch paginated data from endpoints (orders, products, customers, etc.).
Validation: Validate structure using Pydantic; drop invalid records to a DLQ (Dead Letter Queue).
Staging: Save valid data as JSON files in data/raw/.
Loading: Bulk insert JSON files into PostgreSQL raw schema (JSONB columns).
Transformation: dbt processes raw data into Staging views and Mart tables.

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
Client: Handles OAuth JWT token refresh and thread-safe HTTP sessions.
Retries: Implements exponential backoff for transient API errors.
Metadata: Tracks last_extracted_at and data hashes to prevent processing unchanged data.
Endpoints Extracted: /products, /customers, /sellers, /orders, /orders/reviews, /orders/payments, /orders/items.

### 2. Loading Phase
Storage: Raw data is stored in JSONB format in PostgreSQL to maintain schema flexibility.
Performance: Uses the COPY command for high-speed bulk insertion.
Error Handling: Records failing database constraints are routed to raw.invalid_records tables for auditing.

### 3. Database Schemas
The pipeline uses a Medallion Architecture:
raw (Bronze): Immutable raw JSONB data and audit logs.
staging (Silver): Cleaned views with normalized types, deduplication, and casted columns.
marts (Gold): Dimensional models (Star Schema) optimized for BI tools.
invalid: Storage for data validation failures.

### 4. Transformation & Modeling
Dimension Tables:
dim_customer, dim_product, dim_seller, dim_date, dim_payment_method, dim_order_status.
Fact Tables:
fact_orders: Header-level metrics (timestamps, totals).
fact_order_items: Line-item metrics (price, freight).
fct_payments: Transaction details.
fct_reviews: Customer sentiment and ratings.

### 5. Key Business Metrics
The analytics layer derives the following insights:
Order Lifecycle: Time to Approve (hours), Days to Ship, Delivery Variance.
Financials: Total Item Value, Freight Costs, Average Order Value.
Quality: Review Sentiment Scores, Seller Response Times.



