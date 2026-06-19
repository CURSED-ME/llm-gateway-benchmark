# Budget Leak Test Results (2026-06-19)

**Goal:** Prove whether a proxy enforces a hard budget accurately under concurrent load.
**Setup:**
- Hard budget limit: $0.01
- Concurrent VUs: 1000
- Cost per request: $0.0000315 (Expected allowed requests: ~317)

## Results

| Metric | Loopers | LiteLLM |
|---|---|---|
| Budget limit | $0.01 | $0.01 |
| Requests allowed | 316 | 318 |
| Actual spend allowed | $0.009954 | $0.010017 |
| Overspend | $0.000000 | $0.000017 |

### Analysis
LiteLLM recently shipped "authoritative DB spend" enforcement to prevent cross-pod counter drift. This test demonstrates whether the database fallback is able to mitigate the TOCTOU race conditions under high concurrent load compared to Loopers' atomic Redis Lua scripts.
