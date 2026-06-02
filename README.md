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

We provide a direct, automated `Makefile` to run the entire benchmark suite without friction.

```bash
cd ep01-litellm

# Run the complete test suite (Budget Leak, Throughput, Latency)
make test-all
```

Alternatively, you can run individual phases manually:
```bash
# 1. Start the stack
make up

# 2. Run the Budget Leak benchmark
make seed-leak
make test-leak

# 3. Run Throughput and Latency benchmarks
make seed-uncap
make test-throughput
make test-latency

# 4. Tear down
make down
```

### Test 4 (Resource Footprint)
Container footprint measurements are taken manually using `docker stats --no-stream` at idle (post-startup) and under load (during `make test-latency`) on the target proxy containers.
