#!/bin/bash
# seed.sh - Provision API keys and set budgets for Loopers and LiteLLM local proxies.
# Retrieved 2026-05-31

set -e

MODE=$1

if [ -z "$MODE" ]; then
  echo "Usage: ./seed.sh [--leak|--uncap|--reset]"
  exit 1
fi

if command -v docker-compose &> /dev/null; then
  DOCKER_COMPOSE="docker-compose"
else
  DOCKER_COMPOSE="docker compose"
fi

# Static loopers key matching the regex: ^lp-[a-zA-Z0-9]{43}$
LOOPERS_KEY="lp-looperstestkey12345678901234567890123456789"
# SHA-256 hash of the loopers key
LOOPERS_HASH="b168b4e75b33ee699d775588c229f7206c3e6890bbc8514310108aec4af35082"

if [ "$MODE" = "--leak" ]; then
  echo "Setting budget limit to \$0.01 for both proxies..."
  
  # Loopers key creation via direct Redis HSET commands
  $DOCKER_COMPOSE exec -T redis redis-cli HSET "loopers:key:$LOOPERS_HASH" \
    name "loopers-test" \
    provider "openai" \
    created_at "$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")" \
    active "true" > /dev/null
    
  # Loopers budget configuration (set across all windows to ensure strict coverage)
  $DOCKER_COMPOSE exec -T redis redis-cli HSET "loopers:budget:$LOOPERS_HASH:config" \
    minute "0.01" \
    hourly "0.01" \
    daily "0.01" \
    weekly "0.01" \
    monthly "0.01" > /dev/null
  
  # LiteLLM key creation with custom key specified (matches k6 scripts)
  curl -s -X POST http://localhost:4001/key/generate \
    -H "Authorization: Bearer sk-litellm-master" \
    -H "Content-Type: application/json" \
    -d '{"key": "sk-litellm-test", "key_alias": "sk-litellm-test", "max_budget": 0.01, "budget_duration": "1d"}' > /dev/null
  
  echo "Keys seeded successfully!"

elif [ "$MODE" = "--uncap" ]; then
  echo "Uncapping budgets to \$999,999..."
  
  # Loopers budget update in Redis
  $DOCKER_COMPOSE exec -T redis redis-cli HSET "loopers:budget:$LOOPERS_HASH:config" \
    minute "999999" \
    hourly "999999" \
    daily "999999" \
    weekly "999999" \
    monthly "999999" > /dev/null
  
  # LiteLLM key update
  curl -s -X POST http://localhost:4001/key/update \
    -H "Authorization: Bearer sk-litellm-master" \
    -H "Content-Type: application/json" \
    -d '{"key": "sk-litellm-test", "max_budget": 999999}' > /dev/null
    
  echo "Budgets uncapped successfully!"

elif [ "$MODE" = "--reset" ]; then
  echo "Resetting states..."
  
  # Delete Loopers keys and configs in Redis
  $DOCKER_COMPOSE exec -T redis redis-cli DEL "loopers:key:$LOOPERS_HASH" > /dev/null
  $DOCKER_COMPOSE exec -T redis redis-cli DEL "loopers:budget:$LOOPERS_HASH:config" > /dev/null
  
  # Flush Redis database entirely to clear current spend tracking
  $DOCKER_COMPOSE exec -T redis redis-cli FLUSHALL > /dev/null
  
  # LiteLLM delete key
  curl -s -X POST http://localhost:4001/key/delete \
    -H "Authorization: Bearer sk-litellm-master" \
    -H "Content-Type: application/json" \
    -d '{"keys": ["sk-litellm-test"]}' > /dev/null
    
  echo "State reset successfully!"
fi
