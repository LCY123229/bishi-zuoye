import socket

import psutil

MIB = 1024 * 1024


class SystemSampler:
    def __init__(self):
        self.hostname = socket.gethostname()
        # 首次调用只建立 CPU 采样基准。
        psutil.cpu_percent(interval=None)

    def sample(self):
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        network = psutil.net_io_counters(nowrap=True)
        return dict(
            hostname=self.hostname,
            cpu_percent=float(cpu),
            memory_percent=float(memory.percent),
            memory_total=memory.total / MIB,
            memory_available=memory.available / MIB,
            net_sent=network.bytes_sent / MIB if network else 0.0,
            net_recv=network.bytes_recv / MIB if network else 0.0,
        )
