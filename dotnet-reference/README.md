# .NET Reference: Semantic Search Against This Course's Database

This isn't an official course module or a required exercise — it's a
single reference file for anyone in the room who's more comfortable in
C#/.NET and is curious how the same pattern you're building in
Python/SQL looks in that world. It's meant to be read and discussed, not
completed as a lab.

It reproduces the core "aha" moment from Module 05 (semantic search) and
the Day 2 capstone (real embeddings, not keyword matching): connect to
Postgres, get a real embedding for a search phrase from Ollama, and use
pgvector's `<=>` operator to find the closest matches -- against the
same `items` table already populated by the course's Python labs.

## What it maps to

| This course (Python/SQL) | .NET equivalent |
|---|---|
| `psycopg` | `Npgsql` |
| storing/reading a `vector(1024)` column | `Pgvector` (the `Pgvector.Npgsql` package registers the type with Npgsql) |
| calling Ollama with `requests` | calling Ollama with `HttpClient` |
| `embedding <=> '[...]'` in raw SQL | the exact same `<=>` operator, just parameterized with a `Vector` object instead of a string literal |

## Prerequisites

- .NET 8 SDK
- The course's Docker services already running (`docker compose up -d` from `environment/`)
- The `items` table already populated (it is, from Module 03/05's labs)

## Running it

```bash
cd dotnet-reference
dotnet run "artificial intelligence and machine learning"
```

It'll print the top 5 closest `items` rows by cosine distance, same as
the SQL queries you've already run by hand in Module 05.

## A note on testing

This was written and carefully checked against the documented APIs of
`Npgsql` and `Pgvector.Npgsql`, but it hasn't been compiled -- there's no
.NET SDK available in the environment this was written in. Please run
`dotnet build` once before showing it live, in case a package version or
API detail needs a small adjustment.
