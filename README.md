# Logpose Core

Shared database schema, SQLAlchemy models, search serialization, and provider normalization helpers for Logpose.

Both sibling runtime projects use this package:

```bash
../logpose-api
../logpose-jobs
```

## Local Database

Start Postgres/PostGIS:

```bash
npm run db:up
```

Initialize or update the schema:

```bash
npm run init-db
```

Connection string:

```bash
postgresql+psycopg://logpose:logpose@localhost:54322/logpose
```

For local sibling projects, include this directory on `PYTHONPATH`:

```bash
PYTHONPATH=../logpose-core
```
