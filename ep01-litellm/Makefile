.PHONY: up down check-health seed-leak seed-uncap test-leak test-throughput test-latency test-all

# Use docker compose plugin if docker-compose is not installed
DOCKER_COMPOSE := $(shell command -v docker-compose 2> /dev/null || echo "docker compose")

up:
	$(DOCKER_COMPOSE) up -d
	@echo "Waiting 5s for services to initialize..."
	@sleep 5

down:
	$(DOCKER_COMPOSE) down -v

seed-leak:
	bash ./seed.sh --leak

seed-uncap:
	bash ./seed.sh --uncap

test-leak:
	@echo "Running Budget Leak Test (Loopers)..."
	k6 run -e PROXY=loopers -e VUS=1000 -e DURATION=10s ../shared/harness/budget_leak_test.js
	@echo "Running Budget Leak Test (LiteLLM)..."
	k6 run -e PROXY=litellm -e VUS=1000 -e DURATION=10s ../shared/harness/budget_leak_test.js

test-throughput:
	@echo "Running Throughput Test (Loopers)..."
	k6 run -e PROXY=loopers ../shared/harness/throughput_test.js
	@echo "Running Throughput Test (LiteLLM)..."
	k6 run -e PROXY=litellm ../shared/harness/throughput_test.js

test-latency:
	@echo "Running Latency Test (Loopers)..."
	k6 run -e PROXY=loopers ../shared/harness/latency_test.js
	@echo "Running Latency Test (LiteLLM)..."
	k6 run -e PROXY=litellm ../shared/harness/latency_test.js

test-all: up seed-leak test-leak seed-uncap test-throughput test-latency down
