from threading import Lock, Thread
from subprocess import Popen, PIPE


class Tegrastats:
    def __init__(self, interval_ms: int):
        command = ['tegrastats', '--interval', str(interval_ms)]
        self.process = \
            Popen(command, stdout=PIPE, text=True, bufsize=1)
        self._lock = Lock()
        self.latest_line: float = None
        self.consumed_energy_j: float = 0
        self.interval_s: float = interval_ms/1000

        self.reader_thread = Thread(target=self._read_lines)
        self.reader_thread.start()

    def start_measurement(self) -> None:
        self.consumed_energy_j = 0

    def end_measurement_j(self) -> float:
        return self.consumed_energy_j

    def _read_lines(self) -> None:
        while self.process.poll() is None:
            self._last_consumption_blockable()

    def _last_consumption_blockable(self) -> None:
        line = self.process.stdout.readline()
        parts = line.strip().split(" ")
        for i in range(len(parts)):
            if parts[i] == "VDD_IN":
                instants, average = parts[i+1].split("/")
                only_digits = int(''.join(filter(str.isdigit, instants)))
                value = float(only_digits/1000 if "mw" in instants.lower() else only_digits)
                self.consumed_energy_j += value * self.interval_s
                with self._lock:
                    self.latest_line = value

    def get_last_consumption_w(self) -> float:
        with self._lock:
            return self.latest_line

    def stop(self) -> None:
        self.process.terminate()
