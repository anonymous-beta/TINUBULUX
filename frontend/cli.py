import time
import threading
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box

class TerminalUI:
    def __init__(self, engine, args):
        self.engine = engine
        self.args = args
        self.running = True
        
    def _make_layout(self):
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="stats"),
            Layout(name="visual")
        )
        return layout
    
    def _header_panel(self):
        return Panel(
            Text(f"TINUBULUX v1.0 | Target: {self.args.target}:{self.args.port} | Method: {self.args.method.upper()}", 
                 style="bold cyan", justify="center"),
            box=box.DOUBLE
        )
    
    def _stats_table(self, stats):
        table = Table(title="Live Statistics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Target", stats['target'])
        table.add_row("Method", stats['method'])
        table.add_row("Workers", str(stats['workers']))
        table.add_row("Elapsed", f"{stats['elapsed']:.1f}s")
        table.add_row("Packets Sent", f"{stats['sent']:,}")
        table.add_row("Packets Failed", f"{stats['failed']:,}")
        table.add_row("Packets/Sec", f"{stats['pps']:,.0f}")
        table.add_row("Bandwidth", f"{(stats['bps'] * 8 / 1024 / 1024):.2f} Mbps")
        
        return Panel(table, border_style="green")
    
    def _visual_bar(self, stats):
        total = stats['sent'] + stats['failed']
        if total == 0:
            ratio = 0
        else:
            ratio = stats['sent'] / total
            
        bar_width = 30
        filled = int(bar_width * ratio)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        text = Text()
        text.append(f"Success Rate: {ratio*100:.1f}%\n", style="bold")
        text.append(f"[{bar}]", style="green" if ratio > 0.8 else "yellow" if ratio > 0.5 else "red")
        
        return Panel(text, title="Performance", border_style="blue")
    
    def _footer_panel(self, stats):
        status = "🔥 ATTACKING" if self.engine.running.value else "⏹ STOPPED"
        return Panel(
            Text(f"{status} | Press Ctrl+C to stop", style="bold red" if self.engine.running.value else "bold white", justify="center"),
            box=box.SIMPLE
        )
    
    def _update(self, layout):
        while self.running:
            stats = self.engine.get_stats()
            layout["header"].update(self._header_panel())
            layout["stats"].update(self._stats_table(stats))
            layout["visual"].update(self._visual_bar(stats))
            layout["footer"].update(self._footer_panel(stats))
            time.sleep(0.5)
    
    def run(self):
        self.engine.start()
        
        layout = self._make_layout()
        
        try:
            with Live(layout, refresh_per_second=4, screen=True):
                self._update(layout)
                self.engine.wait()
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.engine.stop()
