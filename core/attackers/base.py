import time

class BaseAttacker:
    """Common plumbing for all attackers:
    - buffered stat flushing (no per-packet lock contention)
    - per-worker rate limiting via --rate (packets/sec, 0 = unlimited)
    Subclasses implement attack() and call self._count() / self._pace()."""

    FLUSH_COUNT = 50
    FLUSH_INTERVAL = 0.5

    def __init__(self, args, config, stats, running, worker_id):
        self.target = args.target
        self.port = args.port
        self.config = config
        self.stats = stats
        self.running = running
        self.worker_id = worker_id
        self.rate = max(0, getattr(args, 'rate', 0) or 0)

        # Local buffers — flushed to SharedStats in batches
        self._buf_sent = 0
        self._buf_failed = 0
        self._buf_bytes = 0
        self._ops_since_flush = 0
        self._last_flush = time.monotonic()

        # Rate limiting state
        self._next_slot = time.monotonic()

    # ---------- stats ----------

    def _count(self, sent=0, failed=0, size=0):
        self._buf_sent += sent
        self._buf_failed += failed
        self._buf_bytes += size
        self._ops_since_flush += 1
        now = time.monotonic()
        if (self._ops_since_flush >= self.FLUSH_COUNT
                or now - self._last_flush >= self.FLUSH_INTERVAL):
            self._flush()

    def _flush(self):
        if self._buf_sent or self._buf_failed or self._buf_bytes:
            self.stats.add(sent=self._buf_sent, failed=self._buf_failed,
                           bps=self._buf_bytes)
        self._buf_sent = self._buf_failed = self._buf_bytes = 0
        self._ops_since_flush = 0
        self._last_flush = time.monotonic()

    def finalize(self):
        """Flush remaining counters on exit. Call in a finally block."""
        try:
            self._flush()
        except Exception:
            pass

    # ---------- pacing ----------

    def _pace(self):
        """Sleep to hold self.rate packets/sec for this worker."""
        if self.rate <= 0:
            return
        self._next_slot += 1.0 / self.rate
        delay = self._next_slot - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        else:
            # We've fallen behind (e.g. slow I/O); resync instead of bursting
            self._next_slot = time.monotonic()

    # ---------- helpers ----------

    @staticmethod
    def random_ip():
        import random
        return (f"{random.randint(1, 254)}.{random.randint(0, 255)}."
                f"{random.randint(0, 255)}.{random.randint(1, 254)}")