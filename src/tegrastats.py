from threading import Lock, Thread
from subprocess import Popen, PIPE


class Tegrastats:
    def __init__(self, interval_ms: int, get_instant:bool):
        command = ['tegrastats', '--interval', str(interval_ms)]
        self.process = \
            Popen(command, stdout=PIPE, text=True, bufsize=1)
        self._lock = Lock()
        self.latest_line: float = None
        self.consumed_energy_j: float = 0
        self.interval_s: float = interval_ms/1000
        self.get_instant = get_instant
 
        self.reader_thread = Thread(target=self._read_lines, daemon=True)
        self.reader_thread.start()

    def start_measurement(self) -> None:
        self.consumed_energy_j = 0

    def end_measurement_j(self) -> float:
        return self.consumed_energy_j

    def _read_lines(self) -> None:
        try:
            while self.process.poll() is None:
                self._last_consumption_blockable()
        except Exception as e:
            print("Warning: tegrastats reader exception:", e)

    def _last_consumption_blockable(self) -> None:
        try:
            line = self.process.stdout.readline()
            if not line:
                return
            parts = line.strip().split(" ")
            for i in range(len(parts)):
                if parts[i] == "VDD_IN":
                    if self.get_instant:
                        value, _ = parts[i+1].split("/")
                    else:
                        _, value = parts[i+1].split("/")
                    only_digits = int(''.join(filter(str.isdigit, value)))
                    value = float(only_digits/1000 if "mw" in value.lower() else only_digits)
                    self.consumed_energy_j += value * self.interval_s
                    with self._lock:
                        self.latest_line = value
        except Exception:
            # Ignore malformed lines or parse errors
            return

    def get_last_consumption_w(self) -> float:
        with self._lock:
            return self.latest_line

    def stop(self) -> None:
        try:
            if self.process.poll() is None:
                self.process.terminate()
        except Exception:
            pass
        try:
            if hasattr(self, 'reader_thread') and self.reader_thread.is_alive():
                self.reader_thread.join(timeout=0.5)
        except Exception:
            pass

    def __del__(self):
        self.stop()
