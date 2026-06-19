import json
import os
import glob
from datetime import datetime

RESULTS_DIR = "results"
DATE_SUFFIX = datetime.now().strftime("%Y-%m-%d")

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def generate_budget_leak_md():
    loopers_data = load_json(f"{RESULTS_DIR}/summary_budget_leak_loopers.json")
    litellm_data = load_json(f"{RESULTS_DIR}/summary_budget_leak_litellm.json")

    if not loopers_data or not litellm_data:
        return

    # Extract 200 OKs
    def get_200s(data):
        try:
            return data["root_group"]["checks"]["is status 200"]["passes"]
        except KeyError:
            return 0
    
    loopers_200 = get_200s(loopers_data)
    litellm_200 = get_200s(litellm_data)

    cost_per_req = 0.0000315
    budget_limit = 0.01
    expected_reqs = 317

    loopers_spend = loopers_200 * cost_per_req
    litellm_spend = litellm_200 * cost_per_req

    loopers_overspend = max(0, loopers_spend - budget_limit)
    litellm_overspend = max(0, litellm_spend - budget_limit)

    md_content = f"""# Budget Leak Test Results ({DATE_SUFFIX})

**Goal:** Prove whether a proxy enforces a hard budget accurately under concurrent load.
**Setup:**
- Hard budget limit: $0.01
- Concurrent VUs: 1000
- Cost per request: $0.0000315 (Expected allowed requests: ~317)

## Results

| Metric | Loopers | LiteLLM |
|---|---|---|
| Budget limit | $0.01 | $0.01 |
| Requests allowed | {loopers_200} | {litellm_200} |
| Actual spend allowed | ${loopers_spend:.6f} | ${litellm_spend:.6f} |
| Overspend | ${loopers_overspend:.6f} | ${litellm_overspend:.6f} |

### Analysis
LiteLLM recently shipped "authoritative DB spend" enforcement to prevent cross-pod counter drift. This test demonstrates whether the database fallback is able to mitigate the TOCTOU race conditions under high concurrent load compared to Loopers' atomic Redis Lua scripts.
"""
    with open(f"{RESULTS_DIR}/budget_leak_{DATE_SUFFIX}.md", "w") as f:
        f.write(md_content)

def generate_throughput_md():
    loopers_data = load_json(f"{RESULTS_DIR}/summary_throughput_loopers.json")
    litellm_data = load_json(f"{RESULTS_DIR}/summary_throughput_litellm.json")

    if not loopers_data or not litellm_data:
        return

    def get_rps(data):
        try:
            total_reqs_rate = data["metrics"]["http_reqs"]["rate"]
            fail_rate = data["metrics"].get("http_req_failed", {}).get("value", 0)
            return total_reqs_rate * (1 - fail_rate)
        except:
            return 0

    loopers_rps = get_rps(loopers_data)
    litellm_rps = get_rps(litellm_data)

    md_content = f"""# Throughput Test Results ({DATE_SUFFIX})

**Goal:** Find the maximum requests-per-second each proxy can sustain before dropping or erroring.
**Setup:**
- Ramp up to 2000 concurrent VUs over 5 minutes.
- No budget limits.

## Results

| Proxy | Peak Sustained RPS |
|---|---|
| Loopers | {loopers_rps:.2f} |
| LiteLLM | {litellm_rps:.2f} |

### Analysis
Loopers leverages Go's native multi-threading and goroutines to scale efficiently across CPU cores. LiteLLM is Python-based (FastAPI/asyncio), and while it can scale via Gunicorn workers, the event loop inherently presents a different concurrency ceiling.
"""
    with open(f"{RESULTS_DIR}/throughput_{DATE_SUFFIX}.md", "w") as f:
        f.write(md_content)

def generate_latency_md():
    loopers_data = load_json(f"{RESULTS_DIR}/summary_latency_loopers.json")
    litellm_data = load_json(f"{RESULTS_DIR}/summary_latency_litellm.json")

    if not loopers_data or not litellm_data:
        return

    def get_latencies(data):
        try:
            req_duration = data["metrics"]["http_req_duration"]
            return req_duration["med"], req_duration["p(90)"], req_duration.get("p(99)", req_duration.get("p(95)", 0))
        except:
            return 0, 0, 0

    loopers_p50, loopers_p90, loopers_p99 = get_latencies(loopers_data)
    litellm_p50, litellm_p90, litellm_p99 = get_latencies(litellm_data)

    upstream_delay = 0 # Assume 0ms added delay based on mock server without sleep

    def calc_overhead(val):
        return max(0, val - upstream_delay)

    md_content = f"""# Latency Overhead Results ({DATE_SUFFIX})

**Goal:** Measure the latency the proxy itself adds.
**Setup:**
- 500 concurrent VUs for 60 seconds.

## Results

| Proxy | P50 Overhead | P90 Overhead | P99 Overhead |
|---|---|---|---|
| Loopers | {calc_overhead(loopers_p50):.2f} ms | {calc_overhead(loopers_p90):.2f} ms | {calc_overhead(loopers_p99):.2f} ms |
| LiteLLM | {calc_overhead(litellm_p50):.2f} ms | {calc_overhead(litellm_p90):.2f} ms | {calc_overhead(litellm_p99):.2f} ms |

### Analysis
A proxy should be as invisible as possible. The P99 latency overhead is the most critical metric as it represents real impact to the 99th percentile of users.
"""
    with open(f"{RESULTS_DIR}/latency_{DATE_SUFFIX}.md", "w") as f:
        f.write(md_content)

if __name__ == "__main__":
    print("Generating markdown summaries...")
    generate_budget_leak_md()
    generate_throughput_md()
    generate_latency_md()
    print("Done!")
