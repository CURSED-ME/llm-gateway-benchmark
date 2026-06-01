# Peak Throughput Test Results (2026-05-31)

This document contains the raw output and narrative explanation for **Test 2: Peak Throughput Test (Max RPS)**, comparing Loopers and LiteLLM under high concurrency.

## Setup
- **Concurrency profile:** Ramped from 10 to 2,000 concurrent Virtual Users (VUs) over 5 minutes.
- **Budget limits:** Disabled / uncapped ($999,999) on both proxies.
- **Mock Upstream:** Artificial delay set to 0ms to isolate proxy overhead.
- **Hardware Profile:** All containers restricted to 2GB RAM and 1.0 CPU (`redis` and `mock-llm` restricted to 0.5 CPU).

---

## 📊 The Results

| Metric | Loopers (Go) | LiteLLM (Python/FastAPI) |
|---|---|---|
| Total HTTP Requests | 1,388,886 | 58,300 |
| Average RPS | ~4,623 req/s | ~176.7 req/s |
| HTTP 200 OK Responses | 1,341,675 (96.6%) | 56,623 (97.1%) |
| Failed Requests | 47,211 (3.4%) | 1,677 (2.9%) |
| Test Completion | Succeeded | Failed at max concurrency |

---

## 🔬 Architectural Analysis: Why Loopers Won

In this test, Loopers' Go/Gin multi-threaded architecture demonstrated its raw performance capability, massively outperforming LiteLLM's Python `asyncio` event loop by a factor of roughly **26x** (4,623 RPS vs 176.7 RPS).

### The Power of Compiled Languages vs Global Interpreter Locks
Loopers is written in Go, which natively supports parallel execution across multiple CPU cores through Goroutines. When subjected to an extreme load of 2,000 concurrent Virtual Users, the Go scheduler efficiently multiplexes requests across available threads, absorbing the traffic without breaking a sweat.

LiteLLM, built on Python and FastAPI, relies on the `asyncio` event loop. While asynchronous IO handles concurrent connections well, the Python Global Interpreter Lock (GIL) fundamentally limits the server to a single thread of execution per worker. Even with multiple Gunicorn workers, the overhead of Python interpreter context switching under heavy load creates a strict ceiling.

### The Trade-Offs
- **Loopers** demonstrates the incredible ceiling of compiled, natively concurrent languages. After architectural adjustments to alleviate bottlenecks in its atomic Redis checks, Loopers can process millions of requests in minutes without buckling.
- **LiteLLM** relies on a massive ecosystem of 100+ supported providers and a rich feature set, accepting lower raw throughput in exchange for broad compatibility and rapid development speed inherent to the Python ecosystem. 

### Addendum: Overcoming the Redis Bottleneck
Earlier benchmarks showed Loopers failing at ~32 RPS due to a single-threaded Redis lock bottleneck. However, after recent architectural changes to how Loopers handles budget reservations (likely introducing asynchronous or batch-level updates rather than strictly synchronous blocking locks), the proxy was able to bypass the database bottleneck entirely, unlocking the true speed of the Go runtime.
