# Logpose Core

Shared database schema, SQLAlchemy models, search serialization, and provider normalization helpers for Logpose.

Both sibling runtime projects use this package:

```bash
../logpose-api
../logpose-jobs
```

## Install

Runtime projects should depend on the public GitHub package:

```txt
logpose-core @ git+https://github.com/ambidextrous-dev/logpose-core.git@develop
```

Local sibling projects can test unpublished core changes by installing this checkout in editable mode:

```bash
python3 -m pip install -e ../logpose-core
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

This is a local Docker-only example credential. Production database URLs belong in an ignored `.env` file or deployment secret store.

For local sibling projects, include this directory on `PYTHONPATH`:

```bash
PYTHONPATH=../logpose-core
```
