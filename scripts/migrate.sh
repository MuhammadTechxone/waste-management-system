#!/bin/bash

# Database migration helper script
# Usage: ./scripts/migrate.sh [upgrade|downgrade|current|revision]

set -e

COMMAND=${1:-upgrade}
MESSAGE=${2:-"Auto-generated migration"}

echo "🗄️  Database Migration Helper"
echo "Command: $COMMAND"

case $COMMAND in
    upgrade)
        echo "📈 Upgrading database schema..."
        alembic upgrade head
        echo "✅ Database upgraded successfully"
        ;;
    
    downgrade)
        echo "📉 Downgrading database schema..."
        alembic downgrade -1
        echo "✅ Database downgraded successfully"
        ;;
    
    current)
        echo "📋 Current database revision:"
        alembic current --verbose
        ;;
    
    revision)
        echo "✍️  Creating new migration: $MESSAGE"
        alembic revision --autogenerate -m "$MESSAGE"
        echo "✅ Migration created. Review alembic/versions/ and apply with: alembic upgrade head"
        ;;
    
    history)
        echo "📜 Migration history:"
        alembic history --verbose
        ;;
    
    *)
        echo "❌ Unknown command: $COMMAND"
        echo "Usage: $0 [upgrade|downgrade|current|revision|history]"
        exit 1
        ;;
esac
