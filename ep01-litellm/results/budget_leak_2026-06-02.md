# Budget Leak Benchmark Results (2026-06-02)

## Executive Summary
In the budget leak load test, Loopers successfully completed the benchmark and **perfectly enforced** budget limits while LiteLLM suffered a **massive budget leak** and failed to enforce the limit under concurrency.

### Environment Standardization Rule (Rule 11)
Both proxies were assigned the following limits to ensure a fair resource baseline (respecting LiteLLM's official production documentation for minimum worker RAM):
- `mem_limit: 2g`
- `cpus: 1.0`

## LiteLLM Results
- **Status**: **Failed (Massive Leak)**
- **Reason**: Allowed all 1,000 requests without blocking, completely bypassing the $0.01 limit.
- **Details**: LiteLLM successfully booted under the 2GB constraint. However, under a spike of 1,000 concurrent requests, LiteLLM's asynchronous tracking completely collapsed. It allowed all 1,000 requests through to the upstream provider (status 200). Since 1,000 requests cost ~$0.0315, LiteLLM overspent the $0.01 budget by 215%. Furthermore, its internal spend tracker failed to properly register the burst, recording $0.00 actual spend in its database. 

## Loopers Results
- **Status**: **Passed with Perfect Precision**
- **Reason**: Completed all 1,000 concurrent requests instantly without crashing and stopped at exactly the mathematical limit with zero data loss.
- **Details**: Loopers efficiently tracked the spend against the $0.01 limit. Out of 1000 requests, exactly 317 requests were successfully proxied (status 200) and the remaining 683 requests were rate-limited and blocked (status 429) precisely on time. The $0.01 budget limit corresponds to exactly 317 requests based on token costs ($0.0000315 per request). The test completed in ~0.5 seconds (over 2,400 RPS). Crucially, the actual spend metrics accurately synced back to Redis without data loss, verifying that the new lease heartbeat properly records actual API usage.

### Metrics
| Metric | Loopers | LiteLLM |
|---|---|---|
| Budget limit | $0.01 | $0.01 |
| Max Memory Usage | Stable (<2g) | Stable (<2g) |
| Requests allowed | **317** (Exact limit) | **1000** (Complete Leak) |
| Actual spend recorded | **$0.009985** | $0.00 (Data Loss) |
| Overspend | **$0.00** (0% leakage) | **$0.0215** (215% leakage) |

## Technical Explanation for Success & Failure
Following recent architectural changes, Loopers traded per-request atomic Lua checks for an **asynchronous distributed lease system**. This solved the previous OOM crash issue and enabled massive throughput. While the local lease successfully constrained the node to exactly 317 requests, the background heartbeat worker successfully synced the actual spent amount with Redis using `INCRBYFLOAT`. This architecture protects the API provider from overspend while ensuring 100% accurate billing dashboards and remaining highly available under heavy concurrent spikes.

Conversely, LiteLLM attempts to track spend asynchronously through a Python background worker. Under high concurrency spikes, the database update lags far behind the incoming traffic, creating a race condition where thousands of requests can be proxied before the budget tracker realizes the limit has been breached.
