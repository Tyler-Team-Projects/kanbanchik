#!/usr/bin/env bash
docker-compose up -d

echo "Wait PostgreSQL..."
until docker exec kanban_postgres pg_isready -U mcvent -d kanbanchick > /dev/null 2>&1; do
    sleep 1
done
echo "PostgreSQL is ready"
echo "Do alembic upgrade head..."
alembic upgrade head
uvicorn app.main:app --reload
