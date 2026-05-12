# ChatBI Demo Data

This directory contains demo business data for testing ChatBI end to end.

`chatbi.db` is the lite-mode application database used by the backend. It is not
committed because it contains local runtime state.

## Files

- `demo-postgres.sql` - PostgreSQL demo datasource for ChatBI. Use this for real
  ChatBI schema sync, SQL generation, and query execution tests.
- `demo-sqlite.sql` - SQLite version of the same dataset for quick local
  inspection outside ChatBI.

## PostgreSQL Setup

ChatBI currently executes user queries against PostgreSQL datasources. Create a
separate demo database and load the data:

```bash
createdb chatbi_demo
psql -d chatbi_demo -f data/demo-postgres.sql
```

Then add a datasource in ChatBI:

```text
Name: Demo Sales
Type: postgres
Host: localhost
Port: 5432
Database: chatbi_demo
Username: chatbi_demo_readonly
Password: chatbi_demo_readonly
Readonly user: chatbi_demo_readonly
Readonly password: chatbi_demo_readonly
```

If the backend runs inside Docker Compose and PostgreSQL is the `postgres`
service, use `Host: postgres` instead of `localhost`.

After creating the datasource, run schema sync in the admin UI.

## Useful Test Questions

- What is total net sales by month?
- Which product categories generated the most revenue?
- Show revenue by customer segment and region.
- What is the return rate by product?
- Which channels have the highest average order value?
- Show inventory available by product and warehouse region.
