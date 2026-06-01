# LLM Gateway Benchmark Suite

A local, mock-backed, reproducible load-testing harness to compare open-source LLM gateways under concurrency.

## Philosophy & Core Directives
1. **Local and Deterministic:** All request traffic is routed to a local mock server (`shared/mock-llm`) with fixed token costs and a deterministic 50ms latency. No real LLM API keys are needed, and no traffic is sent to the public internet.
2. **Infrastructure Focus:** The benchmark focuses purely on performance, cost enforcement, and memory footprints. It does not measure dashboard UI, feature richness, or provider support.
3. **Episode-based Cadence:** Benchmarks are run as side-by-side matches (1v1). Each folder represents an episode testing Loopers against a specific competitor.

## Directory Structure
- `shared/`
  - `mock-llm/`: Nginx/OpenResty mock upstream serving static completions with 50ms delay.
  - `harness/`: Standardized k6 test scripts for budget leakage, latency overhead, and peak throughput.
- `ep01-litellm/`: Episode 1 benchmark comparing Loopers vs LiteLLM.

## Prerequisites
- **Docker** and **Docker Compose** (with resources limits support)
- **k6** (load testing CLI tool)

## Quick Start (Episode 1: LiteLLM)

### 1. Boot up the environment
```bash
cd ep01-litellm
docker compose up -d
```
Verify all containers (`mock-llm`, `redis`, `postgres`, `litellm`, `loopers`) are healthy.

### 2. Run Test 1 (Budget Leak Test)
This test validates if the gateway enforces budget restrictions under high concurrency (1,000 VUs firing 1,000 requests simultaneously).

```bash
# Seed a $0.01 limit
./seed.sh --leak

# Run against Loopers
k6 run --env PROXY=loopers --out json=results/raw_budget_loopers.json ../shared/harness/budget_leak_test.js

# Reset and seed for competitor
./seed.sh --reset
./seed.sh --leak

# Run against LiteLLM
k6 run --env PROXY=litellm --out json=results/raw_budget_litellm.json ../shared/harness/budget_leak_test.js
```

### 3. Run Test 2 (Peak Throughput Test)
This test ramps load from 10 to 2,000 VUs over 5 minutes to measure the maximum sustained requests-per-second before error rate exceeds 1%.

```bash
# Uncap budget limits
./seed.sh --uncap

# Run Loopers
k6 run --env PROXY=loopers --out json=results/raw_throughput_loopers.json ../shared/harness/throughput_test.js

# Run LiteLLM
k6 run --env PROXY=litellm --out json=results/raw_throughput_litellm.json ../shared/harness/throughput_test.js
```

### 4. Run Test 3 (Proxy Overhead Latency Test)
This test measures proxy overhead under a sustained load of 500 VUs.

```bash
# Run Loopers
k6 run --env PROXY=loopers --out json=results/raw_latency_loopers.json ../shared/harness/latency_test.js

# Run LiteLLM
k6 run --env PROXY=litellm --out json=results/raw_latency_litellm.json ../shared/harness/latency_test.js
```

### 5. Run Test 4 (Resource Footprint)
Capture container size and RSS memory footprint at idle and under load:
```bash
# Idle
docker stats --no-stream

# Run during active load test (e.g. latency test)
docker stats --no-stream
```
Capture and document the footprint results under `ep01-litellm/results/`.
