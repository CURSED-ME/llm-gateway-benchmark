# Resource Footprint Benchmark (2026-06-02)

## Goal
Measure the deployment cost of each proxy in terms of container size and memory consumption at scale.

## Setup
- **Idle Measurement**: Taken using `docker stats --no-stream` after 60 seconds of idle time.
- **Load Measurement**: Taken during the 60 seconds of sustained load at 500 concurrent VUs.
- **Image Size**: Pulled using `docker image ls`.
- **Infrastructure limits**: All containers were bound to their defined `docker-compose` cpu/mem limits.

## Results

### Container Image Footprint
| Metric | Loopers | LiteLLM |
|---|---|---|
| Image Size (Disk Usage) | 102 MB | 5,600 MB (5.6 GB) |
| Required Containers | 2 (Loopers + Redis) | 3 (LiteLLM + Redis + PostgreSQL) |

### Memory Footprint at Idle
| Component | Loopers Stack | LiteLLM Stack |
|---|---|---|
| Proxy Container | 33.46 MB | 906.10 MB |
| Redis | 8.12 MB | 8.12 MB |
| PostgreSQL | N/A | 43.61 MB |
| **Total Idle Memory** | **41.58 MB** | **957.83 MB** |

### Memory Footprint under Load (500 VUs)
| Component | Loopers Stack | LiteLLM Stack |
|---|---|---|
| Proxy Container | 67.33 MB | 1,064.96 MB (1.04 GB) |
| Redis | 8.41 MB | 8.44 MB |
| PostgreSQL | N/A | 65.60 MB |
| **Total Load Memory** | **75.74 MB** | **1,139.00 MB (1.14 GB)** |

## Analysis

**What does it actually cost to run each gateway in Kubernetes?**

Infrastructure engineers care deeply about resource consumption at scale. The difference in architecture between Go and Python yields drastically different footprints. 

LiteLLM requires three containers for a production-grade deployment with budget tracking (Proxy, Redis, and PostgreSQL), and sits at nearly a gigabyte of RAM (~957 MB) even when completely idle. Under a load of 500 concurrent VUs, this scales up to ~1.14 GB, largely driven by the Python event loops in Gunicorn workers and the DB connection overhead. Its Docker image is also a hefty 5.6 GB.

Loopers, running as a statically linked Go binary, requires only two containers (Proxy and Redis) and idles at a combined 41.58 MB. Under the same 500 VU load, its total footprint rises slightly to 75.74 MB. This represents a 93% reduction in memory requirements compared to the competitor, meaning Loopers can be deployed effectively as a sidecar proxy without consuming the majority of a node's resources.
