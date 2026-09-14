import multiprocessing as mp
import time

class SharedStats:
    """Cross-process stats with a single lock acquisition per batch,
    instead of per packet."""

    def __init__(self):
        self._sent = mp.Value('Q', 0)
        self._failed = mp.Value('Q', 0)
        self._bps = mp.Value('Q', 0)
        self._lock = mp.Lock()
        self.start_time = None

    def add(self, sent=0, failed=0, bps=0):
        with self._lock:
            if sent:
                self._sent.value += sent
            if failed:
                self._failed.value += failed
            if bps:
                self._bps.value += bps

    @property
    def sent(self):
        return self._sent.value

    @property
    def failed(self):
        return self._failed.value

    @property
    def bps(self):
        return self._bps.value

    def reset(self):
        with self._lock:
            self._sent.value = 0
            self._failed.value = 0
            self._bps.value = 0
            self.start_time = time.time()