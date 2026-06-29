#!/usr/bin/env python3
"""
TINUBULUX — High-Performance Network Stress Testing Framework
Built for LO. Real power. No simulations.
"""

import argparse
import sys
import os
import yaml
import signal
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.engine import AttackEngine
from frontend.cli import TerminalUI
from utils.logger import TINULogger

def signal_handler(sig, frame):
    print("\n\n[!] TINUBULUX shutting down gracefully...")
    if 'engine' in globals():
        engine.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def load_config(config_path="config.yaml"):
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def main():
    parser = argparse.ArgumentParser(
        description="TINUBULUX — Network Stress Testing Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tinubulux.py -t 192.168.1.1 -p 80 -m http -c 500
  python3 tinubulux.py -t target.com -m udp --duration 300
  python3 tinubulux.py -t 10.0.0.5 -m syn -c 1000 --no-ui
        """
    )
    
    parser.add_argument('-t', '--target', required=True, help='Target IP or hostname')
    parser.add_argument('-p', '--port', type=int, default=80, help='Target port (default: 80)')
    parser.add_argument('-m', '--method', choices=['http', 'syn', 'udp', 'slowloris', 'dns'], 
                        default='http', help='Attack method')
    parser.add_argument('-c', '--connections', type=int, default=500, 
                        help='Number of concurrent connections/threads')
    parser.add_argument('-d', '--duration', type=int, default=60, 
                        help='Attack duration in seconds (0 = unlimited)')
    parser.add_argument('--threads', type=int, default=4, 
                        help='OS threads for multiprocessing (default: 4)')
    parser.add_argument('--no-ui', action='store_true', 
                        help='Disable terminal UI, use console output only')
    parser.add_argument('--proxy-file', help='File containing proxy list (host:port format)')
    parser.add_argument('--user-agent', help='Custom User-Agent string')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    logger = TINULogger(verbose=args.verbose)
    
    logger.banner()
    
    engine = AttackEngine(args, config, logger)
    
    if not args.no_ui:
        ui = TerminalUI(engine, args)
        ui.run()
    else:
        engine.start()
        engine.wait()

if __name__ == "__main__":
    main()
