## HONOR Supervisor Hub — Data Engineer Roadmap & TODOs

Audience: Recruiters and collaborators. This document outlines the MVP scope and DE-focused enhancements with clear, verifiable outcomes.

### 0) MVP Definition (Product + Data)
- [X] Define target personas and core flows (Supervisor, Promoter)
- [X] Agree on minimal entities and relationships (users, user_types, regions, cities, stores, market_centers, clients, pending_*)
- [ ] Acceptance criteria documented per feature (login, dashboard, approvals)

### 1) Data Model & Migrations
- [X] Finalize SQLAlchemy models and alignment with migrations (Alembic)
- [X] Enforce types and constraints (PKs, FKs, unique, not-null)
- [ ] Add idempotent migration scripts and downgrade paths
- [ ] Document model diagram (Mermaid/DBML) in docs/

### 2) Ingestion & Seeding (DE-Focus)
- [ ] Prepare realistic seed datasets: users, stores, user_types, regions/cities, market_centers, pending_* (CSV/JSON)
- [ ] CLI: `flask populate_table <table> <file>` — extend with schema validation and dry-run
- [ ] Implement idempotent upserts (keyed on business keys)
- [ ] Add ingestion logs (row counts, rejects), write to logs/ and DB table `ingestion_runs`

### 3) Data Quality & Validation
- [ ] Schema checks (fields present, types castable)
- [ ] Uniqueness (user ids, store codes)
- [ ] Referential integrity (FK existence: supervisor_id, city_id, province_id)
- [ ] Business rules (status in {ACTIVE, PENDING}, role names in allowed set, phone formats)
- [ ] Summary report per load (pass/fail with metrics)

### 4) Transformations & Analytics Tables
- [ ] Materialize daily aggregates: promoters per supervisor, stores per supervisor, approvals per day
- [ ] Denormalized reporting table for dashboard (precomputed counts)
- [ ] Partition strategy (by day) and retention policy notes
- [ ] Backfill job for historical recompute

### 5) Analytics API & Caching
- [ ] JSON endpoints to expose metrics (e.g., `/api/metrics/supervisor/<id>`) 
- [ ] Lightweight caching (per-user, short TTL)
- [ ] Pagination for list endpoints

### 6) Observability
- [ ] Structured logging (JSON), include request_id and user_id
- [ ] Basic metrics (ingestion rows, reject counts, API latency)
- [ ] Error handling: standardized JSON errors with codes

### 7) Testing
- [ ] Unit tests for validators and transformations
- [ ] E2E tests with a seeded SQLite DB (fixtures)
- [ ] CLI tests (dry-run vs commit)

### 8) Security & Ops
- [ ] Protect debug endpoints (authz), remove in production
- [ ] Add CSP and avoid inline scripts in templates
- [ ] Environment-driven configuration (DATABASE_URL, SECRET_KEY)

### 9) Templates Generation Phase (Project Highlight)
- [X] Dynamic model discovery for templates
- [X] CLI: `flask generate-all-templates data/` writes one file per model
- [X] CLI: `flask load-templates data/` loads and resets templates back to neutral
- [ ] Add `--only`, `--except`, `--dry-run` flags to loader
- [ ] FK-aware load order (topological sort by ForeignKey deps)
- [ ] Column-level hints via `column.info` (examples, required, default) to enrich templates
- [ ] Validation with Marshmallow schemas; strict/lenient modes
- [ ] Upsert with natural keys; `--diff` preview before commit

### 10) Documentation (Recruiter-Friendly)
- [ ] Architecture overview diagram
- [ ] Data flow (ingestion → validation → storage → transforms → API → UI)
- [ ] Runbook: local setup, seed data, run ETL, view metrics
- [ ] Tradeoffs & decisions (why SQLite, why Alembic, role naming strategy)
- [ ] Future work (scaling to Postgres, Airflow/DBT integration)

---

### Execution Plan
1) Lock MVP scope (#0)
2) Models/Migrations (#1)
3) Ingestion + DQ (#2–#3)
4) Analytics tables (#4) and APIs (#5)
5) Observability, testing, docs (#6–#7–#10)
6) Templates generation phase (#9)

### Status Log
- Created: TODO scaffold for DE roadmap
- Next Action: Lock MVP scope and acceptance criteria


