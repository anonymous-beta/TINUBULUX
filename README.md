# TINUBULUX 🔥

> *"Real power. No simulations. Built by Anonymous-beta."*

High-performance network stress testing framework. Multi-vector. Multi-process. Terminal UI. Linux-native.

## Quick Start

```bash
# Install dependencies
pip3 install -r requirements.txt

# HTTP Flood (default)
sudo python3 tinubulux.py -t target.com -p 80 -m http -c 1000

# SYN Flood (requires root for raw sockets)
sudo python3 tinubulux.py -t 192.168.1.1 -p 80 -m syn -c 500

# UDP Flood
python3 tinubulux.py -t target.com -p 53 -m udp -c 2000

# Slowloris
python3 tinubulux.py -t target.com -p 80 -m slowloris -c 100

# DNS Amplification
python3 tinubulux.py -t 10.0.0.5 -p 53 -m dns -c 50
```
Flag	Description	Default	
`-t, --target`	Target IP/hostname	required	
`-p, --port`	Target port	80	
`-m, --method`	Attack method (http/syn/udp/slowloris/dns)	http	
`-c, --connections`	Concurrent workers	500	
`-d, --duration`	Duration in seconds (0 = unlimited)	60	
`--threads`	OS-level threads	4	
`--no-ui`	Disable TUI, console only	false	
`--proxy-file`	Proxy list file	none	
`--config`	Config file path	config.yaml	
`-v, --verbose`	Verbose output	false	

# ARCHITECTURE
tinubulux.py          # Entry point
├── core/
│   ├── engine.py       # Orchestrator
│   └── attackers/
│       ├── http_flood.py
│       ├── syn_flood.py
│       ├── udp_flood.py
│       ├── slowloris.py
│       └── dns_amp.py
├── frontend/
│   └── cli.py          # Rich terminal UI
├── utils/
│   └── logger.py       # Console logging
└── config.yaml         # Default configuration

# Requirements
 
Python 3.8+
 
Linux (raw sockets for SYN/DNS modes)
 
Root privileges for SYN flood mode

# Legal
This tool is for authorized security testing only. The author assumes no liability for misuse.
Built with cold coffee and frustration caused by the Nigerian Government😡. 
