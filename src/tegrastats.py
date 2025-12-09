import subprocess
import re
class Tegrastats:
    def __init__(self, interval_ms:int):
        command = ['tegrastats', '--interval', str(interval_ms)]
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True, bufsize=1)

    def last_consumption(self) -> float:
        line = self.process.stdout.readline()
        parts = line.strip().split(" ")
        for i in range(len(parts)):
            if parts[i]=="VDD_IN":
                instants,average = parts[i+1].split("/")
                only_digits = int(''.join(filter(str.isdigit, instants)))
                if "mw" in instants.lower():
                    return only_digits/1000
                else:
                    return only_digits


