from datetime import datetime

class TINULogger:
    def __init__(self, verbose=False):
        self.verbose = verbose
        
    def _timestamp(self):
        return datetime.now().strftime("%H:%M:%S")
    
    def banner(self):
        print(f"""
╔══════════════════════════════════════════════════════════╗
║  ████████╗██╗███╗   ██╗██╗   ██╗██████╗ ██╗     ██╗   ██╗██╗  ██╗  ║
║  ╚══██╔══╝██║████╗  ██║██║   ██║██╔══██╗██║     ██║   ██║╚██╗██╔╝  ║
║     ██║   ██║██╔██╗ ██║██║   ██║██████╔╝██║     ██║   ██║ ╚███╔╝   ║
║     ██║   ██║██║╚██╗██║██║   ██║██╔══██╗██║     ██║   ██║ ██╔██╗   ║
║     ██║   ██║██║ ╚████║╚██████╔╝██████╔╝███████╗╚██████╔╝██╔╝ ██╗  ║
║     ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═╝  ║
║                                                          ║
║           Network Stress Testing Framework v1.0          ║
║                    Built for LO ❤️                        ║
╚══════════════════════════════════════════════════════════╝
        """)
    
    def info(self, msg):
        print(f"[{self._timestamp()}] [*] {msg}")
    
    def success(self, msg):
        print(f"[{self._timestamp()}] [+] {msg}")
    
    def warning(self, msg):
        print(f"[{self._timestamp()}] [!] {msg}")
    
    def error(self, msg):
        print(f"[{self._timestamp()}] [-] {msg}")
    
    def debug(self, msg):
        if self.verbose:
            print(f"[{self._timestamp()}] [D] {msg}")
