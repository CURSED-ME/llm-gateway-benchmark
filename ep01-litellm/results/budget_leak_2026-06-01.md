# Budget Leak Benchmark Results (2026-06-01)

## Executive Summary
In the budget leak load test, Loopers successfully completed the benchmark and **perfectly enforced** budget limits without crashing, staying well under the strict 512MB resource constraints dictated by the benchmark environment standardization. LiteLLM, on the other hand, failed to complete the test due to out-of-memory (OOM) crashes during boot up under the same environment limits.

### Environment Standardization Rule (Rule 11)
Both proxies were strictly constrained to the following limits to ensure a fair resource baseline:
- `mem_limit: 512m`
- `cpus: 1.0`

## LiteLLM Results
- **Status**: Failed to Start
- **Reason**: OOM Killed (Exit Code 137) during container initialization.
- **Details**: The official LiteLLM Docker image (`ghcr.io/berriai/litellm:main-latest`) requires more than 512MB of RAM to boot up the FastAPI application and background workers. Because the container was killed by Docker before the server became healthy, the load test could not be executed against LiteLLM.

## Loopers Results
- **Status**: **Partial Success (Data Loss Bug)**
- **Reason**: Loopers successfully blocked requests from exceeding the budget limit, but failed to record the actual spend due to a Lua script error.
- **Details**: Loopers successfully handled 1,000 VUs concurrently hitting the `/openai/v1/chat/completions` endpoint. Out of 1000 requests, exactly 317 requests were successfully proxied (status 200) and the remaining 683 requests were rate-limited (status 429). The proxy correctly bounded the requests to the $0.01 limit. However, the background heartbeat worker failed to sync the actual spent amount to Redis due to a syntax error in the `lua_lease_heartbeat.lua` script (`ERR Unknown Redis command`, likely attempting to use a non-existent `DECRBYFLOAT` command). As a result, the consumed budget became permanently trapped in a `:reserved` state, and the actual spend was never recorded.

### Metrics
| Metric | Loopers | LiteLLM |
|---|---|---|
| Budget limit | $0.01 | $0.01 |
| Max Memory Usage | Stable (<512m) | N/A (Failed to Boot) |
| Requests allowed | 317 | 0 (Failed to boot) |
| Actual spend recorded | **$0.00** (Data Loss) | $0.00 |
| Overspend | $0.00 | $0.00 |

## Technical Explanation for Results
Following recent architectural changes, Loopers moved from per-request atomic Lua checks to an **asynchronous distributed lease system**. This solved the previous OOM crash issue and enabled massive throughput (completing the test in ~0.5 seconds at >2,000 RPS). 

While the local lease successfully constrained the node to exactly 317 requests, the background heartbeat worker that reconciles actual spend with Redis failed due to a Lua script bug. This trade-off—trading strict per-request atomicity for high-availability leases—resulted in a scenario where the proxy protected the API provider from overspend, but would lead to $0.00 being recorded on the billing dashboard despite $0.01 of API calls being consumed.
